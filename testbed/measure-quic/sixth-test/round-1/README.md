This campgaign of test was starting at $(date).
Each test result is in a folder whose name uses this format: `index_bandwidth_pattack-flows`
- `index`: order of test
- `bandwidth`: limit bandwidth at the P4 switch, in Mbps. 0 == unlimited
- `pattack`: the power of attack (only for unrespECN)
- `flows`: detailed configuration of each flow. This configuration can be trimmed to keep folder name < 255 characters. Full configuration is in `param.json` file inside each folder.
