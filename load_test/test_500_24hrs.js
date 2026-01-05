import http from 'k6/http';
import { check, sleep } from 'k6';

// Config
export const options = {

  discardResponseBodies: true,         // download the test
  // This defines how the traffic flows
  stages: [
    { duration: '1m', target: 100 },  // RAMP UP: Grow from 0 to 100 users over 1 minute
    { duration: '10m', target: 100 }, // STEADY: Stay at 100 users for 10 minutes 
    { duration: '1m', target: 0 },    // RAMP DOWN: Gracefully disconnect users over 1 minute
  ],

  // Pass/Fail criteria
  thresholds: {
    http_req_failed: ['rate<0.01'],  // Test fails if error rate is > 1%
    http_req_duration: ['p(95)<1000'], // Test fails if 95% of requests take > 1 second
  },
};

// -----------------------------------------------------------------------
// 2. THE TEST LOGIC
// -----------------------------------------------------------------------
export default function () {
  // *** REPLACE THIS URL WITH YOUR TARGET ***
  const url = 'http://cloud-computing-frontend-20260105.s3-website-us-east-1.amazonaws.com/'; //20260101

  // Make the request
  const res = http.get(url);

  // Validate the response
  check(res, {
    'status is 200': (r) => r.status === 200
  });

const resData = http.get('https://b95oaxxipi.execute-api.us-east-1.amazonaws.com/dev/request_24hrs?lat=51.698&lon=-0.293'); //-0.292
check(resData, { 
    'Data Loaded': (r) => r.status === 200
  });

  sleep(2); 
}