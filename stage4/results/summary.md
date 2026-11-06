# E10 -- emulated testbed (Stage 4) summary

13 live sessions. Detector = deployed final-system model (stat_slo registry head); policy = cusum_sprt_mix; evidence = monotone_balanced; threshold = Lorden h.


## Access-control outcomes (real per-device MQTT sessions)

| run | rho | m | wrong grant | detect | tti med | false iso | false reauth | reach | benign deny |
|---|---|---|---|---|---|---|---|---|---|
| e10_edgeiiot_clean |  | 0 | - | - | - | 0 | - | - | 0.0048 |
| e10_edgeiiot_m2_rho0.2 | 0.2 | 2 | 0 | 1 | 35 | 0 | 0 | 0 | 0.00425 |
| e10_edgeiiot_m2_rho0.5 | 0.5 | 2 | 0 | 1 | 5.5 | 0 | 0 | 0 | 0.00425 |
| e10_edgeiiot_m2_rho1.0 | 1.0 | 2 | 0 | 1 | 2 | 0 | 0 | 0 | 0.00425 |
| e10_edgeiiot_m2_rho1.0_evm | 1.0 | 2 | 0 | 1 | 2 | 0 | 0 | 0 | 0.00425 |
| e10_forge_clean |  | 0 | - | - | - | 0 | - | - | 0.0124 |
| e10_forge_m2_rho0.2 | 0.2 | 2 | 0 | 1 | 35 | 0 | 0 | 0 | 0.0115 |
| e10_forge_m2_rho0.5 | 0.5 | 2 | 0 | 1 | 5.5 | 0 | 0 | 0 | 0.0115 |
| e10_forge_m2_rho1.0 | 1.0 | 2 | 0 | 1 | 2 | 0 | 0 | 0 | 0.0115 |
| e10_wustl_clean |  | 0 | - | - | - | 0 | - | - | 0 |
| e10_wustl_m2_rho0.2 | 0.2 | 2 | 0.0574 | 1 | 41 | 0 | 0 | 3.5 | 0 |
| e10_wustl_m2_rho0.5 | 0.5 | 2 | 0.00351 | 1 | 5.5 | 0 | 0 | 0.5 | 0 |
| e10_wustl_m2_rho1.0 | 1.0 | 2 | 0.00186 | 1 | 2 | 0 | 0 | 0.5 | 0 |

## Testbed facts (not available in simulation)

| run | events | detector ms/event | ledger blocks | chain | verified | wall s |
|---|---|---|---|---|---|---|
| e10_edgeiiot_clean | 5000 | 0.404 | 51 | memory | True | 11.7 |
| e10_edgeiiot_m2_rho0.2 | 5000 | 0.317 | 51 | memory | True | 12.0 |
| e10_edgeiiot_m2_rho0.5 | 5000 | 0.269 | 51 | memory | True | 11.4 |
| e10_edgeiiot_m2_rho1.0 | 5000 | 0.306 | 51 | memory | True | 13.3 |
| e10_edgeiiot_m2_rho1.0_evm | 5000 | 0.313 | 51 | evm 1.0205868359771557s/batch | True | 11.4 |
| e10_forge_clean | 5000 | 0.316 | 51 | memory | True | 11.6 |
| e10_forge_m2_rho0.2 | 5000 | 0.283 | 51 | memory | True | 11.4 |
| e10_forge_m2_rho0.5 | 5000 | 0.329 | 51 | memory | True | 13.8 |
| e10_forge_m2_rho1.0 | 5000 | 0.295 | 51 | memory | True | 11.5 |
| e10_wustl_clean | 5000 | 0.285 | 51 | memory | True | 13.2 |
| e10_wustl_m2_rho0.2 | 5000 | 0.247 | 51 | memory | True | 11.9 |
| e10_wustl_m2_rho0.5 | 5000 | 0.257 | 51 | memory | True | 11.4 |
| e10_wustl_m2_rho1.0 | 5000 | 0.375 | 51 | memory | True | 14.1 |