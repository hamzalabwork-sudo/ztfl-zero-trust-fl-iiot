# Audit: wustl

- rows 1,194,464, feature columns 47, binary {0: 1107448, 1: 87016}
- duplicate rows 0.0%; distinct feature rows 1,194,464, of which 0 carry both labels
- identifier-like columns: StartTime, LastTime, SrcAddr, DstAddr, Sport, Dport, IdleTime, sIpId, dIpId, RunTime
- constant columns: none
- suspected single-feature shortcuts (macro-F1 >= 0.95): SrcAddr, sTtl, SAppBytes, TotAppByte, SrcBytes, TotBytes, TotPkts, SrcPkts
- spelling variants: none
- stream readiness: {"distinct_sources": 14, "benign_sources_with_100plus_rows": 8, "top_benign_sources": {"192.168.0.20": 1090547, "192.168.0.44": 8317, "192.168.0.2": 4360, "01:80:c2:00:00:0e": 2529, "0.0.0.0": 573, "0": 423, "fe80::e9ed:931f:c2e0:1333": 354, "fe80::9bc:3b2b:78d3:855c": 321, "fe80::dacb:8aff:fe08:ed2a": 16, "192.168.0.4": 8}, "top_attack_sources": {"209.240.235.92": 46615, "192.168.0.10": 26797, "20.1.249.77": 7220, "49.48.134.64": 6320, "192.168.0.2": 37, "192.168.0.20": 27}, "sources_in_both_labels": 2, "time_numeric_share": 0.0, "time_distinct": 0}

## Classes

| type | rows |
|---|---|
| normal | 1,107,448 |
| DoS | 78,305 |
| Reconn | 8,240 |
| CommInj | 259 |
| Backdoor | 212 |

## Top 25 single-feature macro-F1

| column | macro-F1 |
|---|---|
| SrcAddr | 0.9998 |
| sTtl | 0.9918 |
| SAppBytes | 0.9738 |
| TotAppByte | 0.9738 |
| SrcBytes | 0.9594 |
| TotBytes | 0.9573 |
| TotPkts | 0.9519 |
| SrcPkts | 0.9502 |
| SIntPkt | 0.9385 |
| Sport | 0.937 |
| Load | 0.9339 |
| DstBytes | 0.9333 |
| DIntPkt | 0.9329 |
| DstPkts | 0.9328 |
| DstJitter | 0.932 |
| DAppBytes | 0.932 |
| SrcLoad | 0.9314 |
| Dport | 0.9302 |
| DstRate | 0.9286 |
| DstLoad | 0.9282 |
| Dur | 0.9265 |
| Rate | 0.9255 |
| Sum | 0.9255 |
| Min | 0.9255 |
| Max | 0.9255 |
