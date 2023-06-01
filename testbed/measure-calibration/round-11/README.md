This campgaign of test was starting at jeudi 1 juin 2023, 13:00:57 (UTC+0200).
Each test result is in a folder whose name uses this format: `type-bandwidth-duration`
- `type`: either `legit` (legitime traffic) or `unrespECN` or `iperf3`
- `bandwidth`: limit bandwidth at the client side in Mbps.
- `duration`: the duration of request sent by the client before being stopped
Limit traffic at the egress ports of the P4 switch using Mahimahi. Run in client/server C which have installed Ubuntu 20.04, and TCP-Prague from source.

Double test. Fixed bug which removes picolog.
