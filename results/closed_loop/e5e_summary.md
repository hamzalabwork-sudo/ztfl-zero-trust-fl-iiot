# E5e: evidence-model variants vs E5d (monotone), 15 runs per mode

## cusum_sprt_mix at Lorden's h = 10.82 (mean over seeds)

| dataset | rho | llr | false_isolation_rate | wrongful_grant_rate | detection_rate | tti_median |
|---|---|---|---|---|---|---|
| edgeiiot | rho0.2 | monotone | 0.00 | 0.00 | 98.00 | 26.70 |
| edgeiiot | rho0.2 | monotone_balanced | 0.00 | 0.00 | 98.00 | 26.50 |
| edgeiiot | rho0.2 | monotone_floor | 0.00 | 0.00 | 98.00 | 26.70 |
| edgeiiot | rho0.5 | monotone | 0.03 | 0.00 | 100.00 | 5.20 |
| edgeiiot | rho0.5 | monotone_balanced | 0.03 | 0.00 | 100.00 | 5.20 |
| edgeiiot | rho0.5 | monotone_floor | 0.03 | 0.00 | 100.00 | 5.20 |
| edgeiiot | rho1 | monotone | 0.00 | 0.00 | 100.00 | 2.00 |
| edgeiiot | rho1 | monotone_balanced | 0.00 | 0.00 | 100.00 | 2.00 |
| edgeiiot | rho1 | monotone_floor | 0.00 | 0.00 | 100.00 | 2.00 |
| forge | rho0.2 | monotone | 0.00 | 6.06 | 80.00 | 26.40 |
| forge | rho0.2 | monotone_balanced | 0.00 | 4.88 | 89.30 | 25.10 |
| forge | rho0.2 | monotone_floor | 0.00 | 6.06 | 80.10 | 26.50 |
| forge | rho0.5 | monotone | 0.00 | 6.51 | 86.00 | 6.20 |
| forge | rho0.5 | monotone_balanced | 0.00 | 1.76 | 99.60 | 5.90 |
| forge | rho0.5 | monotone_floor | 0.00 | 6.49 | 86.50 | 6.20 |
| forge | rho1 | monotone | 0.00 | 3.56 | 94.90 | 2.00 |
| forge | rho1 | monotone_balanced | 0.00 | 0.10 | 100.00 | 2.00 |
| forge | rho1 | monotone_floor | 0.00 | 3.56 | 94.90 | 2.00 |
| wustl | rho0.2 | monotone | 0.00 | 1.43 | 99.10 | 29.80 |
| wustl | rho0.2 | monotone_balanced | 0.00 | 1.37 | 99.50 | 29.10 |
| wustl | rho0.2 | monotone_floor | 0.00 | 1.43 | 99.10 | 29.80 |
| wustl | rho0.5 | monotone | 0.00 | 0.20 | 100.00 | 5.60 |
| wustl | rho0.5 | monotone_balanced | 0.00 | 0.18 | 100.00 | 5.40 |
| wustl | rho0.5 | monotone_floor | 0.00 | 0.20 | 100.00 | 5.60 |
| wustl | rho1 | monotone | 0.00 | 0.06 | 100.00 | 2.00 |
| wustl | rho1 | monotone_balanced | 0.00 | 0.06 | 100.00 | 2.00 |
| wustl | rho1 | monotone_floor | 0.00 | 0.06 | 100.00 | 2.00 |

## Worst seed: false isolation at Lorden's h

| dataset | rho | llr | false_isolation_max |
|---|---|---|---|
| edgeiiot | rho0.2 | monotone | 0.00 |
| edgeiiot | rho0.2 | monotone_balanced | 0.00 |
| edgeiiot | rho0.2 | monotone_floor | 0.00 |
| edgeiiot | rho0.5 | monotone | 0.12 |
| edgeiiot | rho0.5 | monotone_balanced | 0.12 |
| edgeiiot | rho0.5 | monotone_floor | 0.12 |
| edgeiiot | rho1 | monotone | 0.00 |
| edgeiiot | rho1 | monotone_balanced | 0.00 |
| edgeiiot | rho1 | monotone_floor | 0.00 |
| forge | rho0.2 | monotone | 0.00 |
| forge | rho0.2 | monotone_balanced | 0.00 |
| forge | rho0.2 | monotone_floor | 0.00 |
| forge | rho0.5 | monotone | 0.00 |
| forge | rho0.5 | monotone_balanced | 0.00 |
| forge | rho0.5 | monotone_floor | 0.00 |
| forge | rho1 | monotone | 0.00 |
| forge | rho1 | monotone_balanced | 0.00 |
| forge | rho1 | monotone_floor | 0.00 |
| wustl | rho0.2 | monotone | 0.00 |
| wustl | rho0.2 | monotone_balanced | 0.00 |
| wustl | rho0.2 | monotone_floor | 0.00 |
| wustl | rho0.5 | monotone | 0.00 |
| wustl | rho0.5 | monotone_balanced | 0.00 |
| wustl | rho0.5 | monotone_floor | 0.00 |
| wustl | rho1 | monotone | 0.00 |
| wustl | rho1 | monotone_balanced | 0.00 |
| wustl | rho1 | monotone_floor | 0.00 |

## Equal realised false isolation <= 1% (oracle threshold, analysis only), cusum_sprt_mix

| dataset | rho | llr | false_isolation_rate | wrongful_grant_rate | detection_rate | tti_median |
|---|---|---|---|---|---|---|
| edgeiiot | rho0.2 | monotone | 0.27 | 0.00 | 99.40 | 17.60 |
| edgeiiot | rho0.2 | monotone_balanced | 0.27 | 0.00 | 99.40 | 17.60 |
| edgeiiot | rho0.2 | monotone_floor | 0.27 | 0.00 | 99.40 | 17.60 |
| edgeiiot | rho0.5 | monotone | 0.38 | 0.00 | 100.00 | 3.80 |
| edgeiiot | rho0.5 | monotone_balanced | 0.38 | 0.00 | 100.00 | 4.40 |
| edgeiiot | rho0.5 | monotone_floor | 0.38 | 0.00 | 100.00 | 3.80 |
| edgeiiot | rho1 | monotone | 0.20 | 0.00 | 100.00 | 1.60 |
| edgeiiot | rho1 | monotone_balanced | 0.20 | 0.00 | 100.00 | 1.80 |
| edgeiiot | rho1 | monotone_floor | 0.20 | 0.00 | 100.00 | 1.60 |
| forge | rho0.2 | monotone | 0.03 | 5.48 | 87.90 | 8.80 |
| forge | rho0.2 | monotone_balanced | 0.43 | 3.37 | 96.50 | 16.40 |
| forge | rho0.2 | monotone_floor | 0.03 | 5.46 | 88.00 | 8.80 |
| forge | rho0.5 | monotone | 0.03 | 4.90 | 93.30 | 3.00 |
| forge | rho0.5 | monotone_balanced | 0.62 | 0.54 | 100.00 | 3.20 |
| forge | rho0.5 | monotone_floor | 0.03 | 4.89 | 93.30 | 3.00 |
| forge | rho1 | monotone | 0.05 | 3.51 | 94.90 | 1.20 |
| forge | rho1 | monotone_balanced | 0.62 | 0.07 | 100.00 | 1.60 |
| forge | rho1 | monotone_floor | 0.05 | 3.51 | 94.90 | 1.20 |
| wustl | rho0.2 | monotone | 0.00 | 0.16 | 100.00 | 4.20 |
| wustl | rho0.2 | monotone_balanced | 0.20 | 0.16 | 100.00 | 4.70 |
| wustl | rho0.2 | monotone_floor | 0.00 | 0.16 | 100.00 | 4.20 |
| wustl | rho0.5 | monotone | 0.00 | 0.05 | 100.00 | 1.80 |
| wustl | rho0.5 | monotone_balanced | 0.05 | 0.06 | 100.00 | 2.00 |
| wustl | rho0.5 | monotone_floor | 0.00 | 0.05 | 100.00 | 1.80 |
| wustl | rho1 | monotone | 0.00 | 0.03 | 100.00 | 1.00 |
| wustl | rho1 | monotone_balanced | 0.10 | 0.03 | 100.00 | 1.00 |
| wustl | rho1 | monotone_floor | 0.00 | 0.03 | 100.00 | 1.00 |

## Per attack type: share of compromised devices isolated at Lorden's h

| dataset | attack_type | rho | monotone | monotone_balanced | monotone_floor |
|---|---|---|---|---|---|
| edgeiiot | Backdoor | rho0.2 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Backdoor | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | DDoS_HTTP | rho0.2 | 98.46 | 98.46 | 98.46 |
| edgeiiot | DDoS_HTTP | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | DDoS_ICMP | rho0.2 | 88.61 | 88.61 | 88.61 |
| edgeiiot | DDoS_ICMP | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | DDoS_TCP | rho0.2 | 100.00 | 100.00 | 100.00 |
| edgeiiot | DDoS_TCP | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Fingerprinting | rho0.2 | 93.70 | 93.70 | 93.70 |
| edgeiiot | Fingerprinting | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Password | rho0.2 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Password | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Port_Scanning | rho0.2 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Port_Scanning | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Ransomware | rho0.2 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Ransomware | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | SQL_injection | rho0.2 | 100.00 | 100.00 | 100.00 |
| edgeiiot | SQL_injection | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Uploading | rho0.2 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Uploading | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Vulnerability_scanner | rho0.2 | 100.00 | 100.00 | 100.00 |
| edgeiiot | Vulnerability_scanner | rho1 | 100.00 | 100.00 | 100.00 |
| edgeiiot | XSS | rho0.2 | 99.05 | 99.05 | 99.05 |
| edgeiiot | XSS | rho1 | 100.00 | 100.00 | 100.00 |
| forge | ddos_mp | rho0.2 | 100.00 | 100.00 | 100.00 |
| forge | ddos_mp | rho1 | 100.00 | 100.00 | 100.00 |
| forge | ddos_tcp | rho0.2 | 100.00 | 100.00 | 100.00 |
| forge | ddos_tcp | rho1 | 100.00 | 100.00 | 100.00 |
| forge | dos_deauth | rho0.2 | 1.33 | 49.21 | 2.67 |
| forge | dos_deauth | rho1 | 100.00 | 100.00 | 100.00 |
| forge | dos_icmp | rho0.2 | 100.00 | 100.00 | 100.00 |
| forge | dos_icmp | rho1 | 100.00 | 100.00 | 100.00 |
| forge | dos_ipv4 | rho0.2 | 100.00 | 100.00 | 100.00 |
| forge | dos_ipv4 | rho1 | 100.00 | 100.00 | 100.00 |
| forge | dos_land | rho0.2 | 100.00 | 100.00 | 100.00 |
| forge | dos_land | rho1 | 100.00 | 100.00 | 100.00 |
| forge | dos_udp | rho0.2 | 100.00 | 100.00 | 100.00 |
| forge | dos_udp | rho1 | 100.00 | 100.00 | 100.00 |
| forge | malw_back | rho0.2 | 83.50 | 100.00 | 83.50 |
| forge | malw_back | rho1 | 100.00 | 100.00 | 100.00 |
| forge | mitm_arp | rho0.2 | 3.16 | 74.10 | 3.16 |
| forge | mitm_arp | rho1 | 100.00 | 100.00 | 100.00 |
| forge | mitm_dhcp | rho0.2 | 0.00 | 5.42 | 0.00 |
| forge | mitm_dhcp | rho1 | 0.00 | 100.00 | 0.00 |
| forge | mitm_ndp | rho0.2 | 92.06 | 97.78 | 92.06 |
| forge | mitm_ndp | rho1 | 100.00 | 100.00 | 100.00 |
| forge | os_finger | rho0.2 | 100.00 | 100.00 | 100.00 |
| forge | os_finger | rho1 | 100.00 | 100.00 | 100.00 |
| forge | port_scan | rho0.2 | 100.00 | 100.00 | 100.00 |
| forge | port_scan | rho1 | 100.00 | 100.00 | 100.00 |
| forge | sybil | rho0.2 | 92.60 | 97.50 | 92.60 |
| forge | sybil | rho1 | 100.00 | 100.00 | 100.00 |
| forge | vuln_scan | rho0.2 | 100.00 | 100.00 | 100.00 |
| forge | vuln_scan | rho1 | 100.00 | 100.00 | 100.00 |
| forge | wild_card | rho0.2 | 92.94 | 100.00 | 92.94 |
| forge | wild_card | rho1 | 100.00 | 100.00 | 100.00 |
| wustl | Backdoor | rho0.2 | 96.81 | 98.17 | 96.81 |
| wustl | Backdoor | rho1 | 100.00 | 100.00 | 100.00 |
| wustl | CommInj | rho0.2 | 100.00 | 100.00 | 100.00 |
| wustl | CommInj | rho1 | 100.00 | 100.00 | 100.00 |
| wustl | DoS | rho0.2 | 100.00 | 100.00 | 100.00 |
| wustl | DoS | rho1 | 100.00 | 100.00 | 100.00 |
| wustl | Reconn | rho0.2 | 100.00 | 100.00 | 100.00 |
| wustl | Reconn | rho1 | 100.00 | 100.00 | 100.00 |

## Per attack type: attack events granted at Lorden's h

| dataset | attack_type | rho | monotone | monotone_balanced | monotone_floor |
|---|---|---|---|---|---|
| edgeiiot | Backdoor | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Backdoor | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | DDoS_HTTP | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | DDoS_HTTP | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | DDoS_ICMP | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | DDoS_ICMP | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | DDoS_TCP | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | DDoS_TCP | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Fingerprinting | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Fingerprinting | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Password | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Password | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Port_Scanning | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Port_Scanning | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Ransomware | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Ransomware | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | SQL_injection | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | SQL_injection | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Uploading | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Uploading | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Vulnerability_scanner | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | Vulnerability_scanner | rho1 | 0.00 | 0.00 | 0.00 |
| edgeiiot | XSS | rho0.2 | 0.00 | 0.00 | 0.00 |
| edgeiiot | XSS | rho1 | 0.00 | 0.00 | 0.00 |
| forge | ddos_mp | rho0.2 | 0.00 | 0.00 | 0.00 |
| forge | ddos_mp | rho1 | 0.00 | 0.00 | 0.00 |
| forge | ddos_tcp | rho0.2 | 0.00 | 0.00 | 0.00 |
| forge | ddos_tcp | rho1 | 0.00 | 0.00 | 0.00 |
| forge | dos_deauth | rho0.2 | 24.85 | 15.55 | 24.85 |
| forge | dos_deauth | rho1 | 1.38 | 0.29 | 1.30 |
| forge | dos_icmp | rho0.2 | 0.00 | 0.00 | 0.00 |
| forge | dos_icmp | rho1 | 0.00 | 0.00 | 0.00 |
| forge | dos_ipv4 | rho0.2 | 0.00 | 0.00 | 0.00 |
| forge | dos_ipv4 | rho1 | 0.00 | 0.00 | 0.00 |
| forge | dos_land | rho0.2 | 0.00 | 0.00 | 0.00 |
| forge | dos_land | rho1 | 0.00 | 0.00 | 0.00 |
| forge | dos_udp | rho0.2 | 0.00 | 0.00 | 0.00 |
| forge | dos_udp | rho1 | 0.00 | 0.00 | 0.00 |
| forge | malw_back | rho0.2 | 0.59 | 0.35 | 0.59 |
| forge | malw_back | rho1 | 0.01 | 0.01 | 0.01 |
| forge | mitm_arp | rho0.2 | 13.22 | 6.31 | 13.22 |
| forge | mitm_arp | rho1 | 0.48 | 0.18 | 0.48 |
| forge | mitm_dhcp | rho0.2 | 61.79 | 60.32 | 61.79 |
| forge | mitm_dhcp | rho1 | 62.08 | 1.19 | 62.08 |
| forge | mitm_ndp | rho0.2 | 0.74 | 0.35 | 0.74 |
| forge | mitm_ndp | rho1 | 0.01 | 0.00 | 0.01 |
| forge | os_finger | rho0.2 | 0.04 | 0.00 | 0.04 |
| forge | os_finger | rho1 | 0.00 | 0.00 | 0.00 |
| forge | port_scan | rho0.2 | 0.00 | 0.00 | 0.00 |
| forge | port_scan | rho1 | 0.00 | 0.00 | 0.00 |
| forge | sybil | rho0.2 | 1.05 | 0.89 | 1.05 |
| forge | sybil | rho1 | 0.06 | 0.06 | 0.06 |
| forge | vuln_scan | rho0.2 | 0.02 | 0.02 | 0.02 |
| forge | vuln_scan | rho1 | 0.00 | 0.00 | 0.00 |
| forge | wild_card | rho0.2 | 0.15 | 0.11 | 0.15 |
| forge | wild_card | rho1 | 0.01 | 0.01 | 0.01 |
| wustl | Backdoor | rho0.2 | 3.80 | 3.62 | 3.80 |
| wustl | Backdoor | rho1 | 0.17 | 0.16 | 0.17 |
| wustl | CommInj | rho0.2 | 1.51 | 1.48 | 1.51 |
| wustl | CommInj | rho1 | 0.08 | 0.07 | 0.08 |
| wustl | DoS | rho0.2 | 0.00 | 0.00 | 0.00 |
| wustl | DoS | rho1 | 0.00 | 0.00 | 0.00 |
| wustl | Reconn | rho0.2 | 0.00 | 0.00 | 0.00 |
| wustl | Reconn | rho1 | 0.00 | 0.00 | 0.00 |
