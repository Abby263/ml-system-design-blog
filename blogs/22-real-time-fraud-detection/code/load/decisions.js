import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    authorization_deadline: {
      executor: "constant-arrival-rate",
      rate: 100,
      timeUnit: "1s",
      duration: "30s",
      preAllocatedVUs: 30,
    },
  },
  thresholds: {
    http_req_duration: ["p(99)<80"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const now = new Date();
  const body = JSON.stringify({
    transaction_id: `txn-${__VU}-${__ITER}`,
    event_time: now.toISOString(),
    account_id: `account-${__VU}`,
    account_created_at: new Date(now.getTime() - 86_400_000).toISOString(),
    card_token: `card-${__VU % 20}`,
    device_id: `device-${__VU % 10}`,
    ip_prefix: "203.0.113.0/24",
    country: "CA",
    merchant_id: "merchant-load",
    amount_minor: 2500,
    currency: "CAD",
    cvv_result: "match",
  });
  const response = http.post("http://localhost:8000/v1/risk-decisions", body, {
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": `load-${__VU}-${__ITER}`,
    },
  });
  check(response, {
    "status is 200": (result) => result.status === 200,
    "decision is versioned": (result) => Boolean(result.json("policy_version")),
  });
}
