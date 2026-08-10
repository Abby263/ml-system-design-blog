import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    steady_feed_reads: {
      executor: "constant-arrival-rate",
      rate: 50,
      timeUnit: "1s",
      duration: "30s",
      preAllocatedVUs: 20,
    },
  },
  thresholds: {
    http_req_duration: ["p(99)<200"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const user = `user-00${(__VU % 8) + 1}`;
  const response = http.get(
    `http://localhost:8000/v1/recommendations?user_id=${user}&limit=10`,
  );
  check(response, {
    "status is 200": (result) => result.status === 200,
    "returns model version": (result) => Boolean(result.json("model_version")),
  });
  sleep(0.1);
}
