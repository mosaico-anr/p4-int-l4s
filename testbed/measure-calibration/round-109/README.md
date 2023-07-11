This campgaign of test was starting at mardi 11 juillet 2023, 04:37:46 (UTC+0200).
Each test result is in a folder whose name uses this format: `type-bandwidth-duration-nb_clients-nb_servers`
- `type`: either `legit` (legitime traffic) or `unrespECN` or `iperf3`
- `bandwidth`: limit bandwidth at the client side in Mbps. 0 == unlimited
- `duration`: the duration of request sent by the client before being stopped
- `nb_clients`: number of clients
- `nb_servers`: number of servers

Limit traffic at the egress ports of the P4 switch using Mahimahi. Run in client/server C which have installed Ubuntu 20.04, and TCP-Prague from source.

Double test. Fixed bug which removes picolog. 
Use new way to start picoquic client & server (02 Juin).
Test unlimited bandwidth.

No random spinbit (05 June):
picoquic_set_default_spinbit_policy(quic, picoquic_spinbit_on);

Extract the interested metrics from data.csv to new_data.csv (09 June 2023)

Different numbers of clients and servers (09 June)

Disable TCP cache; add metric avg packet size; nb packets (13 June)
