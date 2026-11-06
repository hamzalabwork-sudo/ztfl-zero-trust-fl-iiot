# E5d operating curves (15 runs; detector matches E5c: 15/15)

## Equal realised false isolation (<= 1% on test; oracle threshold, analysis only)

| dataset | rho | policy | threshold | false_isolation_rate | wrongful_grant_rate | detection_rate | tti_median | lateral_reach_mean |
|---|---|---|---|---|---|---|---|---|
| edgeiiot | rho0.2 | cusum | 7.36 | 0.27 | 0.00 | 99.40 | 17.60 | 0.00 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 7.36 | 0.27 | 0.00 | 99.40 | 17.60 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.78 | 0.27 | 0.00 | 100.00 | 17.50 | 0.00 |
| edgeiiot | rho0.5 | cusum | 7.56 | 0.38 | 0.00 | 100.00 | 3.80 | 0.00 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 7.56 | 0.38 | 0.00 | 100.00 | 3.80 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.78 | 0.27 | 0.00 | 100.00 | 5.60 | 0.00 |
| edgeiiot | rho1 | cusum | 7.96 | 0.20 | 0.00 | 100.00 | 1.60 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 7.96 | 0.20 | 0.00 | 100.00 | 1.60 | 0.00 |
| edgeiiot | rho1 | ewma | 0.80 | 0.43 | 0.00 | 100.00 | 2.80 | 0.00 |
| forge | rho0.2 | cusum | 6.00 | 0.03 | 5.42 | 87.90 | 8.80 | 3.20 |
| forge | rho0.2 | cusum_sprt_mix | 6.00 | 0.03 | 5.48 | 87.90 | 8.80 | 3.24 |
| forge | rho0.2 | ewma | 0.81 | 0.30 | 3.23 | 97.20 | 14.40 | 1.90 |
| forge | rho0.5 | cusum | 6.00 | 0.03 | 4.90 | 93.30 | 3.00 | 6.94 |
| forge | rho0.5 | cusum_sprt_mix | 6.00 | 0.03 | 4.90 | 93.30 | 3.00 | 6.94 |
| forge | rho0.5 | ewma | 0.82 | 0.55 | 1.98 | 98.70 | 4.60 | 2.85 |
| forge | rho1 | cusum | 6.00 | 0.05 | 3.51 | 94.90 | 1.20 | 9.23 |
| forge | rho1 | cusum_sprt_mix | 6.00 | 0.05 | 3.51 | 94.90 | 1.20 | 9.23 |
| forge | rho1 | ewma | 0.80 | 0.35 | 0.48 | 100.00 | 3.00 | 1.38 |
| wustl | rho0.2 | cusum | 1.30 | 0.00 | 0.16 | 100.00 | 4.20 | 0.09 |
| wustl | rho0.2 | cusum_sprt_mix | 1.30 | 0.00 | 0.16 | 100.00 | 4.20 | 0.09 |
| wustl | rho0.2 | ewma | 0.91 | 0.25 | 0.15 | 100.00 | 4.10 | 0.09 |
| wustl | rho0.5 | cusum | 1.30 | 0.00 | 0.05 | 100.00 | 1.80 | 0.08 |
| wustl | rho0.5 | cusum_sprt_mix | 1.30 | 0.00 | 0.05 | 100.00 | 1.80 | 0.08 |
| wustl | rho0.5 | ewma | 0.91 | 0.30 | 0.05 | 100.00 | 1.80 | 0.07 |
| wustl | rho1 | cusum | 1.30 | 0.00 | 0.03 | 100.00 | 1.00 | 0.09 |
| wustl | rho1 | cusum_sprt_mix | 1.30 | 0.00 | 0.03 | 100.00 | 1.00 | 0.09 |
| wustl | rho1 | ewma | 0.91 | 0.33 | 0.03 | 100.00 | 1.00 | 0.09 |

## per_event: score threshold vs wrongful grants and benign denial

| dataset | rho | threshold | wrongful_grant_rate | benign_denial_rate |
|---|---|---|---|---|
| edgeiiot | rho0.2 | 0.0001 | 0.00 | 74.32 |
| edgeiiot | rho0.2 | 0.001 | 0.00 | 40.36 |
| edgeiiot | rho0.2 | 0.01 | 0.01 | 19.85 |
| edgeiiot | rho0.2 | 0.05 | 0.01 | 0.72 |
| edgeiiot | rho0.2 | 0.1 | 0.01 | 0.71 |
| edgeiiot | rho0.2 | 0.3 | 0.01 | 0.62 |
| edgeiiot | rho0.2 | 0.5 | 0.01 | 0.56 |
| edgeiiot | rho0.5 | 0.0001 | 0.00 | 74.37 |
| edgeiiot | rho0.5 | 0.001 | 0.00 | 40.40 |
| edgeiiot | rho0.5 | 0.01 | 0.00 | 19.89 |
| edgeiiot | rho0.5 | 0.05 | 0.01 | 0.71 |
| edgeiiot | rho0.5 | 0.1 | 0.01 | 0.70 |
| edgeiiot | rho0.5 | 0.3 | 0.01 | 0.61 |
| edgeiiot | rho0.5 | 0.5 | 0.01 | 0.55 |
| edgeiiot | rho1 | 0.0001 | 0.00 | 74.39 |
| edgeiiot | rho1 | 0.001 | 0.00 | 40.38 |
| edgeiiot | rho1 | 0.01 | 0.00 | 19.87 |
| edgeiiot | rho1 | 0.05 | 0.01 | 0.71 |
| edgeiiot | rho1 | 0.1 | 0.01 | 0.71 |
| edgeiiot | rho1 | 0.3 | 0.01 | 0.61 |
| edgeiiot | rho1 | 0.5 | 0.01 | 0.56 |
| forge | rho0.2 | 0.0001 | 0.01 | 65.09 |
| forge | rho0.2 | 0.001 | 0.02 | 17.64 |
| forge | rho0.2 | 0.01 | 0.04 | 2.25 |
| forge | rho0.2 | 0.05 | 0.37 | 1.60 |
| forge | rho0.2 | 0.1 | 0.92 | 1.46 |
| forge | rho0.2 | 0.3 | 4.94 | 0.93 |
| forge | rho0.2 | 0.5 | 6.37 | 0.69 |
| forge | rho0.5 | 0.0001 | 0.01 | 65.10 |
| forge | rho0.5 | 0.001 | 0.03 | 17.60 |
| forge | rho0.5 | 0.01 | 0.05 | 2.26 |
| forge | rho0.5 | 0.05 | 0.46 | 1.61 |
| forge | rho0.5 | 0.1 | 1.11 | 1.46 |
| forge | rho0.5 | 0.3 | 5.91 | 0.94 |
| forge | rho0.5 | 0.5 | 7.62 | 0.70 |
| forge | rho1 | 0.0001 | 0.01 | 65.10 |
| forge | rho1 | 0.001 | 0.03 | 17.72 |
| forge | rho1 | 0.01 | 0.05 | 2.26 |
| forge | rho1 | 0.05 | 0.36 | 1.59 |
| forge | rho1 | 0.1 | 0.93 | 1.45 |
| forge | rho1 | 0.3 | 5.18 | 0.93 |
| forge | rho1 | 0.5 | 6.95 | 0.70 |
| wustl | rho0.2 | 0.0001 | 0.12 | 2.04 |
| wustl | rho0.2 | 0.001 | 0.58 | 0.69 |
| wustl | rho0.2 | 0.01 | 2.64 | 0.18 |
| wustl | rho0.2 | 0.05 | 3.27 | 0.13 |
| wustl | rho0.2 | 0.1 | 3.48 | 0.11 |
| wustl | rho0.2 | 0.3 | 4.63 | 0.08 |
| wustl | rho0.2 | 0.5 | 6.59 | 0.03 |
| wustl | rho0.5 | 0.0001 | 0.09 | 2.04 |
| wustl | rho0.5 | 0.001 | 0.52 | 0.68 |
| wustl | rho0.5 | 0.01 | 2.52 | 0.18 |
| wustl | rho0.5 | 0.05 | 3.14 | 0.12 |
| wustl | rho0.5 | 0.1 | 3.35 | 0.11 |
| wustl | rho0.5 | 0.3 | 4.52 | 0.08 |
| wustl | rho0.5 | 0.5 | 6.37 | 0.03 |
| wustl | rho1 | 0.0001 | 0.08 | 2.05 |
| wustl | rho1 | 0.001 | 0.44 | 0.69 |
| wustl | rho1 | 0.01 | 2.45 | 0.18 |
| wustl | rho1 | 0.05 | 3.13 | 0.12 |
| wustl | rho1 | 0.1 | 3.32 | 0.11 |
| wustl | rho1 | 0.3 | 4.36 | 0.08 |
| wustl | rho1 | 0.5 | 6.15 | 0.03 |

## Full curves (mean over seeds)

| dataset | rho | policy | threshold | false_isolation_rate | detection_rate | tti_median | wrongful_grant_rate | false_reauth_rate |
|---|---|---|---|---|---|---|---|---|
| edgeiiot | rho0.2 | cusum | 0.5 | 92.92 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 1.0 | 92.92 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 1.5 | 86.98 | 100.00 | 0.40 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 2.0 | 86.98 | 100.00 | 0.40 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 3.0 | 86.98 | 100.00 | 0.40 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 4.0 | 71.30 | 100.00 | 1.40 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 5.0 | 16.40 | 100.00 | 4.60 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 6.0 | 2.68 | 100.00 | 5.60 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 7.0 | 0.87 | 100.00 | 21.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 8.0 | 0.78 | 99.80 | 21.50 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 9.0 | 0.33 | 98.90 | 24.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 10.819778284410283 | 0.00 | 98.00 | 26.70 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 13.0 | 0.00 | 90.70 | 41.40 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 16.0 | 0.00 | 78.00 | 83.20 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum | 20.0 | 0.00 | 57.40 | 105.90 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 0.5 | 92.92 | 100.00 | 2.50 | 0.00 | 1.20 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 1.0 | 92.92 | 100.00 | 2.50 | 0.00 | 1.20 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 1.5 | 86.98 | 100.00 | 2.70 | 0.00 | 0.80 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 2.0 | 86.98 | 100.00 | 2.70 | 0.00 | 0.80 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 3.0 | 86.98 | 100.00 | 2.70 | 0.00 | 0.80 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 4.0 | 71.30 | 100.00 | 3.30 | 0.00 | 0.80 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 5.0 | 16.40 | 100.00 | 5.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 6.0 | 2.68 | 100.00 | 5.60 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 7.0 | 0.87 | 100.00 | 21.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 8.0 | 0.78 | 99.80 | 21.50 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 9.0 | 0.33 | 98.90 | 24.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 10.819778284410283 | 0.00 | 98.00 | 26.70 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 13.0 | 0.00 | 90.70 | 41.40 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 16.0 | 0.00 | 78.00 | 83.20 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | cusum_sprt_mix | 20.0 | 0.00 | 57.40 | 105.90 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.2 | 0.00 | 0.00 | - | 0.01 | nan |
| edgeiiot | rho0.2 | ewma | 0.3 | 0.00 | 0.00 | - | 0.01 | nan |
| edgeiiot | rho0.2 | ewma | 0.4 | 0.00 | 1.60 | 122.50 | 0.01 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.5 | 0.00 | 25.90 | 143.60 | 0.01 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.6 | 0.00 | 89.00 | 86.90 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.7 | 0.00 | 100.00 | 32.80 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.8 | 0.50 | 100.00 | 14.20 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.85 | 8.90 | 100.00 | 8.30 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.9 | 71.40 | 100.00 | 1.60 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.93 | 93.42 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.95 | 93.88 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.97 | 95.12 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.98 | 95.35 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.99 | 96.82 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.2 | ewma | 0.995 | 97.85 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 0.5 | 92.25 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 1.0 | 92.25 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 1.5 | 86.50 | 100.00 | 0.40 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 2.0 | 86.50 | 100.00 | 0.40 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 3.0 | 86.50 | 100.00 | 0.40 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 4.0 | 70.12 | 100.00 | 0.60 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 5.0 | 16.40 | 100.00 | 1.80 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 6.0 | 2.85 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 7.0 | 1.10 | 100.00 | 4.20 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 8.0 | 0.97 | 100.00 | 4.20 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 9.0 | 0.25 | 100.00 | 4.70 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 10.819778284410283 | 0.03 | 100.00 | 5.20 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 13.0 | 0.00 | 100.00 | 6.80 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 16.0 | 0.00 | 100.00 | 11.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum | 20.0 | 0.00 | 99.80 | 14.90 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 0.5 | 92.25 | 100.00 | 1.00 | 0.00 | 0.40 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 1.0 | 92.25 | 100.00 | 1.00 | 0.00 | 0.40 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 1.5 | 86.50 | 100.00 | 1.00 | 0.00 | 0.40 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 2.0 | 86.50 | 100.00 | 1.00 | 0.00 | 0.40 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 3.0 | 86.50 | 100.00 | 1.00 | 0.00 | 0.40 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 4.0 | 70.12 | 100.00 | 1.20 | 0.00 | 0.40 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 5.0 | 16.40 | 100.00 | 1.80 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 6.0 | 2.85 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 7.0 | 1.10 | 100.00 | 4.20 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 8.0 | 0.97 | 100.00 | 4.20 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 9.0 | 0.25 | 100.00 | 4.70 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 10.819778284410283 | 0.03 | 100.00 | 5.20 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 13.0 | 0.00 | 100.00 | 6.80 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 16.0 | 0.00 | 100.00 | 11.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | cusum_sprt_mix | 20.0 | 0.00 | 99.80 | 14.90 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.2 | 0.00 | 28.60 | 147.50 | 0.01 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.3 | 0.00 | 93.90 | 79.90 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.4 | 0.00 | 100.00 | 34.60 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.5 | 0.00 | 100.00 | 19.80 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.6 | 0.00 | 100.00 | 12.20 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.7 | 0.00 | 100.00 | 7.80 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.8 | 0.55 | 100.00 | 5.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.85 | 8.83 | 100.00 | 3.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.9 | 69.83 | 100.00 | 0.60 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.93 | 92.70 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.95 | 93.23 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.97 | 94.98 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.98 | 95.10 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.99 | 96.45 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho0.5 | ewma | 0.995 | 97.50 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 0.5 | 92.80 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 1.0 | 92.80 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 1.5 | 86.88 | 100.00 | 0.20 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 2.0 | 86.88 | 100.00 | 0.20 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 3.0 | 86.88 | 100.00 | 0.20 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 4.0 | 70.53 | 100.00 | 0.40 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 5.0 | 17.05 | 100.00 | 1.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 6.0 | 2.95 | 100.00 | 1.20 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 7.0 | 0.92 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 8.0 | 0.85 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 9.0 | 0.22 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 10.819778284410283 | 0.00 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 13.0 | 0.00 | 100.00 | 2.40 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 16.0 | 0.00 | 100.00 | 3.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum | 20.0 | 0.00 | 100.00 | 3.60 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 0.5 | 92.80 | 100.00 | 1.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 1.0 | 92.80 | 100.00 | 1.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 1.5 | 86.88 | 100.00 | 1.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 2.0 | 86.88 | 100.00 | 1.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 3.0 | 86.88 | 100.00 | 1.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 4.0 | 70.53 | 100.00 | 1.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 5.0 | 17.05 | 100.00 | 1.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 6.0 | 2.95 | 100.00 | 1.20 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 7.0 | 0.92 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 8.0 | 0.85 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 9.0 | 0.22 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 10.819778284410283 | 0.00 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 13.0 | 0.00 | 100.00 | 2.40 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 16.0 | 0.00 | 100.00 | 3.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | cusum_sprt_mix | 20.0 | 0.00 | 100.00 | 3.60 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.2 | 0.00 | 100.00 | 16.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.3 | 0.00 | 100.00 | 12.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.4 | 0.00 | 100.00 | 9.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.5 | 0.00 | 100.00 | 7.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.6 | 0.00 | 100.00 | 5.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.7 | 0.00 | 100.00 | 4.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.8 | 0.43 | 100.00 | 2.80 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.85 | 8.92 | 100.00 | 2.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.9 | 70.32 | 100.00 | 0.60 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.93 | 93.15 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.95 | 93.85 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.97 | 95.02 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.98 | 95.40 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.99 | 96.85 | 100.00 | 0.00 | 0.00 | 0.00 |
| edgeiiot | rho1 | ewma | 0.995 | 97.95 | 100.00 | 0.00 | 0.00 | 0.00 |
| forge | rho0.2 | cusum | 0.5 | 58.73 | 97.80 | 1.80 | 2.25 | 0.00 |
| forge | rho0.2 | cusum | 1.0 | 53.42 | 97.60 | 2.10 | 2.25 | 0.00 |
| forge | rho0.2 | cusum | 1.5 | 30.32 | 96.00 | 3.00 | 2.37 | 0.00 |
| forge | rho0.2 | cusum | 2.0 | 24.00 | 95.30 | 3.20 | 2.92 | 0.00 |
| forge | rho0.2 | cusum | 3.0 | 9.38 | 93.90 | 3.80 | 3.73 | 0.00 |
| forge | rho0.2 | cusum | 4.0 | 9.35 | 92.80 | 4.40 | 3.97 | 0.00 |
| forge | rho0.2 | cusum | 5.0 | 5.58 | 91.00 | 5.20 | 4.50 | 0.00 |
| forge | rho0.2 | cusum | 6.0 | 2.73 | 88.00 | 5.70 | 5.20 | 0.00 |
| forge | rho0.2 | cusum | 7.0 | 1.10 | 86.20 | 6.60 | 5.43 | 0.00 |
| forge | rho0.2 | cusum | 8.0 | 0.00 | 84.40 | 21.50 | 5.72 | 0.00 |
| forge | rho0.2 | cusum | 9.0 | 0.00 | 83.80 | 23.70 | 5.79 | 0.00 |
| forge | rho0.2 | cusum | 10.819778284410283 | 0.00 | 80.00 | 26.40 | 6.03 | 0.00 |
| forge | rho0.2 | cusum | 13.0 | 0.00 | 75.30 | 29.50 | 6.12 | 0.00 |
| forge | rho0.2 | cusum | 16.0 | 0.00 | 63.40 | 75.50 | 6.23 | 0.00 |
| forge | rho0.2 | cusum | 20.0 | 0.00 | 53.80 | 82.90 | 6.29 | 0.00 |
| forge | rho0.2 | cusum_sprt_mix | 0.5 | 58.73 | 97.10 | 3.60 | 3.30 | 7.41 |
| forge | rho0.2 | cusum_sprt_mix | 1.0 | 53.42 | 96.70 | 3.60 | 3.30 | 6.93 |
| forge | rho0.2 | cusum_sprt_mix | 1.5 | 30.32 | 95.60 | 4.00 | 3.36 | 5.44 |
| forge | rho0.2 | cusum_sprt_mix | 2.0 | 24.00 | 95.20 | 4.20 | 3.48 | 4.72 |
| forge | rho0.2 | cusum_sprt_mix | 3.0 | 9.38 | 93.80 | 4.60 | 4.04 | 3.53 |
| forge | rho0.2 | cusum_sprt_mix | 4.0 | 9.35 | 92.70 | 4.60 | 4.25 | 3.02 |
| forge | rho0.2 | cusum_sprt_mix | 5.0 | 5.58 | 90.90 | 5.40 | 4.74 | 1.77 |
| forge | rho0.2 | cusum_sprt_mix | 6.0 | 2.73 | 88.00 | 5.70 | 5.26 | 1.02 |
| forge | rho0.2 | cusum_sprt_mix | 7.0 | 1.10 | 86.20 | 6.70 | 5.46 | 0.58 |
| forge | rho0.2 | cusum_sprt_mix | 8.0 | 0.00 | 84.40 | 21.50 | 5.74 | 0.35 |
| forge | rho0.2 | cusum_sprt_mix | 9.0 | 0.00 | 83.80 | 23.70 | 5.81 | 0.35 |
| forge | rho0.2 | cusum_sprt_mix | 10.819778284410283 | 0.00 | 80.00 | 26.40 | 6.06 | 0.25 |
| forge | rho0.2 | cusum_sprt_mix | 13.0 | 0.00 | 75.30 | 29.50 | 6.12 | 0.13 |
| forge | rho0.2 | cusum_sprt_mix | 16.0 | 0.00 | 63.40 | 75.50 | 6.23 | 0.16 |
| forge | rho0.2 | cusum_sprt_mix | 20.0 | 0.00 | 53.80 | 82.90 | 6.29 | 0.00 |
| forge | rho0.2 | ewma | 0.2 | 0.00 | 0.00 | - | 6.37 | nan |
| forge | rho0.2 | ewma | 0.3 | 0.00 | 0.00 | - | 6.37 | nan |
| forge | rho0.2 | ewma | 0.4 | 0.00 | 0.90 | 131.60 | 6.37 | 0.00 |
| forge | rho0.2 | ewma | 0.5 | 0.00 | 21.50 | 140.60 | 6.30 | 0.00 |
| forge | rho0.2 | ewma | 0.6 | 0.00 | 75.50 | 87.80 | 5.85 | 0.00 |
| forge | rho0.2 | ewma | 0.7 | 0.00 | 94.40 | 36.00 | 4.56 | 0.00 |
| forge | rho0.2 | ewma | 0.8 | 0.12 | 96.60 | 15.60 | 3.53 | 0.00 |
| forge | rho0.2 | ewma | 0.85 | 3.62 | 97.50 | 9.00 | 3.00 | 0.00 |
| forge | rho0.2 | ewma | 0.9 | 39.85 | 99.80 | 3.30 | 1.29 | 0.00 |
| forge | rho0.2 | ewma | 0.93 | 81.77 | 100.00 | 0.60 | 0.25 | 0.00 |
| forge | rho0.2 | ewma | 0.95 | 92.30 | 100.00 | 0.20 | 0.13 | 0.00 |
| forge | rho0.2 | ewma | 0.97 | 97.08 | 100.00 | 0.00 | 0.06 | 0.00 |
| forge | rho0.2 | ewma | 0.98 | 99.83 | 100.00 | 0.00 | 0.02 | 0.00 |
| forge | rho0.2 | ewma | 0.99 | 99.98 | 100.00 | 0.00 | 0.01 | 0.00 |
| forge | rho0.2 | ewma | 0.995 | 100.00 | 100.00 | 0.00 | 0.01 | 0.00 |
| forge | rho0.5 | cusum | 0.5 | 59.60 | 96.60 | 0.80 | 3.23 | 0.00 |
| forge | rho0.5 | cusum | 1.0 | 55.00 | 96.60 | 1.00 | 3.23 | 0.00 |
| forge | rho0.5 | cusum | 1.5 | 32.25 | 94.70 | 1.20 | 3.39 | 0.00 |
| forge | rho0.5 | cusum | 2.0 | 25.38 | 94.40 | 1.40 | 3.61 | 0.00 |
| forge | rho0.5 | cusum | 3.0 | 10.15 | 93.90 | 2.00 | 4.05 | 0.00 |
| forge | rho0.5 | cusum | 4.0 | 10.15 | 93.90 | 2.00 | 4.11 | 0.00 |
| forge | rho0.5 | cusum | 5.0 | 5.98 | 93.80 | 2.00 | 4.34 | 0.00 |
| forge | rho0.5 | cusum | 6.0 | 3.20 | 93.50 | 2.20 | 4.75 | 0.00 |
| forge | rho0.5 | cusum | 7.0 | 1.20 | 92.90 | 2.50 | 5.00 | 0.00 |
| forge | rho0.5 | cusum | 8.0 | 0.00 | 92.00 | 5.40 | 5.41 | 0.00 |
| forge | rho0.5 | cusum | 9.0 | 0.00 | 91.10 | 5.80 | 5.73 | 0.00 |
| forge | rho0.5 | cusum | 10.819778284410283 | 0.00 | 86.00 | 6.20 | 6.51 | 0.00 |
| forge | rho0.5 | cusum | 13.0 | 0.00 | 83.60 | 6.80 | 6.79 | 0.00 |
| forge | rho0.5 | cusum | 16.0 | 0.00 | 81.60 | 11.20 | 7.07 | 0.00 |
| forge | rho0.5 | cusum | 20.0 | 0.00 | 80.30 | 13.20 | 7.18 | 0.00 |
| forge | rho0.5 | cusum_sprt_mix | 0.5 | 59.60 | 95.90 | 1.00 | 3.98 | 2.38 |
| forge | rho0.5 | cusum_sprt_mix | 1.0 | 55.00 | 95.80 | 1.00 | 3.98 | 2.28 |
| forge | rho0.5 | cusum_sprt_mix | 1.5 | 32.25 | 94.50 | 1.40 | 4.00 | 0.95 |
| forge | rho0.5 | cusum_sprt_mix | 2.0 | 25.38 | 94.20 | 1.60 | 4.08 | 0.63 |
| forge | rho0.5 | cusum_sprt_mix | 3.0 | 10.15 | 93.80 | 2.00 | 4.24 | 0.32 |
| forge | rho0.5 | cusum_sprt_mix | 4.0 | 10.15 | 93.80 | 2.00 | 4.31 | 0.32 |
| forge | rho0.5 | cusum_sprt_mix | 5.0 | 5.98 | 93.80 | 2.00 | 4.45 | 0.32 |
| forge | rho0.5 | cusum_sprt_mix | 6.0 | 3.20 | 93.50 | 2.40 | 4.77 | 0.11 |
| forge | rho0.5 | cusum_sprt_mix | 7.0 | 1.20 | 92.90 | 2.60 | 5.00 | 0.11 |
| forge | rho0.5 | cusum_sprt_mix | 8.0 | 0.00 | 92.00 | 5.40 | 5.41 | 0.00 |
| forge | rho0.5 | cusum_sprt_mix | 9.0 | 0.00 | 91.10 | 5.80 | 5.73 | 0.00 |
| forge | rho0.5 | cusum_sprt_mix | 10.819778284410283 | 0.00 | 86.00 | 6.20 | 6.51 | 0.00 |
| forge | rho0.5 | cusum_sprt_mix | 13.0 | 0.00 | 83.60 | 6.80 | 6.79 | 0.00 |
| forge | rho0.5 | cusum_sprt_mix | 16.0 | 0.00 | 81.60 | 11.20 | 7.07 | 0.00 |
| forge | rho0.5 | cusum_sprt_mix | 20.0 | 0.00 | 80.30 | 13.20 | 7.18 | 0.00 |
| forge | rho0.5 | ewma | 0.2 | 0.00 | 23.70 | 164.60 | 7.57 | 0.00 |
| forge | rho0.5 | ewma | 0.3 | 0.00 | 76.40 | 83.20 | 7.27 | 0.00 |
| forge | rho0.5 | ewma | 0.4 | 0.00 | 88.80 | 37.30 | 6.42 | 0.00 |
| forge | rho0.5 | ewma | 0.5 | 0.00 | 94.40 | 21.70 | 5.01 | 0.00 |
| forge | rho0.5 | ewma | 0.6 | 0.00 | 95.90 | 13.60 | 4.34 | 0.00 |
| forge | rho0.5 | ewma | 0.7 | 0.00 | 95.90 | 8.60 | 4.13 | 0.00 |
| forge | rho0.5 | ewma | 0.8 | 0.15 | 98.10 | 5.20 | 2.92 | 0.00 |
| forge | rho0.5 | ewma | 0.85 | 3.57 | 99.70 | 3.60 | 1.38 | 0.00 |
| forge | rho0.5 | ewma | 0.9 | 41.57 | 100.00 | 1.20 | 0.29 | 0.00 |
| forge | rho0.5 | ewma | 0.93 | 82.88 | 100.00 | 0.60 | 0.09 | 0.00 |
| forge | rho0.5 | ewma | 0.95 | 92.88 | 100.00 | 0.20 | 0.05 | 0.00 |
| forge | rho0.5 | ewma | 0.97 | 96.80 | 100.00 | 0.00 | 0.02 | 0.00 |
| forge | rho0.5 | ewma | 0.98 | 99.72 | 100.00 | 0.00 | 0.00 | 0.00 |
| forge | rho0.5 | ewma | 0.99 | 99.98 | 100.00 | 0.00 | 0.00 | 0.00 |
| forge | rho0.5 | ewma | 0.995 | 99.98 | 100.00 | 0.00 | 0.00 | 0.00 |
| forge | rho1 | cusum | 0.5 | 59.17 | 96.10 | 0.80 | 2.84 | 0.00 |
| forge | rho1 | cusum | 1.0 | 54.45 | 95.70 | 1.00 | 2.85 | 0.00 |
| forge | rho1 | cusum | 1.5 | 31.05 | 95.50 | 1.00 | 2.88 | 0.00 |
| forge | rho1 | cusum | 2.0 | 24.52 | 95.50 | 1.00 | 2.88 | 0.00 |
| forge | rho1 | cusum | 3.0 | 9.82 | 95.10 | 1.00 | 3.27 | 0.00 |
| forge | rho1 | cusum | 4.0 | 9.82 | 95.10 | 1.00 | 3.28 | 0.00 |
| forge | rho1 | cusum | 5.0 | 5.95 | 95.10 | 1.00 | 3.30 | 0.00 |
| forge | rho1 | cusum | 6.0 | 2.73 | 94.90 | 1.00 | 3.51 | 0.00 |
| forge | rho1 | cusum | 7.0 | 1.00 | 94.90 | 1.40 | 3.51 | 0.00 |
| forge | rho1 | cusum | 8.0 | 0.00 | 94.90 | 2.00 | 3.52 | 0.00 |
| forge | rho1 | cusum | 9.0 | 0.00 | 94.90 | 2.00 | 3.54 | 0.00 |
| forge | rho1 | cusum | 10.819778284410283 | 0.00 | 94.90 | 2.00 | 3.56 | 0.00 |
| forge | rho1 | cusum | 13.0 | 0.00 | 94.90 | 2.20 | 3.60 | 0.00 |
| forge | rho1 | cusum | 16.0 | 0.00 | 94.90 | 3.00 | 3.64 | 0.00 |
| forge | rho1 | cusum | 20.0 | 0.00 | 94.90 | 3.20 | 3.69 | 0.00 |
| forge | rho1 | cusum_sprt_mix | 0.5 | 59.17 | 95.20 | 1.00 | 3.42 | 0.21 |
| forge | rho1 | cusum_sprt_mix | 1.0 | 54.45 | 95.10 | 1.00 | 3.43 | 0.21 |
| forge | rho1 | cusum_sprt_mix | 1.5 | 31.05 | 95.10 | 1.00 | 3.44 | 0.21 |
| forge | rho1 | cusum_sprt_mix | 2.0 | 24.52 | 95.10 | 1.00 | 3.44 | 0.21 |
| forge | rho1 | cusum_sprt_mix | 3.0 | 9.82 | 95.00 | 1.00 | 3.46 | 0.11 |
| forge | rho1 | cusum_sprt_mix | 4.0 | 9.82 | 95.00 | 1.00 | 3.47 | 0.11 |
| forge | rho1 | cusum_sprt_mix | 5.0 | 5.95 | 95.00 | 1.00 | 3.49 | 0.11 |
| forge | rho1 | cusum_sprt_mix | 6.0 | 2.73 | 94.90 | 1.00 | 3.51 | 0.00 |
| forge | rho1 | cusum_sprt_mix | 7.0 | 1.00 | 94.90 | 1.40 | 3.51 | 0.00 |
| forge | rho1 | cusum_sprt_mix | 8.0 | 0.00 | 94.90 | 2.00 | 3.52 | 0.00 |
| forge | rho1 | cusum_sprt_mix | 9.0 | 0.00 | 94.90 | 2.00 | 3.54 | 0.00 |
| forge | rho1 | cusum_sprt_mix | 10.819778284410283 | 0.00 | 94.90 | 2.00 | 3.56 | 0.00 |
| forge | rho1 | cusum_sprt_mix | 13.0 | 0.00 | 94.90 | 2.20 | 3.60 | 0.00 |
| forge | rho1 | cusum_sprt_mix | 16.0 | 0.00 | 94.90 | 3.00 | 3.64 | 0.00 |
| forge | rho1 | cusum_sprt_mix | 20.0 | 0.00 | 94.90 | 3.20 | 3.69 | 0.00 |
| forge | rho1 | ewma | 0.2 | 0.00 | 92.40 | 16.00 | 4.90 | 0.00 |
| forge | rho1 | ewma | 0.3 | 0.00 | 95.90 | 12.00 | 3.85 | 0.00 |
| forge | rho1 | ewma | 0.4 | 0.00 | 96.90 | 9.00 | 3.44 | 0.00 |
| forge | rho1 | ewma | 0.5 | 0.00 | 96.90 | 7.00 | 3.38 | 0.00 |
| forge | rho1 | ewma | 0.6 | 0.00 | 96.90 | 5.00 | 3.34 | 0.00 |
| forge | rho1 | ewma | 0.7 | 0.00 | 97.00 | 4.00 | 3.27 | 0.00 |
| forge | rho1 | ewma | 0.8 | 0.35 | 100.00 | 3.00 | 0.48 | 0.00 |
| forge | rho1 | ewma | 0.85 | 4.32 | 100.00 | 2.00 | 0.16 | 0.00 |
| forge | rho1 | ewma | 0.9 | 40.65 | 100.00 | 1.00 | 0.08 | 0.00 |
| forge | rho1 | ewma | 0.93 | 83.05 | 100.00 | 0.40 | 0.04 | 0.00 |
| forge | rho1 | ewma | 0.95 | 92.55 | 100.00 | 0.40 | 0.02 | 0.00 |
| forge | rho1 | ewma | 0.97 | 97.15 | 100.00 | 0.00 | 0.01 | 0.00 |
| forge | rho1 | ewma | 0.98 | 99.72 | 100.00 | 0.00 | 0.00 | 0.00 |
| forge | rho1 | ewma | 0.99 | 99.98 | 100.00 | 0.00 | 0.00 | 0.00 |
| forge | rho1 | ewma | 0.995 | 99.98 | 100.00 | 0.00 | 0.00 | 0.00 |
| wustl | rho0.2 | cusum | 0.5 | 7.05 | 100.00 | 3.80 | 0.13 | 0.00 |
| wustl | rho0.2 | cusum | 1.0 | 2.68 | 100.00 | 4.00 | 0.14 | 0.00 |
| wustl | rho0.2 | cusum | 1.5 | 0.00 | 100.00 | 4.60 | 0.16 | 0.00 |
| wustl | rho0.2 | cusum | 2.0 | 0.00 | 100.00 | 4.70 | 0.16 | 0.00 |
| wustl | rho0.2 | cusum | 3.0 | 0.00 | 100.00 | 4.70 | 0.17 | 0.00 |
| wustl | rho0.2 | cusum | 4.0 | 0.00 | 100.00 | 4.70 | 0.17 | 0.00 |
| wustl | rho0.2 | cusum | 5.0 | 0.00 | 100.00 | 4.80 | 0.17 | 0.00 |
| wustl | rho0.2 | cusum | 6.0 | 0.00 | 100.00 | 4.80 | 0.18 | 0.00 |
| wustl | rho0.2 | cusum | 7.0 | 0.00 | 100.00 | 5.40 | 0.18 | 0.00 |
| wustl | rho0.2 | cusum | 8.0 | 0.00 | 100.00 | 22.30 | 0.92 | 0.00 |
| wustl | rho0.2 | cusum | 9.0 | 0.00 | 100.00 | 23.50 | 0.97 | 0.00 |
| wustl | rho0.2 | cusum | 10.819778284410283 | 0.00 | 99.10 | 29.80 | 1.42 | 0.00 |
| wustl | rho0.2 | cusum | 13.0 | 0.00 | 98.70 | 34.70 | 1.53 | 0.00 |
| wustl | rho0.2 | cusum | 16.0 | 0.00 | 81.70 | 80.40 | 3.79 | 0.00 |
| wustl | rho0.2 | cusum | 20.0 | 0.00 | 63.80 | 91.40 | 4.98 | 0.00 |
| wustl | rho0.2 | cusum_sprt_mix | 0.5 | 7.05 | 100.00 | 3.80 | 0.14 | 0.20 |
| wustl | rho0.2 | cusum_sprt_mix | 1.0 | 2.68 | 100.00 | 4.00 | 0.14 | 0.10 |
| wustl | rho0.2 | cusum_sprt_mix | 1.5 | 0.00 | 100.00 | 4.60 | 0.16 | 0.10 |
| wustl | rho0.2 | cusum_sprt_mix | 2.0 | 0.00 | 100.00 | 4.70 | 0.16 | 0.10 |
| wustl | rho0.2 | cusum_sprt_mix | 3.0 | 0.00 | 100.00 | 4.70 | 0.17 | 0.10 |
| wustl | rho0.2 | cusum_sprt_mix | 4.0 | 0.00 | 100.00 | 4.70 | 0.17 | 0.10 |
| wustl | rho0.2 | cusum_sprt_mix | 5.0 | 0.00 | 100.00 | 4.80 | 0.17 | 0.10 |
| wustl | rho0.2 | cusum_sprt_mix | 6.0 | 0.00 | 100.00 | 4.80 | 0.18 | 0.10 |
| wustl | rho0.2 | cusum_sprt_mix | 7.0 | 0.00 | 100.00 | 5.40 | 0.18 | 0.10 |
| wustl | rho0.2 | cusum_sprt_mix | 8.0 | 0.00 | 100.00 | 22.30 | 0.94 | 0.30 |
| wustl | rho0.2 | cusum_sprt_mix | 9.0 | 0.00 | 100.00 | 23.50 | 0.99 | 0.30 |
| wustl | rho0.2 | cusum_sprt_mix | 10.819778284410283 | 0.00 | 99.10 | 29.80 | 1.43 | 0.20 |
| wustl | rho0.2 | cusum_sprt_mix | 13.0 | 0.00 | 98.70 | 34.70 | 1.54 | 0.10 |
| wustl | rho0.2 | cusum_sprt_mix | 16.0 | 0.00 | 81.70 | 80.40 | 3.79 | 0.00 |
| wustl | rho0.2 | cusum_sprt_mix | 20.0 | 0.00 | 63.80 | 91.40 | 4.98 | 0.00 |
| wustl | rho0.2 | ewma | 0.2 | 0.00 | 0.00 | - | 6.59 | nan |
| wustl | rho0.2 | ewma | 0.3 | 0.00 | 0.00 | - | 6.59 | nan |
| wustl | rho0.2 | ewma | 0.4 | 0.00 | 0.80 | 114.62 | 6.59 | 0.00 |
| wustl | rho0.2 | ewma | 0.5 | 0.00 | 16.30 | 147.10 | 6.37 | 0.00 |
| wustl | rho0.2 | ewma | 0.6 | 0.00 | 74.10 | 101.60 | 4.52 | 0.00 |
| wustl | rho0.2 | ewma | 0.7 | 0.00 | 99.30 | 40.40 | 1.73 | 0.00 |
| wustl | rho0.2 | ewma | 0.8 | 0.00 | 100.00 | 16.30 | 0.55 | 0.00 |
| wustl | rho0.2 | ewma | 0.85 | 0.00 | 100.00 | 10.00 | 0.33 | 0.00 |
| wustl | rho0.2 | ewma | 0.9 | 0.22 | 100.00 | 4.40 | 0.16 | 0.00 |
| wustl | rho0.2 | ewma | 0.93 | 6.20 | 100.00 | 4.00 | 0.14 | 0.00 |
| wustl | rho0.2 | ewma | 0.95 | 11.88 | 100.00 | 3.60 | 0.13 | 0.00 |
| wustl | rho0.2 | ewma | 0.97 | 31.40 | 100.00 | 2.80 | 0.11 | 0.00 |
| wustl | rho0.2 | ewma | 0.98 | 34.67 | 100.00 | 2.80 | 0.10 | 0.00 |
| wustl | rho0.2 | ewma | 0.99 | 42.65 | 100.00 | 2.80 | 0.10 | 0.00 |
| wustl | rho0.2 | ewma | 0.995 | 46.17 | 100.00 | 2.70 | 0.09 | 0.00 |
| wustl | rho0.5 | cusum | 0.5 | 6.90 | 100.00 | 1.40 | 0.04 | 0.00 |
| wustl | rho0.5 | cusum | 1.0 | 2.63 | 100.00 | 1.40 | 0.05 | 0.00 |
| wustl | rho0.5 | cusum | 1.5 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum | 2.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum | 3.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum | 4.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum | 5.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum | 6.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum | 7.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum | 8.0 | 0.00 | 100.00 | 4.60 | 0.14 | 0.00 |
| wustl | rho0.5 | cusum | 9.0 | 0.00 | 100.00 | 4.80 | 0.15 | 0.00 |
| wustl | rho0.5 | cusum | 10.819778284410283 | 0.00 | 100.00 | 5.60 | 0.20 | 0.00 |
| wustl | rho0.5 | cusum | 13.0 | 0.00 | 100.00 | 6.30 | 0.22 | 0.00 |
| wustl | rho0.5 | cusum | 16.0 | 0.00 | 100.00 | 10.90 | 0.41 | 0.00 |
| wustl | rho0.5 | cusum | 20.0 | 0.00 | 100.00 | 13.00 | 0.59 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 0.5 | 6.90 | 100.00 | 1.40 | 0.04 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 1.0 | 2.63 | 100.00 | 1.40 | 0.05 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 1.5 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 2.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 3.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 4.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 5.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 6.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 7.0 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 8.0 | 0.00 | 100.00 | 4.60 | 0.14 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 9.0 | 0.00 | 100.00 | 4.80 | 0.15 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 10.819778284410283 | 0.00 | 100.00 | 5.60 | 0.20 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 13.0 | 0.00 | 100.00 | 6.30 | 0.22 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 16.0 | 0.00 | 100.00 | 10.90 | 0.41 | 0.00 |
| wustl | rho0.5 | cusum_sprt_mix | 20.0 | 0.00 | 100.00 | 13.00 | 0.59 | 0.00 |
| wustl | rho0.5 | ewma | 0.2 | 0.00 | 17.50 | 154.70 | 6.23 | 0.00 |
| wustl | rho0.5 | ewma | 0.3 | 0.00 | 73.70 | 94.90 | 4.71 | 0.00 |
| wustl | rho0.5 | ewma | 0.4 | 0.00 | 98.60 | 45.20 | 1.85 | 0.00 |
| wustl | rho0.5 | ewma | 0.5 | 0.00 | 100.00 | 23.50 | 0.79 | 0.00 |
| wustl | rho0.5 | ewma | 0.6 | 0.00 | 100.00 | 14.20 | 0.42 | 0.00 |
| wustl | rho0.5 | ewma | 0.7 | 0.00 | 100.00 | 9.00 | 0.25 | 0.00 |
| wustl | rho0.5 | ewma | 0.8 | 0.00 | 100.00 | 5.60 | 0.13 | 0.00 |
| wustl | rho0.5 | ewma | 0.85 | 0.00 | 100.00 | 3.60 | 0.09 | 0.00 |
| wustl | rho0.5 | ewma | 0.9 | 0.23 | 100.00 | 2.00 | 0.05 | 0.00 |
| wustl | rho0.5 | ewma | 0.93 | 6.60 | 100.00 | 1.40 | 0.05 | 0.00 |
| wustl | rho0.5 | ewma | 0.95 | 12.15 | 100.00 | 1.40 | 0.04 | 0.00 |
| wustl | rho0.5 | ewma | 0.97 | 30.65 | 100.00 | 1.00 | 0.04 | 0.00 |
| wustl | rho0.5 | ewma | 0.98 | 33.80 | 100.00 | 1.00 | 0.04 | 0.00 |
| wustl | rho0.5 | ewma | 0.99 | 41.15 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho0.5 | ewma | 0.995 | 44.55 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum | 0.5 | 7.75 | 100.00 | 1.00 | 0.02 | 0.00 |
| wustl | rho1 | cusum | 1.0 | 2.90 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum | 1.5 | 0.00 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum | 2.0 | 0.00 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum | 3.0 | 0.00 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum | 4.0 | 0.00 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum | 5.0 | 0.00 | 100.00 | 1.00 | 0.04 | 0.00 |
| wustl | rho1 | cusum | 6.0 | 0.00 | 100.00 | 1.00 | 0.04 | 0.00 |
| wustl | rho1 | cusum | 7.0 | 0.00 | 100.00 | 1.00 | 0.04 | 0.00 |
| wustl | rho1 | cusum | 8.0 | 0.00 | 100.00 | 2.00 | 0.05 | 0.00 |
| wustl | rho1 | cusum | 9.0 | 0.00 | 100.00 | 2.00 | 0.05 | 0.00 |
| wustl | rho1 | cusum | 10.819778284410283 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho1 | cusum | 13.0 | 0.00 | 100.00 | 2.20 | 0.06 | 0.00 |
| wustl | rho1 | cusum | 16.0 | 0.00 | 100.00 | 3.00 | 0.08 | 0.00 |
| wustl | rho1 | cusum | 20.0 | 0.00 | 100.00 | 3.40 | 0.09 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 0.5 | 7.75 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 1.0 | 2.90 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 1.5 | 0.00 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 2.0 | 0.00 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 3.0 | 0.00 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 4.0 | 0.00 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 5.0 | 0.00 | 100.00 | 1.00 | 0.04 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 6.0 | 0.00 | 100.00 | 1.00 | 0.04 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 7.0 | 0.00 | 100.00 | 1.00 | 0.04 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 8.0 | 0.00 | 100.00 | 2.00 | 0.05 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 9.0 | 0.00 | 100.00 | 2.00 | 0.05 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 10.819778284410283 | 0.00 | 100.00 | 2.00 | 0.06 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 13.0 | 0.00 | 100.00 | 2.20 | 0.06 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 16.0 | 0.00 | 100.00 | 3.00 | 0.08 | 0.00 |
| wustl | rho1 | cusum_sprt_mix | 20.0 | 0.00 | 100.00 | 3.40 | 0.09 | 0.00 |
| wustl | rho1 | ewma | 0.2 | 0.00 | 100.00 | 16.60 | 0.55 | 0.00 |
| wustl | rho1 | ewma | 0.3 | 0.00 | 100.00 | 12.20 | 0.34 | 0.00 |
| wustl | rho1 | ewma | 0.4 | 0.00 | 100.00 | 9.00 | 0.23 | 0.00 |
| wustl | rho1 | ewma | 0.5 | 0.00 | 100.00 | 7.00 | 0.17 | 0.00 |
| wustl | rho1 | ewma | 0.6 | 0.00 | 100.00 | 5.00 | 0.12 | 0.00 |
| wustl | rho1 | ewma | 0.7 | 0.00 | 100.00 | 4.00 | 0.09 | 0.00 |
| wustl | rho1 | ewma | 0.8 | 0.00 | 100.00 | 3.00 | 0.07 | 0.00 |
| wustl | rho1 | ewma | 0.85 | 0.00 | 100.00 | 2.00 | 0.05 | 0.00 |
| wustl | rho1 | ewma | 0.9 | 0.33 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | ewma | 0.93 | 6.70 | 100.00 | 1.00 | 0.03 | 0.00 |
| wustl | rho1 | ewma | 0.95 | 12.10 | 100.00 | 1.00 | 0.02 | 0.00 |
| wustl | rho1 | ewma | 0.97 | 30.77 | 100.00 | 1.00 | 0.02 | 0.00 |
| wustl | rho1 | ewma | 0.98 | 34.12 | 100.00 | 1.00 | 0.02 | 0.00 |
| wustl | rho1 | ewma | 0.99 | 40.73 | 100.00 | 1.00 | 0.02 | 0.00 |
| wustl | rho1 | ewma | 0.995 | 43.90 | 100.00 | 1.00 | 0.02 | 0.00 |

## Per attack type (cusum_sprt_mix at Lorden's h; per_event at 0.5)

| dataset | attack_type | rho | device_isolated_rate:cusum_sprt_mix | device_isolated_rate:per_event | wrongful_grant_rate:cusum_sprt_mix | wrongful_grant_rate:per_event | event_detect_rate | llr_nonpositive_share |
|---|---|---|---|---|---|---|---|---|
| edgeiiot | Backdoor | rho0.2 | 100.00 | 0.00 | 0.00 | 0.10 | 99.94 | 0.06 |
| edgeiiot | Backdoor | rho1 | 100.00 | 0.00 | 0.00 | 0.07 | 99.94 | 0.06 |
| edgeiiot | DDoS_HTTP | rho0.2 | 98.46 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | DDoS_HTTP | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | DDoS_ICMP | rho0.2 | 88.61 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | DDoS_ICMP | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | DDoS_TCP | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | DDoS_TCP | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | Fingerprinting | rho0.2 | 93.70 | 0.00 | 0.00 | 0.00 | 100.00 | 0.80 |
| edgeiiot | Fingerprinting | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.80 |
| edgeiiot | Password | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | Password | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | Port_Scanning | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | Port_Scanning | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | Ransomware | rho0.2 | 100.00 | 0.00 | 0.00 | 0.02 | 99.96 | 0.04 |
| edgeiiot | Ransomware | rho1 | 100.00 | 0.00 | 0.00 | 0.04 | 99.96 | 0.04 |
| edgeiiot | SQL_injection | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | SQL_injection | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | Uploading | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | Uploading | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | Vulnerability_scanner | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.01 |
| edgeiiot | Vulnerability_scanner | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.01 |
| edgeiiot | XSS | rho0.2 | 99.05 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| edgeiiot | XSS | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| forge | ddos_mp | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| forge | ddos_mp | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| forge | ddos_tcp | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 99.99 | 0.01 |
| forge | ddos_tcp | rho1 | 100.00 | 0.00 | 0.00 | 0.02 | 99.99 | 0.01 |
| forge | dos_deauth | rho0.2 | 1.33 | 0.00 | 24.85 | 24.95 | 73.46 | 39.78 |
| forge | dos_deauth | rho1 | 100.00 | 0.00 | 1.38 | 26.71 | 73.46 | 39.78 |
| forge | dos_icmp | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.01 |
| forge | dos_icmp | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.01 |
| forge | dos_ipv4 | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 99.99 | 0.01 |
| forge | dos_ipv4 | rho1 | 100.00 | 0.00 | 0.00 | 0.02 | 99.99 | 0.01 |
| forge | dos_land | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| forge | dos_land | rho1 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| forge | dos_udp | rho0.2 | 100.00 | 0.00 | 0.00 | 0.02 | 99.99 | 0.01 |
| forge | dos_udp | rho1 | 100.00 | 0.00 | 0.00 | 0.01 | 99.99 | 0.01 |
| forge | malw_back | rho0.2 | 83.50 | 0.00 | 0.59 | 1.25 | 98.76 | 3.00 |
| forge | malw_back | rho1 | 100.00 | 0.00 | 0.01 | 1.52 | 98.76 | 3.00 |
| forge | mitm_arp | rho0.2 | 3.16 | 0.00 | 13.22 | 13.46 | 85.87 | 24.96 |
| forge | mitm_arp | rho1 | 100.00 | 0.00 | 0.48 | 14.23 | 85.87 | 24.96 |
| forge | mitm_dhcp | rho0.2 | 0.00 | 0.00 | 61.79 | 61.79 | 38.18 | 98.18 |
| forge | mitm_dhcp | rho1 | 0.00 | 0.00 | 62.08 | 62.08 | 38.18 | 98.18 |
| forge | mitm_ndp | rho0.2 | 92.06 | 0.00 | 0.74 | 1.80 | 98.37 | 2.84 |
| forge | mitm_ndp | rho1 | 100.00 | 0.00 | 0.01 | 1.66 | 98.37 | 2.84 |
| forge | os_finger | rho0.2 | 100.00 | 0.00 | 0.04 | 0.27 | 99.84 | 0.28 |
| forge | os_finger | rho1 | 100.00 | 0.00 | 0.00 | 0.22 | 99.84 | 0.28 |
| forge | port_scan | rho0.2 | 100.00 | 0.00 | 0.00 | 0.09 | 99.87 | 0.13 |
| forge | port_scan | rho1 | 100.00 | 0.00 | 0.00 | 0.07 | 99.87 | 0.13 |
| forge | sybil | rho0.2 | 92.60 | 0.00 | 1.05 | 3.96 | 96.21 | 6.47 |
| forge | sybil | rho1 | 100.00 | 0.00 | 0.06 | 3.79 | 96.21 | 6.47 |
| forge | vuln_scan | rho0.2 | 100.00 | 0.00 | 0.02 | 0.13 | 99.84 | 0.17 |
| forge | vuln_scan | rho1 | 100.00 | 0.00 | 0.00 | 0.15 | 99.84 | 0.17 |
| forge | wild_card | rho0.2 | 92.94 | 0.00 | 0.15 | 0.36 | 99.49 | 0.74 |
| forge | wild_card | rho1 | 100.00 | 0.00 | 0.01 | 0.49 | 99.49 | 0.74 |
| wustl | Backdoor | rho0.2 | 96.81 | 0.00 | 3.80 | 15.06 | 85.12 | 15.81 |
| wustl | Backdoor | rho1 | 100.00 | 0.00 | 0.17 | 15.11 | 85.12 | 15.81 |
| wustl | CommInj | rho0.2 | 100.00 | 0.00 | 1.51 | 9.62 | 90.38 | 9.62 |
| wustl | CommInj | rho1 | 100.00 | 0.00 | 0.08 | 9.49 | 90.38 | 9.62 |
| wustl | DoS | rho0.2 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |
| wustl | DoS | rho1 | 100.00 | 0.00 | 0.00 | 0.01 | 100.00 | 0.00 |
| wustl | Reconn | rho0.2 | 100.00 | 0.00 | 0.00 | 0.06 | 99.94 | 0.06 |
| wustl | Reconn | rho1 | 100.00 | 0.00 | 0.00 | 0.07 | 99.94 | 0.06 |
