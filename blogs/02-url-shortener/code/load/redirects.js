import http from "k6/http";
import { check, sleep } from "k6";


export const options = {
  scenarios: {
    hot_links: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.RPS || 500),
      timeUnit: "1s",
      duration: __ENV.DURATION || "60s",
      preAllocatedVUs: 50,
      maxVUs: 500,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<100"],
  },
};


const baseUrl = __ENV.BASE_URL || "http://localhost:8000";
const shortCode = __ENV.SHORT_CODE || "1000000";


export default function () {
  const response = http.get(`${baseUrl}/${shortCode}`, { redirects: 0 });
  check(response, {
    "returns 307": (result) => result.status === 307,
    "has Location": (result) => Boolean(result.headers.Location),
  });
  sleep(0.01);
}
