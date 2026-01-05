import http from 'k6/http';
import { check, sleep } from 'k6';

// Config
export const options = {
  // dont download response bodies for prevent memory issues
  discardResponseBodies: true,         
  // This defines how the traffic flows : 2000 users
  stages: [
    { duration: '1m', target: 2000 },  // RAMP UP
    { duration: '10m', target: 2000 }, // STEADY
    { duration: '1m', target: 0 },    // RAMP DOWN
  ],

  // Pass/Fail criteria
  thresholds: {
    http_req_failed: ['rate<0.01'],  // Test fails if error rate is > 1%
    http_req_duration: ['p(95)<1000'], // Test fails if 95% of requests take > 1 second
  },
};

// -----------------------------------------------------------------------
// The TEST LOGIC
// -----------------------------------------------------------------------
export default function () {
  const url = 'http://cloud-computing-frontend-20260101.s3-website-us-east-1.amazonaws.com/'; 
  const res = http.get(url);
  // Validate the response
  check(res, {
    'status is 200': (r) => r.status === 200
  });
  const resData = http.get('https://b95oaxxipi.execute-api.us-east-1.amazonaws.com/dev/request_24hrs?lat=51.698&lon=-0.292'); //link is copied from index.html
  check(resData, { 
    'Data Loaded': (r) => r.status === 200
  });
  sleep(2); 
}