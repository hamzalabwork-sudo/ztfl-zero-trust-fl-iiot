# Audit: edgeiiot

- rows 157,800, feature columns 61, binary {0: 24301, 1: 133499}
- duplicate rows 0.5%; distinct feature rows 156,986, of which 0 carry both labels
- identifier-like columns: frame.time, ip.src_host, ip.dst_host, icmp.checksum, icmp.seq_le, icmp.transmit_timestamp, http.file_data, http.request.uri.query, http.request.full_uri, http.tls_port, tcp.ack_raw, tcp.checksum, tcp.dstport, tcp.payload, tcp.seq, tcp.srcport, udp.port, udp.stream, udp.time_delta, dns.qry.name, dns.qry.name.len, mqtt.msg, mqtt.topic, mbtcp.trans_id
- constant columns: icmp.unused, http.tls_port, dns.qry.type, dns.retransmit_request_in, mqtt.msg_decoded_as, mbtcp.len, mbtcp.trans_id, mbtcp.unit_id
- suspected single-feature shortcuts (macro-F1 >= 0.95): frame.time, dns.qry.name.len, mqtt.conack.flags, mqtt.msg, mqtt.protoname, mqtt.topic
- spelling variants: ip.dst_host, arp.dst.proto_ipv4, arp.src.proto_ipv4, http.file_data, http.request.uri.query, http.request.method, http.referer, http.request.full_uri, http.request.version, tcp.options, tcp.payload, tcp.srcport, dns.qry.name.len, mqtt.conack.flags, mqtt.msg, mqtt.protoname, mqtt.topic
- stream readiness: {"distinct_sources": 19090, "benign_sources_with_100plus_rows": 3, "top_benign_sources": {"192.168.0.128": 10125, "192.168.0.101": 9971, "0": 4190, "192.168.0.1": 7, "0.0.0.0": 4, "143.107.229.210": 1, "85.254.217.5": 1, "197.84.150.123": 1, "160.119.193.252": 1}, "top_attack_sources": {"192.168.0.128": 62421, "192.168.0.170": 47688, "0": 3801, "0.0.0.0": 204, "192.168.0.101": 155, "192.168.0.152": 120, "172.217.19.42": 17, "104.16.87.20": 7, "142.250.200.205": 5, "172.217.19.35": 2}, "sources_in_both_labels": 5, "time_numeric_share": 0.0077, "time_distinct": 2, "time_range": [0.0, 6.0], "time_monotonic_in_file": false}

## Classes

| type | rows |
|---|---|
| Normal | 24,301 |
| DDoS_UDP | 14,498 |
| DDoS_ICMP | 14,090 |
| Ransomware | 10,925 |
| DDoS_HTTP | 10,561 |
| SQL_injection | 10,311 |
| Uploading | 10,269 |
| DDoS_TCP | 10,247 |
| Backdoor | 10,195 |
| Vulnerability_scanner | 10,076 |
| Port_Scanning | 10,071 |
| XSS | 10,052 |
| Password | 9,989 |
| MITM | 1,214 |
| Fingerprinting | 1,001 |

## Top 25 single-feature macro-F1

| column | macro-F1 |
|---|---|
| frame.time | 1.0 |
| dns.qry.name.len | 1.0 |
| mqtt.conack.flags | 1.0 |
| mqtt.msg | 1.0 |
| mqtt.protoname | 1.0 |
| mqtt.topic | 1.0 |
| tcp.options | 0.9371 |
| tcp.srcport | 0.9252 |
| tcp.seq | 0.8662 |
| tcp.dstport | 0.8546 |
| tcp.ack | 0.8193 |
| ip.src_host | 0.8053 |
| ip.dst_host | 0.7728 |
| tcp.payload | 0.7204 |
| tcp.len | 0.6889 |
| mqtt.hdrflags | 0.6439 |
| mqtt.msgtype | 0.6439 |
| mqtt.len | 0.6054 |
| tcp.flags | 0.593 |
| tcp.ack_raw | 0.5626 |
| mqtt.conflag.cleansess | 0.5114 |
| mqtt.conflags | 0.5114 |
| mqtt.proto_len | 0.5114 |
| mqtt.ver | 0.5114 |
| mqtt.topic_len | 0.5097 |
