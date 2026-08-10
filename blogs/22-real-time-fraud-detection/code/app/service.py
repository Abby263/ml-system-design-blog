import hashlib
import json
import uuid

from .artifacts import ModelBundle
from .models import Action, RiskDecisionView, RiskRequest
from .store import Store


FEATURE_VERSION = "payment-risk-v1"
POLICY_VERSION = "demo-policy-v1"


class RiskService:
    def __init__(self, store: Store, model: ModelBundle):
        self.store = store
        self.model = model

    @staticmethod
    def request_hash(request: RiskRequest) -> str:
        payload = json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    def decide(
        self,
        idempotency_key: str,
        request: RiskRequest,
        fail_model: bool = False,
        stale_features: bool = False,
    ) -> RiskDecisionView:
        def build(features: dict[str, float]) -> RiskDecisionView:
            hard_block = features["cvv_failed"] == 1 and features["card_attempt_count_10m"] >= 4
            reasons: list[str] = []
            if features["account_age_hours_log"] < 1.1:
                reasons.append("new_account")
            if features["card_attempt_count_10m"] >= 3:
                reasons.append("card_velocity_10m")
            if features["device_accounts_24h"] >= 4:
                reasons.append("shared_device_24h")
            if features["country_changed_1h"]:
                reasons.append("country_changed_1h")
            if features["cvv_failed"]:
                reasons.append("cvv_failed")

            unavailable: list[str] = []
            if fail_model:
                unavailable.append("model")
                score = min(
                    0.95,
                    0.12
                    + 0.12 * features["card_attempt_count_10m"]
                    + 0.10 * features["device_accounts_24h"]
                    + 0.25 * features["cvv_failed"],
                )
                reasons.append("rules_only_fallback")
            else:
                score, contributions = self.model.predict(features)
                reasons.extend(
                    f"model:{name}"
                    for name, contribution in contributions[:2]
                    if contribution > 0.05
                )

            if stale_features:
                unavailable.append("streaming_features")
                reasons.append("stale_streaming_features")

            if hard_block or score >= 0.88:
                action = Action.BLOCK
            elif score >= 0.65:
                action = Action.REVIEW
            elif score >= 0.35:
                action = Action.CHALLENGE
            else:
                action = Action.ALLOW

            high_value_new_account = (
                request.amount_minor >= 50_000 and features["account_age_hours_log"] < 1.1
            )
            if high_value_new_account:
                reasons.append("high_value_new_account_policy")
                if action == Action.ALLOW:
                    action = Action.CHALLENGE
            if stale_features and high_value_new_account:
                reasons.append("degraded_high_value_policy")

            return RiskDecisionView(
                decision_id=f"rd_{uuid.uuid4().hex}",
                transaction_id=request.transaction_id,
                action=action,
                risk_score=round(score, 6),
                reason_codes=list(dict.fromkeys(reasons)),
                features={name: round(value, 6) for name, value in features.items()},
                model_version=self.model.version if not fail_model else "rules-only",
                feature_version=FEATURE_VERSION,
                policy_version=POLICY_VERSION,
                degraded=bool(unavailable),
                unavailable_sources=unavailable,
            )

        return self.store.decide(
            idempotency_key=idempotency_key,
            request_hash=self.request_hash(request),
            request=request,
            build=build,
        )
