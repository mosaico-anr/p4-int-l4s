This campgaign of test was starting at Sun Feb 19 20:26:35 UTC 2023.
Each test result is in a folder whose name uses this format: `flowA--flowB--date `,
in which `flowA` and `flowB` has: `type-bandwidth-start_time-duration`
- `type`: either `legit` (legitime traffic) or `unrespECN`
- `bandwidth`: limit bandwidth at the client side in Kbps. Set to 0Kbps to unlimit.
- `start_time`: the client sleeps X seconds before sending request
- `duration`: the duration of request sent by the client before being stopped
LL traffic is classified by using ECN==3
