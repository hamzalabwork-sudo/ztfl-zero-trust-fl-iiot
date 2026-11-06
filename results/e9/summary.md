# E9 summary

trust runs: 630; ledger ok 630, gateway on registry head 630.


## evaluation seeds 43-46


**backdoor success excess, final deployed model (pp)** (m 1-3 pooled)

| dataset | attack | onset | aggregator | canary_stat_slo / baseline | canary_stat_slo / trust | last / baseline | last / trust |
|---|---|---|---|---|---|---|---|
| edgeiiot | backdoor | 1 | fedavg | 4 | 0.3 | 97.8 | 0.3 |
| edgeiiot | backdoor | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor | 11 | fedavg | 0 | 0.1 | 97.8 | 0.1 |
| edgeiiot | backdoor | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor_adaptive | 1 | fedavg | 53.3 | 5.6 | 53.7 | 5.6 |
| edgeiiot | backdoor_adaptive | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor_adaptive | 11 | fedavg | 3.6 | 1.3 | 3.7 | 1.3 |
| edgeiiot | backdoor_adaptive | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 1 | fedavg | 0 | 0 | 0.1 | 0 |
| edgeiiot | label_flip | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 11 | fedavg | 0.1 | 0.1 | 0.1 | 0.1 |
| edgeiiot | label_flip | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | none | 1 | fedavg | 0 | 0 | 0 | 0 |
| edgeiiot | none | 1 | multi_krum | 0 | 0 | 0 | 0 |
| forge | backdoor | 1 | fedavg | 6.8 | 0.9 | 87.2 | 2.3 |
| forge | backdoor | 1 | multi_krum | 0.1 | -0.2 | 0 | -0.1 |
| forge | backdoor | 11 | fedavg | 1.6 | 1 | 91.9 | 1.2 |
| forge | backdoor | 11 | multi_krum | 0 | -0.3 | -0 | -0.2 |
| forge | backdoor_adaptive | 1 | fedavg | 41.7 | 21.9 | 51.9 | 21.9 |
| forge | backdoor_adaptive | 1 | multi_krum | 0.1 | -0.2 | 0 | -0.1 |
| forge | backdoor_adaptive | 11 | fedavg | 3.8 | 3.4 | 4.8 | 3.4 |
| forge | backdoor_adaptive | 11 | multi_krum | -0 | -0.4 | 0.2 | -0.4 |
| forge | label_flip | 1 | fedavg | 2 | -0.2 | 3.1 | -0.2 |
| forge | label_flip | 1 | multi_krum | 0 | -0.1 | -0 | -0.1 |
| forge | label_flip | 11 | fedavg | 0.3 | 0.2 | 2.8 | 0.2 |
| forge | label_flip | 11 | multi_krum | 0.1 | -0.2 | 0.1 | -0.1 |
| forge | none | 1 | fedavg | 0 | 0 | 0 | 0 |
| forge | none | 1 | multi_krum | 0 | 0 | 0 | 0 |
| wustl | backdoor | 1 | fedavg | 30.4 | 13 | 75.2 | 13 |
| wustl | backdoor | 1 | multi_krum | 3.1 | 3.1 | 3.1 | 3.1 |
| wustl | backdoor | 11 | fedavg | 23.8 | 11.4 | 67.1 | 11.4 |
| wustl | backdoor | 11 | multi_krum | 3.3 | 3.3 | 3.3 | 3.3 |
| wustl | backdoor_adaptive | 1 | fedavg | 41.3 | 33.9 | 51.2 | 33.9 |
| wustl | backdoor_adaptive | 1 | multi_krum | 2.9 | 2.9 | 2.9 | 2.9 |
| wustl | backdoor_adaptive | 11 | fedavg | 24.8 | 22.7 | 24.8 | 22.7 |
| wustl | backdoor_adaptive | 11 | multi_krum | 3.3 | 3.3 | 3.3 | 3.3 |
| wustl | label_flip | 1 | fedavg | -2.9 | -1.7 | 14.1 | -1.7 |
| wustl | label_flip | 1 | multi_krum | 0.2 | 0.2 | 0.2 | 0.2 |
| wustl | label_flip | 11 | fedavg | 0.6 | 2.3 | 11 | 2.3 |
| wustl | label_flip | 11 | multi_krum | 1 | 1 | 1 | 1 |
| wustl | none | 1 | fedavg | 0 | 0 | 0 | 0 |
| wustl | none | 1 | multi_krum | -0 | 0 | -0 | 0 |


**exposure: max backdoor success while deployed (%)** (m 1-3 pooled)

| dataset | attack | onset | aggregator | canary_stat_slo / baseline | canary_stat_slo / trust | last / baseline | last / trust |
|---|---|---|---|---|---|---|---|
| edgeiiot | backdoor | 1 | fedavg | 4.2 | 4.5 | 99 | 97.3 |
| edgeiiot | backdoor | 1 | multi_krum | 0.1 | 0.1 | 0.1 | 0.1 |
| edgeiiot | backdoor | 11 | fedavg | 0.1 | 0.6 | 99.4 | 91.4 |
| edgeiiot | backdoor | 11 | multi_krum | 0.1 | 0.1 | 0.1 | 0.1 |
| edgeiiot | backdoor_adaptive | 1 | fedavg | 53.8 | 53.8 | 54.6 | 54.3 |
| edgeiiot | backdoor_adaptive | 1 | multi_krum | 0.1 | 0.1 | 0.1 | 0.1 |
| edgeiiot | backdoor_adaptive | 11 | fedavg | 3.9 | 3.5 | 4.1 | 3.8 |
| edgeiiot | backdoor_adaptive | 11 | multi_krum | 0.1 | 0.1 | 0.1 | 0.1 |
| edgeiiot | label_flip | 1 | fedavg | 0.1 | 0.1 | 0.2 | 0.2 |
| edgeiiot | label_flip | 1 | multi_krum | 0.1 | 0.1 | 0.1 | 0.1 |
| edgeiiot | label_flip | 11 | fedavg | 0.1 | 0.1 | 0.2 | 0.2 |
| edgeiiot | label_flip | 11 | multi_krum | 0.1 | 0.1 | 0.1 | 0.1 |
| edgeiiot | none | 1 | fedavg | 0.1 | 0.1 | 0.1 | 0.1 |
| edgeiiot | none | 1 | multi_krum | 0.1 | 0.1 | 0.1 | 0.1 |
| forge | backdoor | 1 | fedavg | 13.8 | 12 | 99.7 | 99.3 |
| forge | backdoor | 1 | multi_krum | 2.1 | 2 | 2.1 | 2.1 |
| forge | backdoor | 11 | fedavg | 3.3 | 5.4 | 99.7 | 99.7 |
| forge | backdoor | 11 | multi_krum | 1.6 | 1.4 | 1.6 | 1.4 |
| forge | backdoor_adaptive | 1 | fedavg | 49.4 | 49.4 | 60.6 | 59.9 |
| forge | backdoor_adaptive | 1 | multi_krum | 2.1 | 2 | 2.1 | 2.1 |
| forge | backdoor_adaptive | 11 | fedavg | 5.7 | 5.6 | 6.8 | 6.8 |
| forge | backdoor_adaptive | 11 | multi_krum | 1.7 | 1.2 | 2 | 1.3 |
| forge | label_flip | 1 | fedavg | 5.6 | 5.3 | 7.1 | 5.8 |
| forge | label_flip | 1 | multi_krum | 1.7 | 1.8 | 1.8 | 1.9 |
| forge | label_flip | 11 | fedavg | 2.1 | 2.4 | 4.8 | 3.4 |
| forge | label_flip | 11 | multi_krum | 1.5 | 1.3 | 1.6 | 1.3 |
| forge | none | 1 | fedavg | 2 | 2.1 | 2 | 2.1 |
| forge | none | 1 | multi_krum | 2.7 | 2.8 | 2.8 | 2.9 |
| wustl | backdoor | 1 | fedavg | 49.8 | 48.1 | 92.6 | 89 |
| wustl | backdoor | 1 | multi_krum | 26.2 | 26.2 | 26.2 | 26.2 |
| wustl | backdoor | 11 | fedavg | 38 | 32.6 | 90.7 | 88.6 |
| wustl | backdoor | 11 | multi_krum | 18.2 | 18.2 | 18.2 | 18.2 |
| wustl | backdoor_adaptive | 1 | fedavg | 61 | 64.5 | 70 | 70.9 |
| wustl | backdoor_adaptive | 1 | multi_krum | 26.2 | 26.2 | 26.2 | 26.2 |
| wustl | backdoor_adaptive | 11 | fedavg | 41.7 | 42.4 | 42.4 | 42.6 |
| wustl | backdoor_adaptive | 11 | multi_krum | 18.2 | 18.2 | 18.2 | 18.2 |
| wustl | label_flip | 1 | fedavg | 21.3 | 22.9 | 43.8 | 41.9 |
| wustl | label_flip | 1 | multi_krum | 28.1 | 28.1 | 28.1 | 28.1 |
| wustl | label_flip | 11 | fedavg | 18.4 | 20.2 | 29.1 | 20.2 |
| wustl | label_flip | 11 | multi_krum | 17.1 | 17.1 | 17.1 | 17.1 |
| wustl | none | 1 | fedavg | 27.3 | 27.3 | 27.3 | 27.3 |
| wustl | none | 1 | multi_krum | 31.8 | 31.8 | 31.8 | 31.8 |


**revocations (full system)**

| dataset | attack | onset | aggregator | runs | attackers | revoked_true | revoked_false | first_true_mean | no_model_rounds |
|---|---|---|---|---|---|---|---|---|---|
| edgeiiot | backdoor | 1 | fedavg | 12 | 24 | 21 | 0 | 8.5 | 0 |
| edgeiiot | backdoor | 1 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| edgeiiot | backdoor | 11 | fedavg | 12 | 24 | 22 | 0 | 13.08 | 0 |
| edgeiiot | backdoor | 11 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| edgeiiot | backdoor_adaptive | 1 | fedavg | 12 | 24 | 17 | 0 | 8.27 | 0 |
| edgeiiot | backdoor_adaptive | 1 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| edgeiiot | backdoor_adaptive | 11 | fedavg | 12 | 24 | 14 | 0 | 12.89 | 0 |
| edgeiiot | backdoor_adaptive | 11 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| edgeiiot | label_flip | 1 | fedavg | 12 | 24 | 1 | 0 | 15 | 0 |
| edgeiiot | label_flip | 1 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| edgeiiot | label_flip | 11 | fedavg | 12 | 24 | 0 | 0 |  | 0 |
| edgeiiot | label_flip | 11 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| edgeiiot | none | 1 | fedavg | 12 | 24 | 0 | 0 |  | 0 |
| edgeiiot | none | 1 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| forge | backdoor | 1 | fedavg | 12 | 24 | 23 | 17 | 7.25 | 1.75 |
| forge | backdoor | 1 | multi_krum | 12 | 24 | 2 | 8 | 11 | 0 |
| forge | backdoor | 11 | fedavg | 12 | 24 | 21 | 2 | 12.5 | 0 |
| forge | backdoor | 11 | multi_krum | 12 | 24 | 2 | 8 | 10 | 0 |
| forge | backdoor_adaptive | 1 | fedavg | 12 | 24 | 13 | 7 | 7.86 | 0.67 |
| forge | backdoor_adaptive | 1 | multi_krum | 12 | 24 | 2 | 8 | 11 | 0 |
| forge | backdoor_adaptive | 11 | fedavg | 12 | 24 | 5 | 2 | 12 | 0 |
| forge | backdoor_adaptive | 11 | multi_krum | 12 | 24 | 4 | 9 | 11 | 0 |
| forge | label_flip | 1 | fedavg | 12 | 24 | 10 | 2 | 17.75 | 0 |
| forge | label_flip | 1 | multi_krum | 12 | 24 | 0 | 6 |  | 0 |
| forge | label_flip | 11 | fedavg | 12 | 24 | 7 | 2 | 13.43 | 0 |
| forge | label_flip | 11 | multi_krum | 12 | 24 | 2 | 6 | 10 | 0 |
| forge | none | 1 | fedavg | 12 | 24 | 0 | 0 |  | 0 |
| forge | none | 1 | multi_krum | 12 | 24 | 0 | 12 |  | 0 |
| wustl | backdoor | 1 | fedavg | 12 | 24 | 15 | 0 | 10.73 | 0.25 |
| wustl | backdoor | 1 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| wustl | backdoor | 11 | fedavg | 12 | 24 | 14 | 0 | 13.7 | 0 |
| wustl | backdoor | 11 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| wustl | backdoor_adaptive | 1 | fedavg | 12 | 24 | 8 | 1 | 16.5 | 0.25 |
| wustl | backdoor_adaptive | 1 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| wustl | backdoor_adaptive | 11 | fedavg | 12 | 24 | 3 | 1 | 13 | 0 |
| wustl | backdoor_adaptive | 11 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| wustl | label_flip | 1 | fedavg | 12 | 24 | 7 | 4 | 7.67 | 0.75 |
| wustl | label_flip | 1 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| wustl | label_flip | 11 | fedavg | 12 | 24 | 4 | 0 | 12.33 | 0 |
| wustl | label_flip | 11 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |
| wustl | none | 1 | fedavg | 12 | 24 | 0 | 0 |  | 0 |
| wustl | none | 1 | multi_krum | 12 | 24 | 0 | 0 |  | 0 |


**gateway, target streams, attack events granted % (full system, deployed head)**

| dataset | attack | onset | aggregator | wrong:monotone/rho1 | wrong:monotone/rho0.2 | wrong:monotone_balanced/rho1 | wrong:monotone_balanced/rho0.2 |
|---|---|---|---|---|---|---|---|
| edgeiiot | backdoor | 1 | fedavg | 0 | 0.17 | 0 | 0.17 |
| edgeiiot | backdoor | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor | 11 | fedavg | 0 | 0.06 | 0 | 0.06 |
| edgeiiot | backdoor | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor_adaptive | 1 | fedavg | 0.06 | 2.22 | 0.06 | 2.22 |
| edgeiiot | backdoor_adaptive | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor_adaptive | 11 | fedavg | 0.01 | 0.51 | 0.01 | 0.51 |
| edgeiiot | backdoor_adaptive | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 1 | fedavg | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 11 | fedavg | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | label_flip | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | none | 1 | fedavg | 0 | 0 | 0 | 0 |
| edgeiiot | none | 1 | multi_krum | 0 | 0.01 | 0 | 0.01 |
| forge | backdoor | 1 | fedavg | 1.7 | 2.3 | 0.03 | 1.8 |
| forge | backdoor | 1 | multi_krum | 0.01 | 0.73 | 0.01 | 0.33 |
| forge | backdoor | 11 | fedavg | 0.07 | 2.33 | 0.03 | 1.32 |
| forge | backdoor | 11 | multi_krum | 0.01 | 0.6 | 0.01 | 0.37 |
| forge | backdoor_adaptive | 1 | fedavg | 3.41 | 23.33 | 0.28 | 13.92 |
| forge | backdoor_adaptive | 1 | multi_krum | 0.01 | 0.73 | 0.01 | 0.33 |
| forge | backdoor_adaptive | 11 | fedavg | 0.11 | 4.68 | 0.05 | 2.21 |
| forge | backdoor_adaptive | 11 | multi_krum | 0.01 | 0.51 | 0.01 | 0.32 |
| forge | label_flip | 1 | fedavg | 0.01 | 0.76 | 0.01 | 0.39 |
| forge | label_flip | 1 | multi_krum | 0.01 | 0.68 | 0.01 | 0.43 |
| forge | label_flip | 11 | fedavg | 0.02 | 1.13 | 0.01 | 0.6 |
| forge | label_flip | 11 | multi_krum | 0.01 | 0.62 | 0.01 | 0.35 |
| forge | none | 1 | fedavg | 0.01 | 0.97 | 0.01 | 0.4 |
| forge | none | 1 | multi_krum | 0.01 | 0.71 | 0.01 | 0.32 |
| wustl | backdoor | 1 | fedavg | 0.65 | 19.08 | 0.3 | 10.99 |
| wustl | backdoor | 1 | multi_krum | 0.15 | 3.48 | 0.12 | 2.64 |
| wustl | backdoor | 11 | fedavg | 0.59 | 18.21 | 0.27 | 9.72 |
| wustl | backdoor | 11 | multi_krum | 0.15 | 3.62 | 0.13 | 2.82 |
| wustl | backdoor_adaptive | 1 | fedavg | 1.58 | 45.14 | 0.54 | 23.5 |
| wustl | backdoor_adaptive | 1 | multi_krum | 0.15 | 3.51 | 0.12 | 2.7 |
| wustl | backdoor_adaptive | 11 | fedavg | 1.1 | 36.46 | 0.42 | 18.3 |
| wustl | backdoor_adaptive | 11 | multi_krum | 0.15 | 3.62 | 0.13 | 2.82 |
| wustl | label_flip | 1 | fedavg | 0.16 | 3.57 | 0.13 | 3.1 |
| wustl | label_flip | 1 | multi_krum | 0.12 | 2.93 | 0.1 | 2.45 |
| wustl | label_flip | 11 | fedavg | 0.18 | 4 | 0.15 | 2.98 |
| wustl | label_flip | 11 | multi_krum | 0.13 | 3.21 | 0.11 | 2.62 |
| wustl | none | 1 | fedavg | 0.15 | 3.48 | 0.12 | 2.69 |
| wustl | none | 1 | multi_krum | 0.12 | 2.94 | 0.09 | 1.98 |


## design seed 42


**backdoor success excess, final deployed model (pp)** (m 1-3 pooled)

| dataset | attack | onset | aggregator | canary_stat_slo / baseline | canary_stat_slo / trust | last / baseline | last / trust |
|---|---|---|---|---|---|---|---|
| edgeiiot | backdoor | 1 | fedavg | 3 | 0 | 97.9 | 0 |
| edgeiiot | backdoor | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor | 11 | fedavg | 0 | 0.3 | 97.6 | 0.3 |
| edgeiiot | backdoor | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor_adaptive | 1 | fedavg | 54.2 | 0 | 52.2 | 0 |
| edgeiiot | backdoor_adaptive | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor_adaptive | 11 | fedavg | 4.2 | 1.7 | 4.3 | 1.7 |
| edgeiiot | backdoor_adaptive | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 1 | fedavg | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 11 | fedavg | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | none | 1 | fedavg | 0 | 0 | 0 | 0 |
| edgeiiot | none | 1 | multi_krum | 0 | 0 | 0 | 0 |
| forge | backdoor | 1 | fedavg | 19.6 | 5.3 | 72.2 | 5.3 |
| forge | backdoor | 1 | multi_krum | 0.1 | 0.1 | 0.1 | 0.1 |
| forge | backdoor | 11 | fedavg | 0 | 0 | 72.7 | 33.2 |
| forge | backdoor | 11 | multi_krum | 0 | 0 | 0.1 | 0 |
| forge | backdoor_adaptive | 1 | fedavg | 38.8 | 16.4 | 44.4 | 16.4 |
| forge | backdoor_adaptive | 1 | multi_krum | 0.1 | 0.1 | 0.1 | 0.1 |
| forge | backdoor_adaptive | 11 | fedavg | 0 | 0.1 | 2.9 | 1 |
| forge | backdoor_adaptive | 11 | multi_krum | 0 | 0 | 0.1 | 0 |
| forge | label_flip | 1 | fedavg | 5.3 | 0.9 | 5.3 | 0.9 |
| forge | label_flip | 1 | multi_krum | 0.1 | 0 | 0.1 | 0 |
| forge | label_flip | 11 | fedavg | 0 | 0.1 | 5.1 | 0.1 |
| forge | label_flip | 11 | multi_krum | 0 | 0 | 0.1 | 0 |
| forge | none | 1 | fedavg | 0 | 0 | 0 | 0 |
| forge | none | 1 | multi_krum | 0 | 0 | 0 | 0 |
| wustl | backdoor | 1 | fedavg | 1.6 | 6.2 | 72.1 | 6.2 |
| wustl | backdoor | 1 | multi_krum | 0.8 | 0.8 | 0.8 | 0.8 |
| wustl | backdoor | 11 | fedavg | 9.3 | 3.9 | 69 | 3.9 |
| wustl | backdoor | 11 | multi_krum | 0.8 | 0.8 | 0.8 | 0.8 |
| wustl | backdoor_adaptive | 1 | fedavg | 57.4 | 28.7 | 57.4 | 28.7 |
| wustl | backdoor_adaptive | 1 | multi_krum | 0.8 | 0.8 | 0.8 | 0.8 |
| wustl | backdoor_adaptive | 11 | fedavg | 22.5 | 22.5 | 22.5 | 22.5 |
| wustl | backdoor_adaptive | 11 | multi_krum | 0.8 | 0.8 | 0.8 | 0.8 |
| wustl | label_flip | 1 | fedavg | 3.1 | 3.1 | 3.1 | 3.1 |
| wustl | label_flip | 1 | multi_krum | -7 | -7 | 21.7 | 21.7 |
| wustl | label_flip | 11 | fedavg | 1.6 | 1.6 | 1.6 | 1.6 |
| wustl | label_flip | 11 | multi_krum | 2.3 | 2.3 | 2.3 | 2.3 |
| wustl | none | 1 | fedavg | 0 | 0 | 0 | 0 |
| wustl | none | 1 | multi_krum | 0 | 0 | 0 | 0 |


**exposure: max backdoor success while deployed (%)** (m 1-3 pooled)

| dataset | attack | onset | aggregator | canary_stat_slo / baseline | canary_stat_slo / trust | last / baseline | last / trust |
|---|---|---|---|---|---|---|---|
| edgeiiot | backdoor | 1 | fedavg | 3 | 3.2 | 97.9 | 95.2 |
| edgeiiot | backdoor | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor | 11 | fedavg | 0 | 0.6 | 100 | 100 |
| edgeiiot | backdoor | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor_adaptive | 1 | fedavg | 55.3 | 54.9 | 56.3 | 55.4 |
| edgeiiot | backdoor_adaptive | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | backdoor_adaptive | 11 | fedavg | 4.4 | 3.2 | 4.6 | 4.4 |
| edgeiiot | backdoor_adaptive | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 1 | fedavg | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 1 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 11 | fedavg | 0 | 0 | 0 | 0 |
| edgeiiot | label_flip | 11 | multi_krum | 0 | 0 | 0 | 0 |
| edgeiiot | none | 1 | fedavg | 0 | 0 | 0 | 0 |
| edgeiiot | none | 1 | multi_krum | 0 | 0 | 0 | 0 |
| forge | backdoor | 1 | fedavg | 20.7 | 20.3 | 96 | 96 |
| forge | backdoor | 1 | multi_krum | 1 | 1 | 1 | 1 |
| forge | backdoor | 11 | fedavg | 0.3 | 1.6 | 99.7 | 35.2 |
| forge | backdoor | 11 | multi_krum | 0.3 | 0.3 | 0.5 | 0.4 |
| forge | backdoor_adaptive | 1 | fedavg | 40 | 41.7 | 48.2 | 46.7 |
| forge | backdoor_adaptive | 1 | multi_krum | 1 | 1 | 1 | 1 |
| forge | backdoor_adaptive | 11 | fedavg | 0.3 | 1.6 | 3.5 | 3.8 |
| forge | backdoor_adaptive | 11 | multi_krum | 0.3 | 0.3 | 0.5 | 0.4 |
| forge | label_flip | 1 | fedavg | 5.5 | 4.4 | 5.8 | 5.8 |
| forge | label_flip | 1 | multi_krum | 0.3 | 0.3 | 0.3 | 0.3 |
| forge | label_flip | 11 | fedavg | 0.3 | 0.3 | 5.3 | 1.6 |
| forge | label_flip | 11 | multi_krum | 0.3 | 0.3 | 0.5 | 0.3 |
| forge | none | 1 | fedavg | 0.3 | 0.3 | 0.3 | 0.3 |
| forge | none | 1 | multi_krum | 0.3 | 0.3 | 0.4 | 0.4 |
| wustl | backdoor | 1 | fedavg | 29.5 | 41.9 | 100 | 98.4 |
| wustl | backdoor | 1 | multi_krum | 34.1 | 34.1 | 34.1 | 34.1 |
| wustl | backdoor | 11 | fedavg | 37.2 | 37.2 | 98.4 | 95.3 |
| wustl | backdoor | 11 | multi_krum | 29.5 | 29.5 | 29.5 | 29.5 |
| wustl | backdoor_adaptive | 1 | fedavg | 87.6 | 86 | 89.1 | 86.8 |
| wustl | backdoor_adaptive | 1 | multi_krum | 46.5 | 46.5 | 46.5 | 46.5 |
| wustl | backdoor_adaptive | 11 | fedavg | 51.2 | 51.2 | 51.2 | 51.2 |
| wustl | backdoor_adaptive | 11 | multi_krum | 29.5 | 29.5 | 29.5 | 29.5 |
| wustl | label_flip | 1 | fedavg | 39.5 | 39.5 | 39.5 | 39.5 |
| wustl | label_flip | 1 | multi_krum | 22.5 | 22.5 | 51.2 | 51.2 |
| wustl | label_flip | 11 | fedavg | 32.6 | 32.6 | 32.6 | 32.6 |
| wustl | label_flip | 11 | multi_krum | 31 | 31 | 31 | 31 |
| wustl | none | 1 | fedavg | 34.9 | 34.9 | 34.9 | 34.9 |
| wustl | none | 1 | multi_krum | 31.8 | 31.8 | 31.8 | 31.8 |


**revocations (full system)**

| dataset | attack | onset | aggregator | runs | attackers | revoked_true | revoked_false | first_true_mean | no_model_rounds |
|---|---|---|---|---|---|---|---|---|---|
| edgeiiot | backdoor | 1 | fedavg | 3 | 6 | 5 | 1 | 8.67 | 0 |
| edgeiiot | backdoor | 1 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| edgeiiot | backdoor | 11 | fedavg | 3 | 6 | 5 | 1 | 13 | 0 |
| edgeiiot | backdoor | 11 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| edgeiiot | backdoor_adaptive | 1 | fedavg | 3 | 6 | 5 | 2 | 8.33 | 0 |
| edgeiiot | backdoor_adaptive | 1 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| edgeiiot | backdoor_adaptive | 11 | fedavg | 3 | 6 | 4 | 1 | 12.67 | 0 |
| edgeiiot | backdoor_adaptive | 11 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| edgeiiot | label_flip | 1 | fedavg | 3 | 6 | 0 | 0 |  | 0 |
| edgeiiot | label_flip | 1 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| edgeiiot | label_flip | 11 | fedavg | 3 | 6 | 0 | 0 |  | 0 |
| edgeiiot | label_flip | 11 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| edgeiiot | none | 1 | fedavg | 3 | 6 | 0 | 0 |  | 0 |
| edgeiiot | none | 1 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| forge | backdoor | 1 | fedavg | 3 | 6 | 5 | 3 | 8.33 | 0 |
| forge | backdoor | 1 | multi_krum | 3 | 6 | 0 | 3 |  | 0 |
| forge | backdoor | 11 | fedavg | 3 | 6 | 2 | 6 | 12 | 0 |
| forge | backdoor | 11 | multi_krum | 3 | 6 | 0 | 7 |  | 0 |
| forge | backdoor_adaptive | 1 | fedavg | 3 | 6 | 3 | 2 | 7.67 | 0 |
| forge | backdoor_adaptive | 1 | multi_krum | 3 | 6 | 0 | 3 |  | 0 |
| forge | backdoor_adaptive | 11 | fedavg | 3 | 6 | 4 | 7 | 12.33 | 0 |
| forge | backdoor_adaptive | 11 | multi_krum | 3 | 6 | 0 | 7 |  | 0 |
| forge | label_flip | 1 | fedavg | 3 | 6 | 2 | 2 | 7 | 0 |
| forge | label_flip | 1 | multi_krum | 3 | 6 | 0 | 6 |  | 0 |
| forge | label_flip | 11 | fedavg | 3 | 6 | 3 | 7 | 13 | 0 |
| forge | label_flip | 11 | multi_krum | 3 | 6 | 0 | 7 |  | 0 |
| forge | none | 1 | fedavg | 3 | 6 | 0 | 0 |  | 0 |
| forge | none | 1 | multi_krum | 3 | 6 | 0 | 2 |  | 0 |
| wustl | backdoor | 1 | fedavg | 3 | 6 | 5 | 0 | 7 | 0 |
| wustl | backdoor | 1 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| wustl | backdoor | 11 | fedavg | 3 | 6 | 5 | 0 | 12.33 | 0 |
| wustl | backdoor | 11 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| wustl | backdoor_adaptive | 1 | fedavg | 3 | 6 | 3 | 0 | 11.67 | 0 |
| wustl | backdoor_adaptive | 1 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| wustl | backdoor_adaptive | 11 | fedavg | 3 | 6 | 0 | 0 |  | 0 |
| wustl | backdoor_adaptive | 11 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| wustl | label_flip | 1 | fedavg | 3 | 6 | 0 | 0 |  | 0 |
| wustl | label_flip | 1 | multi_krum | 3 | 6 | 0 | 0 |  | 8.33 |
| wustl | label_flip | 11 | fedavg | 3 | 6 | 0 | 0 |  | 0 |
| wustl | label_flip | 11 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |
| wustl | none | 1 | fedavg | 3 | 6 | 0 | 0 |  | 0 |
| wustl | none | 1 | multi_krum | 3 | 6 | 0 | 0 |  | 0 |


**gateway, target streams, attack events granted % (full system, deployed head)**

| dataset | attack | onset | aggregator | wrong:monotone/rho1 | wrong:monotone/rho0.2 | wrong:monotone_balanced/rho1 | wrong:monotone_balanced/rho0.2 |
|---|---|---|---|---|---|---|---|
| edgeiiot | backdoor | 1 | fedavg | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | backdoor | 1 | multi_krum | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | backdoor | 11 | fedavg | 0 | 0.03 | 0 | 0.03 |
| edgeiiot | backdoor | 11 | multi_krum | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | backdoor_adaptive | 1 | fedavg | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | backdoor_adaptive | 1 | multi_krum | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | backdoor_adaptive | 11 | fedavg | 0.02 | 0.66 | 0.02 | 0.66 |
| edgeiiot | backdoor_adaptive | 11 | multi_krum | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | label_flip | 1 | fedavg | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | label_flip | 1 | multi_krum | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | label_flip | 11 | fedavg | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | label_flip | 11 | multi_krum | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | none | 1 | fedavg | 0 | 0.01 | 0 | 0.01 |
| edgeiiot | none | 1 | multi_krum | 0 | 0.01 | 0 | 0.01 |
| forge | backdoor | 1 | fedavg | 0.12 | 5.22 | 0.05 | 2.02 |
| forge | backdoor | 1 | multi_krum | 0 | 0.13 | 0 | 0.08 |
| forge | backdoor | 11 | fedavg | 0.01 | 0.16 | 0 | 0.1 |
| forge | backdoor | 11 | multi_krum | 0 | 0.13 | 0 | 0.07 |
| forge | backdoor_adaptive | 1 | fedavg | 11.22 | 16.1 | 0.26 | 12.14 |
| forge | backdoor_adaptive | 1 | multi_krum | 0 | 0.13 | 0 | 0.08 |
| forge | backdoor_adaptive | 11 | fedavg | 0.01 | 0.23 | 0 | 0.12 |
| forge | backdoor_adaptive | 11 | multi_krum | 0 | 0.13 | 0 | 0.07 |
| forge | label_flip | 1 | fedavg | 0.02 | 0.56 | 0.01 | 0.14 |
| forge | label_flip | 1 | multi_krum | 0 | 0.12 | 0 | 0.07 |
| forge | label_flip | 11 | fedavg | 0.01 | 0.18 | 0 | 0.08 |
| forge | label_flip | 11 | multi_krum | 0 | 0.13 | 0 | 0.05 |
| forge | none | 1 | fedavg | 0 | 0.15 | 0 | 0.02 |
| forge | none | 1 | multi_krum | 0 | 0.16 | 0 | 0.08 |
| wustl | backdoor | 1 | fedavg | 0.44 | 9.28 | 0.34 | 7.39 |
| wustl | backdoor | 1 | multi_krum | 0.34 | 6.72 | 0.25 | 4.93 |
| wustl | backdoor | 11 | fedavg | 0.4 | 8.26 | 0.34 | 7.75 |
| wustl | backdoor | 11 | multi_krum | 0.34 | 6.97 | 0.27 | 5.83 |
| wustl | backdoor_adaptive | 1 | fedavg | 2.31 | 49.82 | 0.66 | 25.39 |
| wustl | backdoor_adaptive | 1 | multi_krum | 0.33 | 6.6 | 0.27 | 5.76 |
| wustl | backdoor_adaptive | 11 | fedavg | 1.92 | 50.4 | 0.58 | 21.1 |
| wustl | backdoor_adaptive | 11 | multi_krum | 0.34 | 6.97 | 0.27 | 5.83 |
| wustl | label_flip | 1 | fedavg | 0.37 | 7.65 | 0.31 | 6.71 |
| wustl | label_flip | 1 | multi_krum | 0.35 | 7.04 | 0.24 | 4.44 |
| wustl | label_flip | 11 | fedavg | 0.37 | 7.26 | 0.29 | 6.22 |
| wustl | label_flip | 11 | multi_krum | 0.36 | 7.16 | 0.29 | 6.15 |
| wustl | none | 1 | fedavg | 0.35 | 6.81 | 0.23 | 4.45 |
| wustl | none | 1 | multi_krum | 0.33 | 6.5 | 0.22 | 4.31 |
