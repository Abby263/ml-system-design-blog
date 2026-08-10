import http from "k6/http";
import { check } from "k6";


export const options = {
  scenarios: {
    burst: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.RPS || 50),
      timeUnit: "1s",
      duration: __ENV.DURATION || "30s",
      preAllocatedVUs: 20,
      maxVUs: 100,
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<50"],
  },
};


export default function () {
  const response = http.get(
    `${__ENV.BASE_URL || "http://localhost:8000"}/public-data`,
    { headers: { "X-API-Key": __ENV.API_KEY || "load-test-client" } },
  );
  check(response, {
    "allowed or intentionally limited": (result) =>
      result.status === 200 || result.status === 429,
    "communicates policy": (result) => Boolean(result.headers.RatelimitPolicy),
  });
}
