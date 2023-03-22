This campgaign of test was starting at Wed Mar 22 12:23:30 UTC 2023.
Each test result is in a folder whose name uses this format: `type-bandwidth-duration`
- `type`: either `legit` (legitime traffic) or `unrespECN` or `iperf3`
- `bandwidth`: limit bandwidth at the client side in Mbps.
- `duration`: the duration of request sent by the client before being stopped
Limit traffic at the egress ports of the P4 switch using Mahimahi
