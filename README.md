# Introduction

- This repository contains an implementaion a monitoring system by using [In-band Network Telemetry](https://p4.org/p4-spec/docs/INT_v2_1.pdf) and [P4](https://p4.org) language.
- It is to monitor [L4S](https://datatracker.ietf.org/doc/draft-ietf-tsvwg-l4s-arch) P4-based switches.
- It has been tested using [BMv2 virtual switches](https://github.com/p4lang/behavioral-model)

<img src=https://raw.githubusercontent.com/mosaico-anr/p4-int-l4s/main/archi_monitoring.jpg width=600px>

# Structure

- `.p4`: P4 source codes that implements INT
- `testbed`: script to run our internal testbed and some seletected results
   + `client-server`: C or Python codes of programs to generate traffic and microburst
   + `log`: selected results which measure different overheads caused by the INT monitoring system
   + `measure-monitoring-delay`: selected results which measure the delay of monitoring metrics' values
   

# License

- This repository is copyrighted by Montimage. It is released under [MIT license](./LICENSE).
- It is part of the French National Research Agency (ANR) [MOSAICO project](https://www.mosaico-project.org/), under grant No ANR-19-CE25-0012.



Made with ❤️ by [@nhnghia](https://github.com/nhnghia)
