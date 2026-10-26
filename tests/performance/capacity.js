import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '20s',
  discardResponseBodies: true,
  thresholds: {
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.99']
  }
};

export default function () {
  const res = http.get(__ENV.TARGET_URL, {
    timeout: '5s'
  });

  check(res, {
    'HTTP 200': r => r.status === 200
  });

  sleep(0.1);
}
