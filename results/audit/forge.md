# Audit: forge

- rows 1,022,786, feature columns 94, binary {0: 176100, 1: 846686}
- duplicate rows 0.0%; distinct feature rows 1,022,786, of which 0 carry both labels
- identifier-like columns: arp.duplicate-address-detected, arp.seconds-since-duplicate-address-frame, eth:ethertype:ip, eth:ethertype:ip:icmp, eth:ethertype:ip:tcp, eth:ethertype:ip:tcp:mqtt, eth:ethertype:ip:udp, eth:ethertype:ip:udp:mdns, frame.number, frame.time_delta, frame.time_epoch, icmp.checksum, icmp.checksum.status, icmpv6.checksum, icmpv6.checksum.status, ip.checksum, ip.checksum.status, ip.dsfield.dscp, ip.flags.df, ip.hdr_len, ip.len, ip.proto, ip.ttl, ip.ttl.lncb, ip.version, tcp.checksum, tcp.checksum.status, tcp.stream, tcp.time_delta, udp.checksum, udp.checksum.status, udp.stream, udp.time_delta
- constant columns: none
- suspected single-feature shortcuts (macro-F1 >= 0.95): tcp.hdr_len, tcp.option_kind, tcp.option_len, tcp.completeness, ip.len, frame.len, tcp.window_size, tcp.stream, tcp.time_delta
- spelling variants: none
- stream readiness: {"distinct_sources": null, "time_numeric_share": 1.0, "time_distinct": 1022619, "time_range": [1688551865.191814, 1729091637.202703], "time_monotonic_in_file": false}

## Classes

| type | rows |
|---|---|
| normal | 176,100 |
| ddos_mp | 99,885 |
| dos_icmp | 99,793 |
| dos_ipv4 | 99,731 |
| dos_udp | 99,724 |
| port_scan | 99,480 |
| dos_land | 99,268 |
| ddos_tcp | 98,955 |
| vuln_scan | 97,556 |
| os_finger | 23,870 |
| mitm_ndp | 10,462 |
| wild_card | 9,959 |
| mitm_arp | 2,093 |
| sybil | 2,084 |
| malw_back | 1,933 |
| dos_deauth | 1,835 |
| mitm_dhcp | 58 |

## Top 25 single-feature macro-F1

| column | macro-F1 |
|---|---|
| tcp.hdr_len | 0.9886 |
| tcp.option_kind | 0.9886 |
| tcp.option_len | 0.9886 |
| tcp.completeness | 0.9882 |
| ip.len | 0.9759 |
| frame.len | 0.9728 |
| tcp.window_size | 0.9543 |
| tcp.stream | 0.9533 |
| tcp.time_delta | 0.9523 |
| tcp.window_size_scalefactor | 0.8255 |
| ·······A···· | 0.8057 |
| tcp.analysis.bytes_in_flight | 0.798 |
| tcp.pdu.size | 0.7963 |
| mqtt.topic_len | 0.795 |
| mqtt.len | 0.7945 |
| tcp.analysis.push_bytes_sent | 0.7931 |
| tcp.analysis.ack_rtt | 0.7927 |
| tcp.len | 0.7906 |
| mqtt.msgtype | 0.7854 |
| eth:ethertype:ip:tcp:mqtt | 0.7848 |
| ·······AP··· | 0.7845 |
| tcp.flags.push | 0.7844 |
| frame.time_epoch | 0.7352 |
| tcp.analysis.acks_frame | 0.7184 |
| frame.time_delta | 0.7153 |
