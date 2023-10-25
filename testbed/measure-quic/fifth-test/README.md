This folder contains the tests which consist only one type of flow, with different bandwidth. Basically each test is generated as [the following](https://github.com/mosaico-anr/p4-int-l4s/blob/main/testbed/measure-quic/fifth-test/run-test-campaign.sh):

```bash
for round in 1 2 3 4
  index = 0
  for bandwidth in 1 2 5 10
    for power_attack in 0 0.1 0.2 0.5 1
      for traffic_confs in "${TRAFFIC_CFG[@]}"
        if power_attack != 0 && "unrespECN" not in traffic_confs then
          skip-this-test
        fi
        index += 1
        run-test( index, bandwidth, power_attack, traffic_types )
      done
    done
  done
done
```

`traffic_confs` is configured using the following syntax: 
  `traffic_conf;trafic_conf;...`
  
and `traffic_conf` is a 4-tuple (`type, start_time, duration, server_port`)
- `type` is one of `ll_legit`, `cl_legit` and `unrespECN`
- `start_time` the moment, in second, the flow is started
- `duration` the duration, in second, the flow is living, i.e., the flow will be terminated at `start_time + duration`
- `server_port` the port number of its picoquic server


The tests in this `fifth-test` folder uses the following configurations:

```bash
# 1x: single flow type
ll_legit,0,120,3000
cl_legit,0,120,2000
unrespECN,0,120,3000
#
# 2x traffic
ll_legit,0,120,3000;ll_legit,30,60,3001
cl_legit,0,120,2000;cl_legit,30,60,2001
unrespECN,0,120,10000;unrespECN,30,60,10001
#
# 5x
ll_legit,0,120,3000; ll_legit,5, 60,3001; ll_legit,10,60,3002; ll_legit,15,60,3003; ll_legit,20,60,3004
cl_legit,0,120,2000; cl_legit,5, 60,2001; cl_legit,10,60,2002; cl_legit,15,60,2003; cl_legit,20,60,2004
unrespECN,0,120,1000; unrespECN,5, 60,1001; unrespECN,10,60,1002; unrespECN,15,60,1003; unrespECN,20,60,1004
#
# 10x
ll_legit,0,120,3000; ll_legit, 5,60,3001; ll_legit,10,60,3002; ll_legit,15,60,3003; ll_legit,20,60,3004; ll_legit,25,60,3005; ll_legit,30,60,3006; ll_legit,35,60,3007; ll_legit,40,60,3008; ll_legit,45,60,3009
cl_legit,0,120,2000; cl_legit, 5,60,2001; cl_legit,10,60,2002; cl_legit,15,60,2003; cl_legit,20,60,2004; cl_legit,25,60,2005; cl_legit,30,60,2006; cl_legit,35,60,2007; cl_legit,40,60,2008; cl_legit,45,60,2009
unrespECN,0,120,1000; unrespECN, 5,60,1001; unrespECN,10,60,1002; unrespECN,15,60,1003; unrespECN,20,60,1004; unrespECN,25,60,1005; unrespECN,30,60,1006; unrespECN,35,60,1007; unrespECN,40,60,1008; unrespECN,45,60,1009
```

