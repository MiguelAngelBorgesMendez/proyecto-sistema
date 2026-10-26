import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  discardResponseBodies: true,
  scenarios: {
    spike: {
      executor: 'ramping-vus',
      startVUs: 5,
      stages: [
        { duration: '10s', target: 5 },
        { duration: '2s', target: 300 },
        { duration: '8s', target: 300 },
        { duration: '3s', target: 5 },
        { duration: '10s', target: 5 },
        { duration: '2s', target: 0 }
      ],
      gracefulRampDown: '3s',
      gracefulStop: '5s'
    }
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    checks: ['rate>0.95']
  }
};

export default function () {
  const response = http.get(
    `${__ENV.BASE_URL}/api/products/cheapest`,
    { timeout: '3s' }
  );

  check(response, {
    'HTTP 200': (r) => r.status === 200
  });

  sleep(0.6);
}
