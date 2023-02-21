This campgaign of test was starting at Tue Feb 21 13:22:23 UTC 2023.
Each test result is in a folder whose name uses this format: `type-bandwidth-duration`
- `type`: either `legit` (legitime traffic) or `unrespECN` or `iperf3`
- `bandwidth`: limit bandwidth at the client side in Kbps. Set to 0Kbps to unlimit.
- `duration`: the duration of request sent by the client before being stopped
LL traffic is classified by using ECN==3
