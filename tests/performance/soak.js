import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  discardResponseBodies: true,
  scenarios: {
    soak: {
      executor: 'constant-vus',
      vus: 10,
      duration: '10m',
      gracefulStop: '10s'
    }
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<200'],
    checks: ['rate>0.99']
  }
};

export default function () {
  const res = http.get(
    `${__ENV.BASE_URL}/api/products/cheapest`,
    { timeout: '5s' }
  );

  check(res, {
    'HTTP 200': r => r.status === 200
  });

  sleep(0.6);
}
