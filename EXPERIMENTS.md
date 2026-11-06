# Experiment log (manuscript record)

Every simulation in this project, in order, including negative and superseded results. Each entry:
question, configuration, code version, where the raw results are, numbers, finding, decision.
Pre-registered protocols are the primary results; later fixes are separate, labelled variants and
never overwrite them. All per-run JSON files carry `code_version` (sha256 of `src/*.py`, 12 hex),
`prep_version`, torch version and host.

Common setup (E1 onward unless stated): a Linux GPU server (NVIDIA RTX 3090; one GPU per run),
PyTorch, seeds 42-46, data prepared by `src/datasets.py` PREP_VERSION 1.

---

## E0 -- Dataset audit (Stage 0)

**Question.** Are the public IIoT datasets free of label shortcuts, and can they support
per-device Zero-Trust experiments (device identity + time order)?

**Method.** `src/audit_datasets.py`. All columns read as strings, so spellings are preserved.
For every column: (a) single-feature shortcut test: a depth-3 decision tree on that column alone,
300k sampled rows, 30% holdout; flagged if macro-F1 >= 0.95. (b) Spelling variants: the same
number written differently, e.g. '0' vs '0.0'. (c) Identifier-like columns. (d) Constant columns.
(e) Stream readiness: distinct sources, benign sources with 100+ rows, timestamp usability.
Results: `results/audit/<dataset>.{json,md}`.

**Findings.**

| dataset | rows | benign / attack | shortcut columns (single-feature macro-F1 >= 0.95) | per-device ZT tests possible? |
|---|---|---|---|---|
| Edge-IIoTSet (ML CSV) | 157,800 | 24,301 / 133,499 | frame.time, dns.qry.name.len, mqtt.conack.flags, mqtt.msg, mqtt.protoname, mqtt.topic (all 1.0, through '0' (benign) vs '0.0' (attack) spellings) | No: benign comes from 2 hosts (.128, .101); .128 is also the top attack source; frame.time is unusable (0.8% numeric) |
| Forge-IIoT | 1,022,786 | 176,100 / 846,686 | tcp.hdr_len, tcp.option_kind, tcp.option_len (0.989), tcp.completeness (0.988), ip.len, frame.len, tcp.window_size, tcp.stream, tcp.time_delta | No: no address columns |
| WUSTL-IIoT-2021 | 1,194,464 | 1,107,448 / 87,016 | SrcAddr (0.9998), sTtl (0.992), byte/packet counts (0.95-0.97) | No: 98% of benign rows come from one host |

**Decision.** (1) Clean the features with the rules in E1-prep. (2) The Zero-Trust closed loop
cannot rely on these datasets, so it uses semi-synthetic device streams (Stage 2) and then an
emulated device testbed with real identity and timing (Stage 4).

## E1-prep -- Cleaning rules (PREP_VERSION 1, fixed 2026-11-03)

- **Parsing.** One canonical numeric parser (plain numbers and hex; anything else is non-numeric).
  This removes the spelling leak: '0' and '0.0' become the same value.
- **Edge-IIoTSet.**
  - Drop identifier and payload columns: timestamps, IPs, URIs, payloads, MQTT message/topic,
    stream ids, checksums, raw sequence and ack numbers, transaction id, UDP port.
  - Raw TCP ports become a fixed IANA service-port category.
  - Drop classes DDoS_UDP and MITM (malformed rows).
- **Forge-IIoT.** Drop frame number/time, stream ids and checksums.
- **WUSTL-IIoT-2021.** Drop start/end time, addresses and IP ids. Ports become the service-port
  category.
- **Fingerprint ablation (Forge, WUSTL).** `keep` keeps the host-fingerprint columns; `nofp`
  drops them. Forge fingerprint columns: TTL, DSCP, DF, TCP header length and options, MSS,
  window size and scale. WUSTL: sTtl, dTtl, sTos.
- **Rows.** Cap 50,000 rows per traffic type. Stratified random split 70/10/20 by traffic type.
- **Scaling.** Signed log1p, then a z-score fitted on train, clipped to +-10. This scaling is
  federated-exact: clients can share sums and squared sums.
- **Unseen-pattern check.** A test row is "unseen" if its cleaned feature pattern never occurs in
  train.

| setting | features | rows (train / val / test) | unseen test rows (seed 42) |
|---|---|---|---|
| edgeiiot / keep | 40 | 99,461 / 14,209 / 28,418 | 8,597 |
| forge / keep | 84 | 351,605 / 50,230 / 100,459 | 30,524 |
| forge / nofp | 74 | same rows | 29,488 |
| wustl / keep | 53 | 76,097 / 10,871 / 21,743 | 17,689 |
| wustl / nofp | 50 | same rows | 16,596 |

After cleaning, the strongest single features are behavioural, not shortcuts: Edge
service_port_mqtt 0.94; Forge (nofp) tcp.completeness 0.975; WUSTL byte counts about 0.99.

---

## E1 -- Centralized detector zoo (Stage 1a), 2026-11-03/04

**Question.** How do all standalone deep models compare on the cleaned data? The zoo is reported
in full so that no "why not model X" remains.

**Config.** `src/train_central.py`.
- Models: MLP, CNN-1D, LSTM, GRU, BiLSTM, TCN, Transformer (feature tokenizer), Autoencoder
  (benign-only, threshold = 99th percentile of benign validation error). HistGradientBoosting is
  the non-deep reference.
- Training: AdamW, cosine lr 1e-3 -> 1e-4, batch 512, 30 epochs, inverse-frequency class weights.
- Selection and timing: the checkpoint with the best validation macro-F1 is kept. CPU latency is
  measured on 1 thread, single row, median of 300 calls.
- Scale: 5 settings x 9 models x 5 seeds = **225 runs**.
- code_version: 1866f1483728. The smoke runs (edgeiiot s42) used b22035b8ae76; the only
  difference was a fix to the `last_epoch_val` field.

Results: `results/central/summary.md`, per-run JSON files in `results/central/<ds>/<mode>/`.

**Numbers** (test macro-F1, mean over 5 seeds; std <= 0.002 everywhere):

| model | edge | forge keep | forge nofp | wustl keep | wustl nofp | params | CPU ms |
|---|---|---|---|---|---|---|---|
| MLP | 0.9983 | 0.9891 | 0.9889 | 0.9995 | 0.9995 | 13.6-19.3k | 0.05 |
| CNN-1D | 0.9981 | **0.9938** | **0.9939** | 0.9994 | 0.9992 | 6.5k | 0.11 |
| LSTM | 0.9981 | 0.9914 | 0.9912 | 0.9988 | 0.9985 | 17.3k | 0.32 |
| GRU | 0.9968 | 0.9907 | 0.9914 | 0.9989 | 0.9985 | 13.0k | 0.9-1.9 |
| BiLSTM | 0.9981 | 0.9904 | 0.9896 | 0.9988 | 0.9989 | 34.6k | 0.5-0.6 |
| TCN | 0.9982 | 0.9920 | 0.9931 | 0.9994 | 0.9991 | 15.8k | 0.5-0.6 |
| Transformer | 0.9983 | 0.9905 | 0.9896 | 0.9995 | 0.9995 | 19.8-22.6k | 0.6 |
| Autoencoder | 0.9963 | 0.9869 | 0.9838 | 0.9953 | 0.9949 | 7-13k | 0.08 |
| HGB (ref.) | 0.9984 | 0.9888 | 0.9887 | 0.9998 | 0.9998 | -- | 1.2-2.1 |

**Findings.**
1. The models are statistically tied within each dataset (spread <= 0.005, AE excepted). Public
   IIoT detection is saturated after cleaning.
2. Removing the fingerprint columns costs nothing (Forge 0.9938 -> 0.9939; WUSTL unchanged).
3. Unseen-pattern test F1 is >= 0.99, so the scores are not memorisation.
4. Edge benign flag rate is about 0.53% for every model. This is the dataset's label-noise floor
   (identical packets carry both labels).
5. Edge cost varies about 35x (MLP 0.05 ms vs GRU up to 1.9 ms) while accuracy does not.

**Decision.** Accuracy alone cannot select the detector. Selection moves to federated behaviour
and edge cost (E2).

## E2 -- Federated detector zoo (Stage 1b), 2026-11-04

**Question.** Which models keep their accuracy when trained federated on non-IID clients?

**Config.** `src/train_fed.py`.
- Federation: in-process FedAvg (same maths as Flower; Flower is used for deployment). K = 10
  clients. Each traffic type is split over the clients by Dirichlet(alpha = 0.5) proportions.
- Training: 30 rounds x 1 local epoch, which is the same 30 data passes as E1. Clients use
  AdamW, fresh each round, with the server's cosine lr. Class weights come from the summed
  client counts. Aggregation is weighted by client rows, clients in fixed order (deterministic).
- Validation: the server holds the validation split. It picks the best round and sets the AE
  threshold (q99).
- Reported: best-val round, last round, and the mean over the last 5 rounds.
- Scale: 8 models x 5 settings x 5 seeds = **200 runs**. HGB is not federatable with FedAvg; its
  E1 result is the reference.
- code_version: ecc4db47cad9.

Results: `results/fed/a0.5_k10/summary.md` (includes the centralized column).

**Client heterogeneity** (edge, s42): client benign share ranges from 0.1% to 59%; client size
from 4.9k to 16.1k rows.

**Numbers** (test macro-F1 at the best-val round, mean +- std over 5 seeds):

| model | edge | forge keep | forge nofp | wustl keep | wustl nofp | FL gap vs E1 |
|---|---|---|---|---|---|---|
| MLP | 0.9982 +- .0002 | 0.9918 +- .0030 | 0.9908 +- .0025 | 0.9993 +- .0002 | 0.9993 +- .0002 | none (Forge +0.002) |
| Transformer | 0.9982 +- .0002 | **0.9929 +- .0003** | **0.9918 +- .0009** | 0.9992 +- .0003 | **0.9994 +- .0002** | none (Forge +0.002) |
| BiLSTM | 0.9978 +- .0006 | 0.9893 +- .0023 | 0.9909 +- .0014 | 0.9943 +- .0021 | 0.9947 +- .0017 | <= 0.0045 |
| TCN | 0.9961 +- .0006 | 0.9888 +- .0035 | 0.9905 +- .0024 | 0.9935 +- .0011 | 0.9914 +- .0035 | 0.002-0.008 |
| CNN-1D | 0.9960 +- .0007 | 0.9890 +- .0024 | 0.9872 +- .0040 | 0.9950 +- .0020 | 0.9931 +- .0032 | 0.002-0.007 |
| GRU | 0.9895 +- .0135 | 0.9900 +- .0019 | 0.9886 +- .0034 | 0.9927 +- .0039 | 0.9930 +- .0035 | 0.0007-0.007, unstable |
| LSTM | 0.9860 +- .0151 | 0.9835 +- .0124 | 0.9889 +- .0033 | 0.9927 +- .0038 | 0.9929 +- .0038 | 0.002-0.012, unstable |
| Autoencoder (q99) | 0.8656 +- .1835 | 0.3200 +- .2468 | 0.4259 +- .3637 | 0.9867 +- .0164 | 0.9952 +- .0005 | collapses on Forge and Edge |

Benign flag rate (test): MLP 0.02-0.8%; CNN on WUSTL rises from 0.07% (E1) to 0.9-1.4%; LSTM on
Edge reaches 3.7 +- 4.7%. Last-5-round mean: LSTM on WUSTL keep falls to 0.975 +- 0.042 (single-round
dips), while MLP and Transformer stay within 0.001 of their best round.

**Findings.**
1. Only MLP and Transformer show no federated gap. They rank first and second on validation in all
   5 settings.
2. CNN-1D is the centralized front-runner on Forge but loses up to 0.007 under FL and its benign
   false alarms grow by 10-20x on WUSTL.
3. Recurrent models (LSTM, GRU) are seed-unstable under non-IID FedAvg. Example: Edge s42 LSTM
   sits at macro-F1 0.75 for rounds 4-15.
4. The federated autoencoder keeps its ranking quality (ROC-AUC 0.98-0.99 on Forge vs 0.996
   centralized), but recall at the q99 threshold collapses to 0.08-0.85. This is a
   threshold-calibration failure, not a representation failure. Hypothesis (not yet verified):
   benign data is concentrated on a few clients, so the aggregated model's benign-error tail
   widens. A separate variant is tested in E4.
5. PR-AUC is not informative here because attacks are the majority class; ROC-AUC and macro-F1
   are reported instead.

**Decision (proposed 2026-11-04).** Primary detector MLP: no FL gap, lowest CPU cost (0.05 ms).
Second: Transformer (equal accuracy, about 10x the cost). This follows the pre-fixed rule: choose on
validation, and within ties prefer the cheaper model. It is confirmed only after E3.

## E3 -- Non-IID severity ablation (done 2026-11-04)

**Question.** Does the MLP and Transformer no-gap result hold from near-IID to extreme non-IID
splits?

**Config.** As E2, with alpha in {0.1 (extreme), 100 (near-IID)}. Models: MLP, Transformer, CNN,
LSTM. 5 settings x 5 seeds, so 200 runs.
- Partition check (seed 42): with alpha 0.1, most clients hold 0% benign. Edge: 6 of 10 clients;
  Forge: 6 of 10 at 0% and one at 92.5%. With alpha 100 every client holds about the global mix.
- Queue: `scripts/stage1c_queue.sh`, log `logs/stage1c.log`.

Results: `results/fed/a0.1_k10/summary.md`, `results/fed/a100_k10/summary.md`. All 200 runs
finished with no errors (log `logs/stage1c.log`). The alpha 0.5 column is E2.

**Numbers** (test macro-F1 at the best-val round, mean +- std over 5 seeds; nofp settings for Forge
and WUSTL are in the summary files and show the same pattern):

| dataset | model | alpha 0.1 | alpha 0.5 (E2) | alpha 100 | benign flagged %, alpha 0.1 | centralized (E1) |
|---|---|---|---|---|---|---|
| Edge | MLP | 0.9982 +- .0002 | 0.9982 +- .0002 | 0.9982 +- .0002 | 0.57 | 0.9983 |
| Edge | Transformer | 0.9982 +- .0003 | 0.9982 +- .0002 | 0.9982 +- .0002 | 0.56 | 0.9983 |
| Edge | CNN-1D | **0.6706 +- .2977** | 0.9960 +- .0007 | 0.9961 +- .0008 | **60.2** | 0.9981 |
| Edge | LSTM | **0.6890 +- .2030** | 0.9860 +- .0151 | 0.9955 +- .0009 | **63.2** | 0.9981 |
| Forge keep | MLP | 0.9926 +- .0017 | 0.9918 +- .0030 | 0.9880 +- .0007 | 1.18 | 0.9891 |
| Forge keep | Transformer | 0.9933 +- .0007 | 0.9929 +- .0003 | 0.9929 +- .0002 | 1.44 | 0.9905 |
| Forge keep | CNN-1D | 0.9503 +- .0860 | 0.9890 +- .0024 | 0.9861 +- .0007 | 12.8 | 0.9938 |
| Forge keep | LSTM | 0.8837 +- .2005 | 0.9835 +- .0124 | 0.9855 +- .0031 | 20.0 | 0.9914 |
| WUSTL keep | MLP | 0.9987 +- .0004 | 0.9993 +- .0002 | 0.9994 +- .0001 | 0.03 | 0.9995 |
| WUSTL keep | Transformer | 0.9988 +- .0004 | 0.9992 +- .0003 | 0.9992 +- .0002 | 0.03 | 0.9995 |
| WUSTL keep | CNN-1D | 0.9873 +- .0101 | 0.9950 +- .0020 | 0.9940 +- .0005 | 1.31 | 0.9994 |
| WUSTL keep | LSTM | 0.9911 +- .0041 | 0.9927 +- .0038 | 0.9951 +- .0016 | 1.13 | 0.9988 |

Last-5-round mean at alpha 0.1: MLP and Transformer stay within 0.003 of their best round; LSTM on
WUSTL falls to 0.940 +- 0.070.

**Findings.**
1. **MLP and Transformer are insensitive to non-IID severity.** From near-IID (alpha 100) to
   extreme (alpha 0.1, most clients hold no benign traffic), they move by <= 0.0046 macro-F1 and
   stay at or above centralized on Forge.
2. **CNN-1D and LSTM collapse under extreme non-IID.** On Edge at alpha 0.1, macro-F1 falls to
   0.67-0.69 and 60-63% of benign rows are flagged; Forge shows the same at 13-20% benign flagged.
   At alpha 100 their gap to centralized shrinks to 0.002-0.008, so the E2 gap is caused by
   heterogeneity, not by FedAvg itself.
3. With alpha 100, MLP on Forge is slightly lower than at alpha 0.1 (0.9880 vs 0.9926). This is
   within the range of Forge's seed-to-seed spread in E1/E2 and is not interpreted.

**Decision (confirmed 2026-11-04).** Primary detector MLP, second Transformer, as proposed in E2.

## E4 -- Federated autoencoder with a validation-optimal threshold (done 2026-11-04)

**Question.** Is the E2 autoencoder collapse fixed by choosing the threshold on validation
macro-F1 instead of the pre-registered q99?

**Config.** As E2, autoencoder only, `--ae-threshold valopt`. The threshold maximises server-side
validation macro-F1 over 199 score quantiles; it uses the labelled validation split, which the
server already holds. Scale: 25 runs.

Results: `results/fed/a0.5_k10_aevalopt/summary.md`. This is reported as a variant next to E2;
E2 stays the primary result.

| setting | E2 q99 test macro-F1 | E4 valopt test macro-F1 | E4 benign flagged % | centralized (E1) |
|---|---|---|---|---|
| edgeiiot / keep | 0.8656 +- 0.1835 | 0.9727 +- 0.0468 | 8.08 +- 13.42 (s46: 31.7) | 0.9963 |
| forge / keep | 0.3200 +- 0.2468 | 0.9857 +- 0.0005 | 2.38 +- 0.20 | 0.9869 |
| forge / nofp | 0.4259 +- 0.3637 | 0.9848 +- 0.0017 | 3.49 +- 1.13 | 0.9838 |
| wustl / keep | 0.9867 +- 0.0164 | 0.9951 +- 0.0006 | 0.91 +- 0.28 | 0.9953 |
| wustl / nofp | 0.9952 +- 0.0005 | 0.9955 +- 0.0010 | 0.82 +- 0.28 | 0.9949 |

**Findings.**
1. The collapse is confirmed to be a threshold problem. With a validation-chosen threshold the
   federated AE matches centralized macro-F1 on Forge and WUSTL, with recall >= 0.996. This does
   not test *why* the q99 threshold fails; the E2 hypothesis about benign concentration stays
   open.
2. The price is benign false alarms. The validation split is attack-majority, so maximising
   macro-F1 lowers the threshold until 2-8% of benign rows are flagged (up to 32% on Edge s46).
   That is above the 1% false-isolation budget used for access control.

**Decision.** The AE is not used as the primary gate. It stays in the zoo report with both
threshold rules, as a candidate unsupervised companion signal for unseen attacks.

## E5 -- Closed-loop Zero-Trust simulator, clean federated detector (Stage 2; done 2026-11-04)

**Question.** Measured in access-control terms, how do these compare when the federated detector
is not under attack?
- per-event gating;
- trust-score (EWMA) isolation;
- sequential change detection (CUSUM), plus SPRT re-authorisation.

This is the no-attack baseline that Stage 3 poisoning is measured against.

**Config** (`src/closed_loop.py`; fixed before the full run).
- **Detector.** Federated MLP trained exactly as in E2 (alpha 0.5, K 10, 30 rounds); the
  best-val round is deployed.
- **Settings.** edgeiiot/keep, forge/nofp, wustl/nofp (no host-fingerprint features). Seeds 42-46.
- **Evidence.** Per-event LLR of the detector logit, from validation histograms (64 bins over
  [-16, 16], +0.5 smoothing, clipped to +-8).
- **Calibration.** On 2,000 benign validation streams of 500 events each. Each policy's threshold
  gives at most a 1% benign false-isolation rate (equal budget). EWMA lambda 0.9. SPRT
  alpha = beta = 0.01, quarantine cap Q_MAX = 100 events. Mixture SPRT RHO_MIN = 0.1.
- **Test streams.** 1,000 devices x 500 events from the test split. 20% are compromised at
  tau ~ U[100, 300).
  - After tau, a share rho in {1.0, 0.5, 0.2} of events are attacks (one attack type per device).
  - Each attack event targets a random other device.
- **Policies** (same streams, paired):
  - per_event;
  - ewma;
  - cusum;
  - cusum_sprt (attack hypothesis = every event);
  - cusum_sprt_mix (attack hypothesis = a share RHO_MIN of events).
- **Ledger.** One block per FL round (global model hash, client update hashes). Decision batches
  of 100 events are each tagged with the deployed model hash. The hash chain is verified.

**Development history** (recorded, not results).
1. The first smoke run (Edge s42, laptop CPU) used 200 devices. With only 160 benign devices the
   1% budget is about +-2 devices of noise, so it was raised to 1,000 devices.
2. That run also showed that a quarantine SPRT against "every event is an attack" re-admits
   58-84% of low-rate attackers (rho 0.5 / 0.2), because their quarantine traffic is mostly
   benign. cusum_sprt_mix was added as the principled fix (a composite low-rate alternative).
   Both are reported.
3. Benign denial was redefined as covering benign devices only. Denying a compromised device's
   benign events after isolation is intended, not collateral damage.

**Smoke result** (Edge s42, 1,000 devices; superseded by the full run):

| metric | per_event | ewma | cusum | cusum_sprt | cusum_sprt_mix |
|---|---|---|---|---|---|
| time-to-isolation, median (p90), events | never isolates | 2-11 (2-24) | 1-4 (2-16) | 1-4 (2-16) | 1-4 (2-16) |
| false re-authorisation, rho 1 / 0.5 / 0.2 | -- | -- | -- | 0 / 0.585 / 0.835 | **0 / 0 / 0** |
| benign devices blocked at the end | 0 | 1.4-2.3% | 0.4-1.4% | 0 | 0-0.25% |

With a clean detector, wrongful grants are about 0 for every policy, because the per-event deny
already stops nearly all attack events. The device-level policies also isolate compromised
devices within a few events. They differ in speed, in false isolation, and in whether attackers
get re-admitted.

Results: `results/closed_loop/hist_empirical/summary.md` (per-run JSON and `_ledger.json`
alongside). The runs used the server copy `~/ztfl_s2`, a separate code directory, so the E3
queue's code version stays fixed. This configuration is called `hist_empirical`: histogram LLR
with empirical CUSUM threshold.

**Numbers** (mean +- std over 5 seeds; rho = 1.0 / 0.2):

| dataset | policy | wrongful grant % | false isolation % (budget 1) | time-to-isolation median | false re-auth % | lateral reach |
|---|---|---|---|---|---|---|
| Edge | per_event | 0.01 / 0.01 | 0 / 0 | -- | -- | 0 / 0 |
| Edge | ewma | 0 / 0 | 1.6 / 1.6 | 2.2 / 12.2 | 0 / 0 | 0 / 0 |
| Edge | cusum | 0 / 0 | 2.8 +- 4.7 / 2.5 +- 4.0 | 1.4 / 9.4 | 0 / 0 | 0 / 0 |
| Edge | cusum_sprt | 0 / 0 | same as cusum (benign blocked at end: 0) | 1.4 / 9.4 | 0 / **84.0** | 0 / 0 |
| Edge | cusum_sprt_mix | 0 / 0 | same as cusum (benign blocked at end: 0.3) | 1.4 / 9.4 | 0 / **0** | 0 / 0 |
| Forge | per_event | 6.95 / 6.37 | 0 / 0 | -- | -- | 19.3 / 3.8 |
| Forge | ewma | 0.17 / 3.12 | 1.9 / 1.5 | 2.0 / 10.2 | 0 / 0 | 0.5 / 1.8 |
| Forge | cusum | 3.25 / 3.94 | **13.1 +- 17.7** / 13.1 +- 18.0 | 1.2 / 5.7 | 0 / 0 | 8.5 / 2.3 |
| Forge | cusum_sprt | 3.47 / 5.86 | same as cusum | 1.2 / 6.1 | 0.95 / **85.1** | 9.1 / 3.5 |
| Forge | cusum_sprt_mix | 3.46 / 4.11 | same as cusum | 1.2 / 6.1 | 0.11 / 2.6 | 9.1 / 2.4 |
| WUSTL | per_event | 6.15 / 6.59 | 0 / 0 | -- | -- | 18.2 / 3.9 |
| WUSTL | ewma | 0.03 / 0.16 | **8.0 +- 8.1** / 6.5 +- 6.9 | 1.2 / 4.4 | 0 / 0 | 0.1 / 0.1 |
| WUSTL | cusum | 0.03 / 0.34 | 5.1 +- 7.1 / 4.2 +- 6.2 | 1.2 / 8.3 | 0 / 0 | 0.1 / 0.2 |
| WUSTL | cusum_sprt | 0.04 / 1.55 | same as cusum | 1.2 / 8.4 | 0.1 / **82.8** | 0.1 / 0.9 |
| WUSTL | cusum_sprt_mix | 0.03 / 0.34 | same as cusum | 1.2 / 8.4 | 0 / 0.2 | 0.1 / 0.2 |

**Findings.**
1. **The per-event gate is not enough on Forge and WUSTL.** It lets 6-8% of attack events
   through, which reach about 18 distinct devices per attacker at rho 1. Device-level isolation
   cuts wrongful grants to 0.03-4% and lateral reach to 0.1-9 devices. On Edge, the detector is
   good enough that the per-event gate already stops nearly everything.
2. **Plain SPRT re-authorisation can be gamed by low-rate attackers.** It re-admits 54-61%
   (rho 0.5) and 83-85% (rho 0.2) of compromised devices. The mixture SPRT reduces this to 0-2.6%
   while still re-admitting falsely isolated benign devices (benign blocked at end 0.3-1.6%,
   versus 2.5-13% for plain CUSUM). This is a positive result for C2's re-authorisation design.
3. **Negative result: the empirical calibration does not hold its 1% false-isolation budget on
   test.** CUSUM averages 2.8% (Edge), 13.1% (Forge) and 5.1% (WUSTL), with high variance across
   seeds (Forge s46: 41.9%; WUSTL s43: 13.9%). EWMA reaches 8.0% on WUSTL. Diagnosis (per-seed
   inspection of thresholds and LLR tables):
   - (a) **The histogram LLR is not monotone.** Empty extreme bins get log(n_benign/n_attack) < 0.
     On Edge, the four most attack-like bins have LLR -1.6.
   - (b) **The empirical threshold degenerates when benign validation streams almost never
     build evidence.** WUSTL h = 0.00-0.35, Forge s46 h = 1.31. The 99th percentile of the max
     CUSUM then sits at the atom at 0, so the first mildly suspicious benign test event
     isolates. The validation benign pool (about 5k rows, resampled into 1M stream events)
     under-represents the rare benign rows that score high in test. EWMA's theta has the same
     problem (WUSTL theta 0.92-0.97, so one event with s of about 0.3 trips it).

**Decision.** E5 stays as the recorded result of the pre-set calibration. Two labelled variants
change one thing at a time:
- **E5b:** monotone LLR, empirical threshold.
- **E5c:** monotone LLR plus Lorden's threshold h = log(T / budget).

### E5b / E5c -- calibration variants (done 2026-11-04)

- **E5b (`monotone_empirical`).** Evidence uses an isotonic (pool-adjacent-violators) fit of the
  bin LLRs, weighted by bin counts. Everything else is as in E5.
- **E5c (`monotone_lorden`).** As E5b, but the CUSUM-family threshold is h = log(T_EV / BUDGET)
  = log(500 / 0.01) = 10.82. Lorden's bound gives ARL0 >= e^h, so P(false alarm within T events)
  is at most about T * e^-h = 1%. The threshold does not depend on rare validation samples. With
  LLR clipped at +-8, at least two strongly suspicious events are needed. EWMA has no analogous
  bound and stays empirically calibrated; whether that matters is part of the C2 claim.
- Same seeds and paired streams as E5. Runner: `scripts/stage2_e5bc.sh`. Results:
  `results/closed_loop/{monotone_empirical,monotone_lorden}/`.
- Note: E6 (chain overhead) used the E5 `hist_empirical` calibration. The chain measurements do
  not depend on the calibration.

All 30 runs finished with no errors (log `logs/closed_loop_e5bc.log`). Sanity check: per_event and
ewma are identical across E5, E5b and E5c, as they should be. per_event does not use the LLR, and
EWMA's calibration is unchanged.

**CUSUM false isolation on test, all rho pooled** (mean +- std over seeds x rho; max = worst seed):

| dataset | E5 hist_empirical | E5b monotone_empirical | E5c monotone_lorden |
|---|---|---|---|
| Edge | 2.62 +- 3.85 (max 11.1) | 2.64 +- 3.90 (max 11.4) | **0.01 +- 0.03 (max 0.12)** |
| Forge | 13.00 +- 16.21 (max 42.1) | 2.17 +- 2.75 (max 6.0) | **0.00** |
| WUSTL | 4.58 +- 5.99 (max 13.9) | 3.72 +- 3.79 (max 11.8) | **0.00** |

**Cost of the Lorden threshold** (cusum_sprt_mix; E5b -> E5c; rho = 1.0 / 0.2):

| dataset | time-to-isolation median, events | detected % | wrongful grant % | lateral reach | false re-auth % |
|---|---|---|---|---|---|
| Edge | 1.4 -> 2.0 / 9.4 -> 26.7 | 100 -> 100 / 99.9 -> 98.0 | 0 -> 0 / 0 -> 0 | 0 -> 0 / 0 -> 0 | 0 -> 0 / 0 -> 0 |
| Forge | 1.4 -> 2.0 / 6.6 -> 26.4 | 95.0 -> 94.9 / 88.1 -> 80.0 | 3.49 -> 3.56 / 5.21 -> 6.06 | 9.2 -> 9.4 / 3.1 -> 3.6 | 0.11 -> 0 / 1.48 -> 0.25 |
| WUSTL | 1.2 -> 2.0 / 7.4 -> 29.8 | 100 -> 100 / 100 -> 99.1 | 0.03 -> 0.06 / 0.30 -> 1.43 | 0.1 -> 0.2 / 0.2 -> 0.9 | 0 -> 0 / 0.10 -> 0.20 |

(per_event for reference, rho 1 / 0.2: Forge 6.95 / 6.37% wrongful grant and 19.3 / 3.8 reach;
WUSTL 6.15 / 6.59% and 18.2 / 3.9.)

**Findings.**
1. **The monotone LLR fixes most of Forge but not the budget.** Forge drops from 13.0% to 2.2%
   false isolation (cause (a) was dominant there). Edge and WUSTL barely move, and all three
   still exceed 1%. This confirms that cause (b), the degenerate empirical threshold, is the
   remaining problem.
2. **Lorden's threshold holds the budget on every seed, dataset and rho** (worst seed 0.12%,
   budget 1%). The threshold is fixed from T and the budget alone, so it needs no rare benign
   validation samples. This is the calibration C2 will report as primary going forward.
3. **The bound is conservative, and the price is low-rate detection speed.** At rho 1 isolation
   still takes 2 events (the minimum with LLR clipped at 8). At rho 0.2 the median rises from
   7-9 to 27-30 events, and on Forge detection falls from 88% to 80%. Observed false isolation
   (~0%) is far below the 1% allowed, so a threshold between the empirical one and Lorden's
   would trade some of that margin back for speed. An operating-curve sweep over h (false
   isolation vs time-to-isolation, all policies) is the fair way to compare policies and is
   added to the plan.
4. **Forge's undetected attackers are a detector limit, not a policy limit.** Each compromised
   device uses one attack type. On Forge some attacker devices are never isolated under any
   CUSUM threshold (detected <= 95% even at rho 1), and wrongful grants stay at 3.5%. Hypothesis
   (not yet verified): these are attack types whose events the detector scores as benign, so
   there is no evidence for a sequential test to accumulate. A per-attack-type breakdown is
   needed to confirm this. *Tested in E5d: partly confirmed, partly corrected.*
5. Mixture SPRT re-authorisation stays effective under the new threshold (false re-auth <= 0.25%).

**Decision (2026-11-04).** From Stage 3 on, the closed loop uses `monotone_lorden` as primary. E5 and E5b stay
in the report as the calibration-failure evidence that motivates it.

### E5d -- operating curves and per-attack-type breakdown (done 2026-11-04)

**Question.** Each E5-E5c policy was compared at one calibrated threshold, so one policy can look
better only because its calibration landed at a different realised false isolation. How do the
policies compare across all thresholds? And why are about 5% of Forge attackers never isolated
(E5c finding 4)?

**Config** (`src/operating_curves.py`, summary `src/summarize_curves.py`).
- The same detectors, seeds and paired test streams as E5c. All 15 deployed models reproduce the
  E5c model hash exactly (determinism check). Evidence: monotone LLR.
- Threshold sweeps:
  - ewma: theta over 15 values in [0.2, 0.995];
  - cusum and cusum_sprt_mix: h over 15 values in [0.5, 20], including Lorden's 10.82;
  - per_event: score threshold in {0.5 ... 1e-4}. It never isolates, so its curve is wrongful
    grants vs benign denial.
- Choosing a threshold from these curves uses test data. The curves analyse the policies; they
  are not a calibration method.
- Per attack type: the event-level detection rate and LLR of each type's test rows. At Lorden's h,
  also the share of devices compromised with that type that get isolated, and their
  wrongful-grant rate.

Results: `results/closed_loop/curves/summary.md`, figures `operating_curves_tti.png` (false
isolation vs median time-to-isolation) and `operating_curves_wrongful.png` (false isolation vs
attack events granted).

**At equal realised false isolation** (best threshold per seed with test false isolation <= 1%;
mean over seeds; rho 1 / 0.2):

| dataset | policy | attack events granted % | median time-to-isolation, events | detected % |
|---|---|---|---|---|
| Edge | ewma | 0 / 0 | 2.8 / 17.5 | 100 / 100 |
| Edge | cusum (= cusum_sprt_mix) | 0 / 0 | 1.6 / 17.6 | 100 / 99.4 |
| Forge | ewma | **0.48** / **3.23** | 3.0 / 14.4 | 100 / 97.2 |
| Forge | cusum (= cusum_sprt_mix) | 3.51 / 5.42 | 1.2 / 8.8 | 94.9 / 87.9 |
| WUSTL | ewma | 0.03 / 0.15 | 1.0 / 4.1 | 100 / 100 |
| WUSTL | cusum (= cusum_sprt_mix) | 0.03 / 0.16 | 1.0 / 4.2 | 100 / 100 |

**Per attack type** (Forge, rho 1, mean over seeds): every type is isolated on 100% of its
devices except `mitm_dhcp`:
- 0% of `mitm_dhcp` devices are isolated, and 62% of their attack events are granted, which is
  the same as per_event;
- only 38% of `mitm_dhcp` events are flagged (score >= 0.5), and 98% of its events get LLR <= 0;
- `mitm_dhcp` has 41 training rows (the smallest class in any dataset).

Other low-support types (dos_deauth, mitm_arp; WUSTL Backdoor, CommInj) are partly missed per
event (event detection 73-90%) but still isolated on 100% of devices, with wrongful grants of
0.1-1.4%.

**Findings.**
1. **On Edge and WUSTL, CUSUM and EWMA are equivalent** at equal realised false isolation.
   CUSUM is faster on Edge at rho 1 (1.6 vs 2.8 events). This means CUSUM's advantage in C2 is
   the *a-priori guarantee* (Lorden, E5c), not raw speed.
2. **On Forge, EWMA beats CUSUM on wrongful grants** (0.48% vs 3.51% at rho 1). CUSUM's curve
   flattens at about 3.5%: lowering h only adds false isolation. The floor is `mitm_dhcp`.
3. **E5c finding 4 is partly confirmed and partly corrected.** It is partly a detector limit (62%
   of `mitm_dhcp` events are missed). It is also an **evidence-model limit**: the 38% of its
   events that the detector does flag fall into bins where the validation-histogram LLR is
   <= 0, because the class is too rare for the histogram to represent. EWMA uses the raw score,
   so those flagged events still lower trust. The evidence model, not CUSUM, is the weak link
   for rare attack types.
4. **A tuned per-event threshold is a strong baseline, so policies must be compared at equal
   benign cost.** Lowering the per-event threshold trades wrongful grants for benign denial
   (events of benign devices that are denied). This is a cost every policy pays, so it is the
   common axis. Lowest attack events granted (%) at a benign-denial budget, best threshold per
   seed, mean over seeds, rho 1 / 0.2:

   | benign denial budget | dataset | per_event | ewma | cusum_sprt_mix |
   |---|---|---|---|---|
   | <= 1% | Forge | 7.41 / 6.80 | **0.61 / 4.03** | 4.36 / 6.40 |
   | <= 1% | WUSTL | 0.82 / 0.92 | 0.03 / 0.15 | **0.03 / 0.14** |
   | <= 2% | Forge | 0.22 / **0.24** | **0.16** / 3.04 | 3.46 / 4.04 |
   | <= 2% | WUSTL | 0.17 / 0.24 | 0.03 / 0.15 | **0.03 / 0.14** |

   Edge is 0-0.02% for every policy, because its benign-denial floor is the 0.55% label-noise
   flag rate.
   - At <= 1% benign denial, device-level isolation beats the per-event gate by 10-30x on WUSTL
     and (EWMA) on Forge.
   - At <= 2%, a per-event threshold of about 0.05 catches up on Forge, and beats both CUSUM
     variants at low rate (rho 0.2), because it does not depend on the rare-class LLR.
   - Implication for the manuscript: the per-event baseline is reported at matched benign
     denial, not only at 0.5.

**Consequence for C2 (not yet run, to be proposed).** An evidence model that cannot report "no
evidence" for a flagged event: for example, an LLR floor at 0 for scores >= 0.5, or pooling the
attack likelihood per attack family. This would be a labelled variant, evaluated with the same
curves.

---

## E6 -- On-chain model provenance: overhead and rollback (C3; done 2026-11-04)

**Question.** What does writing the provenance records to an EVM chain cost, does the gateway
ever wait for it, and does revocation (rollback) work?

**Config.**
- **Contract.** `contracts/src/Provenance.sol` (Solidity 0.8.24, optimizer 200 runs).
  - `commitRound`: global model hash, client update hashes and sizes, validation F1. It stores
    the model -> round mapping and a sha256 root over the client updates; rounds must be
    committed in order.
  - `commitDecisions` (gateway role): model hash, event range, count, digest. It reverts if the
    model was never committed.
  - `revokeRound` and `isTrusted(model)`.
- **Ledger.** `src/ledger.py` `EvmLedger`. Each record goes into the local hash chain and is
  then queued to a sender thread; a confirmer thread timestamps the receipts.
- **Node.** anvil (Foundry 1.8.4) on the GPU server with `--block-time 2`, a stand-in for
  PureChain's 2.0 s transactions. It is bound to localhost and reached from the laptop through
  an SSH tunnel.
- **Run.** The closed loop runs on the **laptop (CPU) as the edge gateway**: Edge-IIoTSet, MLP,
  seeds 42-46, otherwise the same config as E5.

Results: `results/chain/anvil_bt2/edgeiiot/keep/mlp_s<seed>.json`, field `chain`.

**Numbers** (5 seeds; 105 on-chain writes per run = 30 round commits + 75 decision batches):

| quantity | value |
|---|---|
| failed transactions | 0 / 525 |
| contract deployment gas | 630,964 |
| round commit gas (10 client hashes) | 136,323 |
| decision-batch commit gas | 30,158-30,170 |
| round commit latency, submit -> confirmed, median (p95) | 0.97-1.13 s (1.82-1.96 s) |
| decision-batch latency, median (p95) | 2.2-5.9 s (3.0-7.6 s) |
| gateway time spent queueing all 105 writes | 0.83-0.91 ms per run (about 8 us per write) |
| run wall time, EVM vs in-memory ledger | 24-28 s vs about 20 s (laptop CPU training dominates) |

**Rollback check.**
- After `revokeRound(2)`, `isTrusted(model of round 2)` returns false, while round 1 stays
  trusted. The revocation confirmed in 1.96 s (one block).
- A decision batch that cites an uncommitted model hash is rejected on-chain (1 failed tx, as
  intended).
- In every run, the deployed model was confirmed trusted on-chain.

**Findings.**
1. Enforcement never waits for the chain: the gateway pays about 8 microseconds per write (a
   queue put). Round commits confirm within about 1 block.
2. Decision-batch latency is inflated by the simulator. All 75 batches are produced at once at
   the end of a run (500 events x 5 policies x 3 rho are simulated instantly), so they queue
   behind 2-s blocks. In deployment, batches are spread over time; the emulated testbed
   (stage 4) measures this properly.
3. Revocation propagates in one block (about 2 s). The rollback exposure window is therefore
   bounded by the gateway's polling interval plus about 2 s.

---

## E7 -- Stage 3: poisoning the federated detector as privilege escalation (C1; done 2026-11-05)

**Question.** When some FL clients are malicious, how much access does a poisoned detector hand to
attackers at the gateway, and how much do robust aggregation and the sequential gate (E5c) take
back?

**Protocol** (fixed before the full run; `src/poison.py`, `src/stage3.py`, hooks in
`src/train_fed.py`):
- **Federation.** As E2: MLP, K 10, Dirichlet alpha 0.5, 30 rounds. The default path (no attack,
  FedAvg) is the unchanged E2 code.
- **Threat model.** m in {1, 2, 3} of 10 clients are malicious (10/20/30%), chosen per seed. They
  collude and know the aggregation rule. Model-poisoning attacks are omniscient (they see the
  round's honest updates), which is the standard worst case.
- **Attacks.**
  - `label_flip`: malicious clients train on y -> 1 - y.
  - `alie` (Baruch et al. 2019): mu - z sigma of the honest updates, z from n and m.
  - `minmax` (Shejwalkar & Houmansadr 2021): mu + gamma p, with p = -sigma normalised and the
    largest gamma that keeps the update within the maximum honest pairwise distance.
  - `backdoor` ("whitelist-me", targeted): malicious clients add every training row of a
    target attack type, relabelled benign, and boost their update by K/m (model replacement,
    Bagdasaryan et al. 2020). The target is the backdoor-malware class, chosen a priori: Edge
    `Backdoor`, Forge `malw_back`, WUSTL `Backdoor`. Success = share of target-type test rows
    scored benign.
  - `none`: the clean reference for each aggregator.
- **Aggregators.**
  - `fedavg`;
  - `median` (coordinate-wise);
  - `trimmed_mean` (drop f per side);
  - `multi_krum` (keep the n - f lowest-score updates);
  - `fltrust`: trust = ReLU(cos) to a server update computed on a 500-row stratified root set
    from the server's validation split; updates rescaled to the root norm.
  - f = the true m, the defender's best case. "Ours" is not defined yet; it will be proposed
    after these baselines.
- **Two deployment practices.** "best" deploys the server's best-validation round, as in all
  earlier experiments. "last" always deploys the latest round.
- **Access control.** The E5c closed loop (monotone LLR, Lorden's h), calibrated on validation
  with the *deployed, possibly poisoned* model, as a real gateway would. Policies: per_event and
  cusum_sprt_mix; rho 1.0 and 0.2. Two stream sets: "all" (random attack type per device, as in
  E5) and "target" (every compromised device uses the backdoor target type).
- **Scale.** 3 datasets x 5 attacks x 5 aggregators x 3 m x 5 seeds = 1,125 runs, on GPU 0
  (Forge) and GPU 1 (Edge, WUSTL). Queue: `scripts/stage3_queue.sh`; logs
  `logs/stage3_forge.log`, `logs/stage3_edge_wustl.log`. Results:
  `results/poison/<attack>_m<m>/<aggregator>/<dataset>/<mode>/mlp_s<seed>.json`.

**Smoke runs** (seed 42; same code as the full run, so they are kept as part of it):

Edge, m = 2. With FedAvg and Multi-Krum, label flip, ALIE and min-max leave the detector at
F1 0.9984 in both the best and the last round. The attacks are applied (round-1 validation F1
differs from the clean run), but Edge's classes are separated by such a wide margin that 20%
malicious clients cannot move the boundary. The boosted backdoor under FedAvg reaches 97.9%
success in the last round (F1 0.77). Best-val selection deploys round 8 instead, with 0% success,
so the server's validation split acts as a defense here.

Forge, m = 3, FedAvg vs Median (best-val deployment; attack events granted at rho 1, all
streams):

| attack | FedAvg F1 | FedAvg per_event / cusum_sprt_mix | Median per_event / cusum_sprt_mix | backdoor success, best / last (FedAvg) |
|---|---|---|---|---|
| none | 0.9944 | 0.78% / 0.05% | 0.75% / 0.03% | 0.3% / 0.3% |
| label_flip | 0.9778 | 14.4% / 5.3% | 2.7% / 1.1% | 16% / 16% |
| alie | 0.9927 | 3.6% / 1.5% | 3.5% / 1.5% | 0.5% / 0.5% |
| minmax | 0.9887 | 9.3% / 5.0% | 4.7% / 2.9% | 0.5% / 2.6% |
| backdoor | 0.9881 | 5.3% / 2.4% | 3.0% / 0.1% | **28.7% / 100%** |

**Implementation error found in FLTrust (2026-11-04, during the run).**
- Symptom: in the interim results, `fltrust` lowered clean accuracy with no attacker (Forge F1
  0.953 vs 0.991) and collapsed under label flip on Edge (F1 0.58; every other aggregator 0.998).
- Cause: the server's root update g0 was trained for one epoch on the 500-row root set. With
  batch 512 that is **one optimiser step**, against 20-70 steps for a client, so g0 was close to
  an Adam sign vector.
  - Clean Edge s42: 6 of 10 honest clients got trust 0 in every round.
  - Under label flip, the three flipping clients (3, 4, 9) got trust 0.47, more than most honest
    clients.
- Fix: `fltrust_v2` tiles the root set to the mean client size, so the server takes as many local
  steps as an average client (as in Cao et al.).
  - Edge s42 m3: F1 0.9984 for both none and label_flip; the flipping clients' trust falls to
    about 0 by round 15.
  - Several honest clients still get trust 0. That is FLTrust's known non-IID weakness, not the
    bug.
- The original `fltrust` results are kept and reported as the implementation error.
  `fltrust_v2` is the FLTrust result.
- Run: 225 runs (3 datasets x 5 attacks x 3 m x 5 seeds) from a separate server copy `~/ztfl_s3`,
  so the main queue's code version stays fixed. Runner `scripts/stage3_fltrust_v2.sh`, log
  `logs/stage3_fltrust_v2.log`, results under `results/poison/*/fltrust_v2/`.

**Completed runs.**
- 1,125 main runs, code version `daf135fb508b`, plus 225 `fltrust_v2` runs, code version
  `834d436f3ee6`. The second version only adds the v2 root-set tiling.
- 0 errors.
- Summary: `python src/summarize_stage3.py` -> `results/poison/summary.md` (every cell, both
  deployments, all m) and `results/poison/summary_long.csv`.
- Cells are mean over 5 seeds (std in summary.md). Below, `fltrust` is the implementation error
  and is shown only where noted.

**Table E7-1. Clean test macro-F1 (%), m = 3, best-val deployment.**

| dataset | attack | FedAvg | Median | Trimmed | Multi-Krum | FLTrust (bug) | FLTrust v2 |
|---|---|---|---|---|---|---|---|
| Edge | none | 99.8 | 99.8 | 99.8 | 99.8 | 95.5 | 99.8 |
| Edge | label_flip | 99.8 | 99.8 | 99.8 | 99.8 | 50.9 | 99.8 |
| Edge | alie / minmax | 99.8 | 99.8 | 99.8 | 99.8 | 99.8 | 99.8 |
| Edge | backdoor | 98.8 | 99.8 | 99.8 | 99.8 | 67.1 | 99.8 |
| Forge | none | 99.1 | 99.1 | 99.1 | 99.2 | 96.2 | 99.5 |
| Forge | label_flip | 98.4 | 99.0 | 99.0 | 99.1 | 94.4 | 99.4 |
| Forge | alie / minmax | 99.2 / 99.0 | 99.1 / 99.2 | 99.1 / 99.1 | 99.1 / 99.2 | 96.6 / 96.5 | 99.3 / 99.3 |
| Forge | backdoor | 98.2 | 98.9 | 98.9 | 99.1 | 95.7 | 99.4 |
| WUSTL | none | 99.9 | 99.9 | 99.9 | 99.9 | 98.7 | 99.9 |
| WUSTL | label_flip | **78.3 ± 43.4** | 99.9 | 99.9 | **80.2 ± 44.0** | 98.7 | 99.9 |
| WUSTL | alie / minmax | 99.9 | 99.9 | 99.9 | 99.9 / 99.8 | 98.7 | 99.9 |
| WUSTL | backdoor | 99.8 | 99.9 | 99.9 | 99.9 | 98.7 | 99.9 |

**Table E7-2. Backdoor success (%, target-type test rows scored benign). "clean" = the same
aggregator with no attack.**

| dataset | aggregator | clean | m=1 | m=2 | m=3 | last round: clean | m=1 | m=2 | m=3 |
|---|---|---|---|---|---|---|---|---|---|
| Edge | FedAvg | 0.1 | 1.7 | 0.1 | 0.1 | 0.1 | **98.2** | **97.7** | **97.7** |
| Edge | Median / Trimmed / Multi-Krum / FLTrust v2 | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 |
| Edge | FLTrust (bug) | 0.5 | 18.3 | 59.0 | 79.1 | 0.5 | 18.3 | 59.0 | 79.4 |
| Forge | FedAvg | 1.2 | **54.0** | **52.2** | **62.5** | 1.3 | 72.9 | 83.6 | **100.0** |
| Forge | Median | 0.9 | 1.2 | 3.4 | 8.4 | 0.9 | 1.5 | 2.3 | 11.1 |
| Forge | Trimmed mean | 0.9-1.4 | 1.3 | 3.5 | 8.4 | 1.1 | 2.0 | 3.3 | 11.3 |
| Forge | Multi-Krum | 0.9-1.3 | 1.0 | 0.8 | 1.6 | 0.9-1.3 | 1.3 | 0.9 | 1.2 |
| Forge | FLTrust v2 | 0.4 | 0.4 | 0.6 | 1.5 | 2.2 | 3.6 | 7.5 | 12.5 |
| WUSTL | FedAvg | 14.9 | 46.5 | 63.7 | **65.1** | 16.7 | 80.5 | 94.0 | **99.5** |
| WUSTL | Median | 12.6 | 17.7 | 25.1 | 30.7 | 12.1 | 15.3 | 22.8 | 33.5 |
| WUSTL | Trimmed mean | 12.1 | 20.9 | 25.6 | 32.6 | 12.6-13.5 | 22.3 | 26.5 | 36.7 |
| WUSTL | Multi-Krum | 12.6-14.9 | 14.0 | 15.3 | 15.8 | 13.5-14.4 | 16.7 | 15.3 | 17.2 |
| WUSTL | FLTrust v2 | 23.3 | 24.7 | 26.0 | 24.7 | 25.1 | 28.4 | 40.5 | 48.8 |

The clean baseline differs slightly with m for Trimmed mean and Multi-Krum, because f = m changes
the rule even with no attacker; ranges are shown.

**Table E7-3. Gateway under the backdoor: attack events granted (%), "target" streams (every
compromised device uses the whitelisted type), m = 3. Cells: per_event / cusum_sprt_mix.**

| dataset | aggregator | best, rho 1 | best, rho 0.2 | last, rho 1 | last, rho 0.2 |
|---|---|---|---|---|---|
| Edge | FedAvg | 0.06 / 0.00 | 0.06 / 0.02 | **97.8 / 0.97** | **97.7 / 38.3** |
| Forge | FedAvg | **62.6 / 59.6** | **62.6 / 62.6** | **100 / 88.1** | **100 / 100** |
| Forge | Median | 8.4 / 0.20 | 8.3 / 8.1 | 11.0 / 0.28 | 10.9 / 10.6 |
| Forge | Multi-Krum | 1.6 / 0.02 | 1.6 / 1.1 | 1.2 / 0.01 | 1.2 / 0.67 |
| Forge | FLTrust v2 | 1.5 / 0.02 | 1.5 / 1.2 | 12.5 / 0.25 | 12.3 / 9.4 |
| WUSTL | FedAvg | **65.2 / 6.8** | **65.5 / 65.4** | **99.6 / 8.5** | **99.6 / 99.3** |
| WUSTL | Median | 30.7 / 0.96 | 31.0 / 30.0 | 33.5 / 1.2 | 33.7 / 33.4 |
| WUSTL | Multi-Krum | 15.9 / 0.19 | 16.0 / 4.0 | 17.3 / 0.20 | 17.5 / 4.4 |
| WUSTL | FLTrust v2 | 24.7 / 0.33 | 24.9 / 8.0 | 48.8 / 6.6 | 49.1 / 47.1 |
| (clean ref.) | FedAvg, no attack: Forge / WUSTL | 1.2 / 0.01, 15.0 / 0.17 | 1.2 / 0.6, 15.2 / 3.8 | | |

**Findings.**
1. **Untargeted attacks barely move the detector at m <= 3 of 10.**
   - ALIE and min-max change test F1 by <= 0.4 pp everywhere, even though they are omniscient.
     With z = Phi^-1(0.7) = 0.52, ALIE's shift is small, and min-max is bounded by the honest
     spread, which is already wide under non-IID clients.
   - Label flip matters only when the flippers hold most of the training rows. WUSTL FedAvg:
     flippers with 54% and 61% of the rows (seed 43, m = 2 and 3) invert the model completely
     (F1 0.01); 39% (seed 46) gives F1 0.91; at 36% or less F1 stays at 0.999.
   - Multi-Krum also inverted once (WUSTL s42 m3). It kept all three flippers and dropped three
     honest clients whose non-IID updates looked like outliers.
   - Median and trimmed mean resisted label flip in every run.
2. **An inverted detector turns the gateway into a denial of service.** In the inverted runs,
   cusum_sprt_mix isolates 100% of benign devices. Poisoning attacks availability as well as
   access.
3. **The targeted backdoor is the privilege-escalation threat**, and deployment practice decides
   how much it gets.
   - With "last" deployment under FedAvg it whitelists its target almost completely at m = 3:
     Edge 97.7%, Forge 100%, WUSTL 99.5%.
   - With best-val deployment, Edge is fully protected (0.1%). Whitelisting the large Edge
     `Backdoor` class drops validation F1 to 0.77, so the server keeps an early round (2-10).
     This is a crude rollback.
   - On Forge and WUSTL the target class is too small to move macro-F1 (98.2 / 99.8 at m = 3).
     Best-val keeps the backdoored round, and success is 62.5% and 65.1% (clean 1.2% / 14.9%),
     already 54% / 47% at m = 1.
   - So the server's validation check works only when the target type weighs enough in an
     aggregate metric.
4. **No robust aggregator is safe on every axis** (defender's best case, f = true m).
   - **Multi-Krum** is best against the backdoor: excess over clean <= +1 pp on Forge and WUSTL
     with best-val deployment, <= +4 pp in the last round.
     It is also the one rule that inverted under label flip (finding 1).
   - **Median and trimmed mean** resist label flip, but leak the backdoor more as m grows: Forge
     8.4%, WUSTL 31-33% at m = 3, i.e. +18-20 pp over clean on WUSTL.
   - **FLTrust v2** holds the backdoor under best-val deployment (excess about +1 pp). In the last round
     success grows with m: Forge 3.6 / 7.5 / 12.5%, WUSTL 28 / 41 / 49% against 25% clean.
     FLTrust v2 also raises WUSTL's clean miss rate on the target from 15% to 23%: honest non-IID
     clients get trust 0 and the rare class is under-learnt.
   - The buggy `fltrust` is the worst rule overall: Edge backdoor 79% and label-flip F1 0.51 at
     m = 3.
5. **The sequential gate (C2) takes back much of what an untargeted or weak poisoning gives
   away, but not a backdoor whose traffic is mixed with benign traffic.**
   - At rho 1, cusum_sprt_mix cuts grants on the whitelisted type sharply in most cells. WUSTL
     FedAvg best: 65 -> 6.8%. Edge FedAvg last: 97.8 -> 0.97%. The backdoored model's scores still
     carry weak evidence, which accumulates over a device's repeated events.
   - Forge FedAvg keeps 59.6% (best) and 88% (last) even at rho 1: those scores carry no evidence.
   - At rho 0.2 the gain disappears for the strong backdoors. Grants equal the per-event gate:
     Forge 62.6 / 100%, WUSTL 65.4 / 99.3%; Edge last falls only to 38%.
   - Continuous authorization cannot recover what a poisoned model whitelists. Prevention before
     deployment and revocation after it (C3) are required. This motivates the proposed defence
     ("Planned").
6. **The false-isolation guarantee survives poisoning, except under an inverted model.**
   - Excluding inverted runs and the buggy `fltrust`, cusum_sprt_mix's false isolation exceeds
     the 1% budget in 21 of 2,243 deployment x stream cells. All 21 are on Edge; max 1.38% at
     rho 1 and 2.00% at rho 0.2; mean 0.015%.
   - The gateway is calibrated on validation with the deployed, possibly poisoned model.
7. **Caveat on FLTrust.** Its 500-row root set is drawn from the server's validation split, the
   same rows used for best-val selection and gateway calibration.
   - FLTrust v2's best-val Forge numbers (F1 99.5; all-stream grants 1.1% per-event vs 6.9% for
     FedAvg, clean) partly reflect 500 extra labelled training rows.
   - Test data is never used.
   - A disjoint root set would be the stricter design. To state in the manuscript.

---

## E8 -- The proposed defence: per-type canary check + provenance registry with rollback (C1 + C3; done 2026-11-05)

**Decision (2026-11-05).** Scope "canary + rollback": a per-type canary check plus an
on-chain registry and rollback, tested on top of FedAvg and Multi-Krum (and Median / FLTrust v2
for free, same runs). The adaptive attacker is included. Client attribution / quarantine is not
built.

**Motivation (E7 findings 3-5).**
- The server's best-val selection protects only when the target type weighs in macro-F1.
- No aggregator is safe on every axis.
- The sequential gate cannot recover traffic the model has whitelisted.
- Hence: check every type before deployment, and keep the gateway on the last version that passed.

**Rule** (`src/canary.py`). The canary is the server's validation split, the same data the best-val
baseline uses, so both rules see the same information. After each round, the candidate global is
promoted only if:
- every attack type with >= 20 canary rows has detection >= ref_t - delta, where ref_t is the best
  detection of any promoted version after the warm-up (a ratchet, so the reference cannot be walked
  down);
- the benign flag rate is <= ref_b + 0.01, with ref_b the lowest of any promoted version;
- macro-F1 is >= 0.5 (from round 2 on).

Other details:
- Rounds 1-5 are the warm-up and skip the per-type check.
- Training continues on the server's global model; only deployment is gated.
- Promoted versions get a verdict block on the provenance ledger. The gateway runs the registry
  head, so rollback means the head stays at the last version that passed.
- delta: 0.05 primary; 0.02, 0.10 and 0.25 come free from the same run.

**Adaptive attacker** (`backdoor_adaptive`, `src/poison.py`). The attackers know:
- the rule and delta;
- the public registry (which versions were promoted);
- the round's honest updates (omniscient, as for ALIE / min-max).

They do not know the canary rows. They track their own proxy (the target-type training rows plus
their own benign rows) on every promoted version. Each round they scale the backdoor boost to the
largest lambda in [0, K/m] whose aggregate passes the proxy check at 80% of the allowed drop.
During the warm-up they boost fully.

**Matrix** (`src/defense.py`). 3 datasets; attacks none / label_flip / backdoor / backdoor_adaptive;
aggregators FedAvg / Median / Multi-Krum / FLTrust v2; m 1-3; 5 seeds.
- Onset 1 (attack from round 1, as in E7; the warm-up is then poisoned).
- Onset 11 (clients compromised after 10 clean rounds; the Zero-Trust "trusted device turns"
  case).
- ALIE and min-max are left out: they did not move the detector in E7.
- 1,260 runs.

**Deployment tracks** (paired, from the same training run):
- best-val and last, as in E7;
- the canary head for each delta.

**Reported per track:**
- the final deployed model;
- exposure: max / mean backdoor success of the model the gateway runs in each round, from
  max(onset, 6);
- staleness;
- false rejections (no-attack runs);
- the E5c closed loop for best, last and canary(0.05).

**Smoke runs and changes before the full run** (seed 42, WUSTL, m = 3):
- The trainer with the new hooks reproduces E7 bit-for-bit: WUSTL backdoor FedAvg and label-flip
  FLTrust v2 have the same F1 and best round.
- Plain backdoor, onset 11, FedAvg: all 20 poisoned rounds were rejected. The gateway stayed on
  round 10 with backdoor success 32.6% (clean ~28%), against 95.3% for "last".
- **Onset 1** defeats the rule as expected: the warm-up references are already backdoored (95.3%).
- **False rejections.** WUSTL's canary has only 21 Backdoor and 26 CommInj rows. Clean Multi-Krum
  switches between 15 and 20 detected Backdoor rows from round to round (0.71 <-> 0.95), because it
  excludes a different honest client each time, so 18 of 25 checked rounds were rejected with no
  attacker. FedAvg had 0.
  - Kept as pre-registered, and reported as the cost (staleness).
  - delta 0.25 was added to the free sweep to show the trade-off.
- **Change 1:** label flip at onset 1 under Multi-Krum produced an inverted model (F1 0.01) that was
  promoted during the warm-up. Added the F1 >= 0.5 floor.
- **Change 2:** exposure now starts at max(onset, 6), so untrained warm-up rounds do not count.
- The earlier smoke results were deleted. The full run uses only the final code.
- **Second smoke run** (final code, seed 42, m = 3, onset 11; kept as part of the full run).
  - **Forge:** backdoor success with the canary check was 0.3% under FedAvg, against 100% for
    "last". The gateway stayed on round 10.
  - **Edge:** 0.0% against 97.9%.
  - **Adaptive attacker:** Edge FedAvg 4.3% against 4.8% for "last" (best-val 0.0%); on Forge it
    gets only 3.4% even without the check.
  - **Forge false rejections (no attack).** FedAvg rejected 8 of 25 checked rounds at delta 0.05,
    1 at 0.10 and 0 at 0.25, all on dos_deauth (canary detection swings 0.79-0.91). Multi-Krum:
    7 / 4 / 0.
  - **Forge under attack.** Rejections also fall on dos_deauth and mitm_arp, not only on the
    target. Relabelling malw_back rows as benign also moves neighbouring types' boundaries, and the
    per-type check sees it.
- **Launched** 2026-11-05 00:42 KST: `scripts/defense_queue.sh`, 7 workers (GPU 0: Forge s42-44;
  GPU 1: Forge s45-46, Edge, WUSTL then E5e). Logs `logs/defense_*.log`, `logs/curves_e5e.log`.

**Completed** 2026-11-05: 1,260 / 1,260 runs, 0 errors. Summary `src/summarize_defense.py` ->
`results/defense/summary.md` (all cells, m 1-3, all four aggregators, delta sweep) and
`summary_long.csv`. Excess = backdoor success minus the same track's success in the no-attack run
(same dataset, aggregator, m, seed). Clean backdoor success is 0.1% (Edge), ~1% (Forge) and
10-25% (WUSTL, whose Backdoor type is partly missed even without an attacker).

**Table E8-1. Backdoor success excess of the final deployed model, pp** (m = 3, mean over 5
seeds; canary at delta 0.05, delta 0.25 in brackets).

| dataset | attack | onset | FedAvg best / last / canary | Multi-Krum best / last / canary |
|---|---|---|---|---|
| Edge | backdoor | 11 | 0.0 / 97.7 / **0.0** (3.5) | 0.0 / 0.0 / 0.0 (0.0) |
| Edge | backdoor | 1 | 0.0 / 97.7 / 35.2 (36.0) | 0.0 / 0.0 / 0.0 (0.0) |
| Edge | adaptive | 11 | 0.0 / 4.1 / 3.8 (4.1) | 0.0 / 0.0 / 0.0 (0.0) |
| Forge | backdoor | 11 | 0.0 / 98.7 / **0.1** (0.1) | -0.2 / 0.4 / 0.2 (0.4) |
| Forge | backdoor | 1 | 61.3 / 98.7 / 98.7 (98.7) | 0.6 / 0.3 / 0.4 (0.3) |
| Forge | adaptive | 11 | 1.7 / 4.3 / 2.6 (4.3) | -0.2 / 1.0 / 0.2 (1.0) |
| WUSTL | backdoor | 11 | 7.4 / 78.6 / **3.3** (19.1) | 1.4 / 4.2 / 1.4 (4.2) |
| WUSTL | backdoor | 1 | 50.2 / 82.8 / 49.8 (43.3) | 0.9 / 3.7 / 6.5 (3.7) |
| WUSTL | adaptive | 11 | 5.6 / 6.5 / 7.4 (6.5) | -2.8 / 0.5 / 3.7 (0.5) |

**Table E8-2. False rejections and staleness, no-attack runs** (share of checked rounds 6-30
rejected, %; mean over m and seeds).

| dataset | aggregator | delta 0.02 | 0.05 | 0.10 | 0.25 |
|---|---|---|---|---|---|
| Edge | all four | 0 | 0 | 0 | 0 |
| Forge | FedAvg | 60.8 | 7.2 | 0.8 | 0 |
| Forge | Median / Multi-Krum | 67.2 / 62.1 | 32.8 / 34.1 | 27.2 / 22.4 | 0 / 0 |
| Forge | FLTrust v2 | 83.2 | 76.8 | 74.4 | 59.2 |
| WUSTL | FedAvg | 62.4 | 38.4 | 8.0 | 0 |
| WUSTL | Median / Multi-Krum | 32.0 / 37.9 | 16.8 / 29.3 | 6.4 / 18.7 | 0 / 0.8 |
| WUSTL | FLTrust v2 | 68.0 | 53.6 | 35.2 | 4.0 |

The clean F1 of the canary head equals the last round's to within 0.07 pp in every cell (FLTrust v2
on Forge: canary 99.45 vs last 98.55, since the check holds back its noisy last rounds). Mean
final staleness over all runs: best-val 25.8 / 16.0 / 12.1 rounds (Edge / Forge / WUSTL), canary
(0.05) 1.8 / 9.5 / 5.9, canary (0.25) 1.1 / 3.5 / 1.5.

**Gateway** (target streams, cusum_sprt_mix, m = 3, FedAvg, onset 11, rho 0.2; attack events
granted, best / last / canary): Edge 0.01 / 38.0 / 0.02%; Forge 0.56 / 100 / 0.70%; WUSTL 6.3 /
95.2 / 6.7% (WUSTL clean level ~6%). The ledger check passed in 1,260 / 1,260 runs: every round,
the gateway ran the hash at the registry head.

**Findings.**
1. **The canary check stops a client that turns malicious after the federation is trusted
   (onset 11).** Under FedAvg the final excess is 0.0 / 0.1 / 3.3 pp (Edge / Forge / WUSTL),
   against 97.7 / 98.7 / 78.6 pp when the last round is deployed. Exposure gives the same picture:
   the max excess while deployed is <= 0 pp on all three datasets, so no backdoored version
   reached the gateway. The gateway's grant rate for the target type falls from 38-100% to the
   clean level.
2. **The adaptive attacker must give up most of the backdoor to pass.** Knowing the rule, delta
   and the registry, the attacker keeps a final excess of 3.8 / 2.6 / 7.4 pp under FedAvg (Edge /
   Forge / WUSTL), against 78.6-98.7 pp for the same attackers when nothing is checked. The rejected
   share falls (Edge 72.8% -> 34.4%) because the attacker now stays under the threshold. "last" is
   about equal to the canary in the adaptive rows because the attacker limits itself whichever
   version is deployed. The bound is the allowed drop: about delta of the target's detection.
3. **Onset 1 defeats the check, as pre-registered.** The warm-up references are already
   backdoored. Under FedAvg: Forge 98.7 pp (worse than best-val's 61.3), WUSTL 49.8, Edge 35.2.
   Edge is bimodal: seeds 43 and 44 reach 87-88%, the other three <= 0.2%. The canary is a defence
   against a client that turns, not against a federation poisoned from round 0. That case needs a
   trusted reference, such as a genesis model signed into the registry, and is a stated limitation.
4. **Best-val selection is almost as protective in this setting, but it stops updating.** Over the
   720 backdoor runs the canary is within 2 pp of best-val in 533 runs, better by more than 2 pp in
   81 and worse in 106 (mostly onset 1). Best-val protects because macro-F1 peaks early (Edge round
   ~4) and it never deploys again: final staleness 25.8 rounds on Edge, against 1.8 for the canary.
   In this stationary simulation that costs no F1. Under drift, or when new attack types are added,
   it would. What the canary adds over best-val:
   - fresh deployment;
   - a per-type verdict on the ledger that names the failing type;
   - an explicit rule that the adaptive attacker can be analysed against.
   E8 does not show that the canary beats best-val on backdoor success alone. State it this way in
   the manuscript.
5. **False rejections are the cost, and they come from small canary types.** With no attacker,
   delta 0.05 rejects 0% of Edge rounds but 7-77% on Forge and 17-54% on WUSTL. The rejections fall
   on types with 20-60 canary rows (Forge dos_deauth, WUSTL Backdoor / CommInj), where one or two
   rows move detection by more than delta. Robust aggregators reject more because they drop a
   different honest client each round. The cost is staleness, not accuracy (clean F1 unchanged).
   - delta 0.10 is the middle point: Forge FedAvg 0.8% false rejections, WUSTL FedAvg 8%, and
     onset-11 FedAvg excess 0.7 / 0.1 / 9.8 pp.
   - delta 0.25 removes almost all false rejections but lets 19.1 pp through on WUSTL.
   - A fixed delta for every type is the weakness. A per-type tolerance set from the canary's
     binomial confidence interval is the natural fix. It is tested in E8b.
6. **On Multi-Krum the canary adds little.** Multi-Krum alone keeps every backdoor cell <= 4.2 pp.
   The canary leaves it there (WUSTL onset 1: 6.5 vs 3.7 for last) and costs 29-34% false
   rejections.
7. **The closed loop is unchanged by the canary.** False isolation (all streams, rho 1,
   cusum_sprt_mix) exceeds 1% in 4 canary cells, against 22 for best-val. All are on Edge. One
   outlier: adaptive, m = 1, onset 1, seed 42, where the head stayed at round 7 (F1 0.82): 4.6%.
   The two 100% cells are WUSTL "last" under the inverted label-flip model, as in E7.

**Novelty check (2026-11-05, before E8b/E9).** BaFFLe (Andreina et al., IEEE ICDCS 2021,
arXiv 2011.02167) already rejects FL global models whose per-class misclassification on validation
data shifts. A per-class canary check alone is therefore NOT a contribution of this work; cite it as
the closest prior work. What BaFFLe does not do, and what this project therefore has to show:
- measure poisoning as a privilege escalation at the Zero-Trust gateway (wrongful grants; E7);
- treat the FL clients as Zero-Trust subjects: attribute the harm to a client, revoke its update
  privilege with a sequential test, and roll back on the ledger (E9);
- a floor that a federation poisoned from round 1 cannot move (E8b);
- an adaptive attacker played against the exact rule.
Related IIoT blockchain-FL work found (TrustFed, IEEE TII 2021, reputation on a smart contract;
DP2Guard 2025; SecureFed 2024/25; ZTA-FL arXiv 2025, TPM attestation + SHAP aggregation) does not
combine continuous device authorization with model provenance and rollback. A full literature
pass is still needed before the manuscript.

## E8b -- Statistical canary tolerance and a per-type floor (offline replay; done 2026-11-05)

**Decision (2026-11-05).** E8 finding 5 (false rejections from small canary types) and finding 3 (onset 1)
are the two weaknesses of the canary check. Both are addressed by a new rule, pre-registered
before any result:

**Rule** (`canary.StatGate`):
- A drop on type t fails the check only if it is material (>= delta = 0.05 of the type's canary
  rows, as in E8) AND significant: one-sided Fisher exact test of the candidate's counts against
  the reference's, p < 0.05 / (T + 1), Bonferroni over the T checked types and benign. The benign
  flag works the same way with delta_benign 0.01.
- `stat_slo` adds a per-type floor: in every round, including the warm-up, each checked type's
  Clopper-Pearson upper bound on detection (same alpha) must reach 0.5. This is the operator's
  policy ("each known attack type is detected at least half the time"), and no attacker can move
  it. Until a version passes, the gateway has no model (fail-closed).
- The verdict needs only counts, so anyone can re-check it from the ledger.
- Resulting tolerance: a type with 5,000 canary rows may drop 0.05, one with 60 rows 0.13, one with
  21 rows (WUSTL Backdoor, T = 4) 0.29-0.33. The floor for that type is 5 of 21 rows.

**Method.** The gate never changes training, so the rule is replayed offline on the 900
non-adaptive E8 runs (`src/replay_gates.py` -> `results/defense_replay/summary_long.csv`), scored
with each round's stored test metrics.
- Fidelity check: replaying the E8 Gate reproduces the stored promoted rounds in 900 / 900 runs.
- backdoor_adaptive runs are excluded: those attackers adapted to the E8 gate. The adaptive
  attacker against StatGate runs live in the E9 pilot.

**Table E8b-1. False rejections with no attack** (% of checked rounds 6-30).

| dataset | aggregator | E8 delta 0.05 | E8 delta 0.10 | stat (= stat_slo) |
|---|---|---|---|---|
| Edge | all | 0 | 0 | 0 |
| Forge | FedAvg | 7.2 | 0.8 | 0.8 |
| Forge | Median / Multi-Krum | 32.8 / 34.1 | 27.2 / 22.4 | 26.4 / 22.4 |
| Forge | FLTrust v2 | 76.8 | 74.4 | 76.8 |
| WUSTL | FedAvg / Median / Multi-Krum | 38.4 / 16.8 / 29.3 | 8.0 / 6.4 / 18.7 | 0 / 0 / 0 |
| WUSTL | FLTrust v2 | 53.6 | 35.2 | 0.8 |

**Table E8b-2. Backdoor success excess of the final deployed model, pp** (m = 3, FedAvg; best /
last / E8 d0.05 / stat / stat_slo).

| dataset | onset 1 | onset 11 |
|---|---|---|
| Edge | 0.0 / 97.7 / 35.2 / 35.2 / **8.8** | 0.0 / 97.7 / 0.0 / 0.0 / 0.0 |
| Forge | 61.3 / 98.7 / 98.7 / 98.7 / **7.6** | 0.0 / 98.7 / 0.1 / 0.1 / 0.1 |
| WUSTL | 50.2 / 82.8 / 49.8 / 53.5 / **29.8** | 7.4 / 78.6 / **3.3** / 22.8 / 22.8 |

Multi-Krum cells stay <= 4.2 pp under every rule.

**Findings.**
1. **The statistical tolerance removes the false rejections caused by small types.** WUSTL drops
   to 0-0.8% under every aggregator (from 17-54%), and Forge FedAvg to 0.8%. What remains on Forge
   under Median / Multi-Krum (22-26%) and FLTrust v2 (77%) is real churn on large types: those
   aggregators drop a different honest client each round, so the candidate genuinely loses
   detection for a round.
2. **The floor is the first rule that survives an attack from round 1.** Under FedAvg, the onset-1
   backdoor excess falls from 35.2 / 98.7 / 49.8 pp (E8) to 8.8 / 7.6 / 29.8 pp. On Forge, 3 of 5
   seeds never deploy a model: the system fails closed rather than deploy a backdoored one.
   Best-val deploys 61% backdoor success there. This is the first result where the canary beats
   best-val on backdoor success (cf. E8 finding 4). WUSTL stays at 29.8 pp because a 21-row type
   passes the floor at 5 of 21 rows detected.
3. **The cost is the small-type hole.** WUSTL onset 11 rises from 3.3 pp (E8) to 22.8 pp: a 21-row
   type may lose 6-7 rows before the drop becomes significant. A fixed delta and a statistical
   tolerance trade false rejections against attacker slack. On a 21-row canary type, no rule
   achieves both. The remedies are more canary rows for small types, or catching the attacker
   rather than the model (E9).
4. Label flip, onset 1, WUSTL: the floor keeps the inverted Multi-Krum seed out (excess -6.0 pp,
   versus 6.5 under E8), at the cost of 5-10 rounds without a model.

## E9 -- Zero trust for the FL clients: counterfactual attribution, revocation, rollback (C1+C2+C3; done 2026-11-05)

**Decision (2026-11-05).** The canary check (E8 / E8b) can only
refuse to deploy. It cannot stop the attack, and the training state stays poisoned. E9 closes the
loop the Zero-Trust way: submitting an update is a privilege that the client re-earns every round.
A client shown to cause a rejection loses it. The revocation goes on the provenance ledger, its
updates are dropped, and the training state rolls back to the registry head (or the genesis model).
This is what separates the work from BaFFLe (round rejection only).

**Instrumentation** (`src/train_fed.py`, `loo_types`): every round, the aggregate without client i
is scored on the canary for every admitted i (leave-one-out, LOO). Revoked clients still train
locally, so the random stream, and with it the honest clients' training, stays paired with the run
without revocation. With no revocation, training is bit-identical to E8 (checked on the WUSTL seed-42
smoke run: best / last / E8-gate backdoor success 0.326 / 0.953 / 0.326, as in E8).

**Pilot** (`--variant pilot`, seed 42 = design seed; 126 runs: 3 datasets x none / label_flip /
backdoor / backdoor_adaptive x onset 1 / 11 x FedAvg / Multi-Krum x m 1-3; nothing revoked). The
gates are e8, stat and stat_slo, and the adaptive attacker plays against stat_slo.
`scripts/e9_pilot_queue.sh`, 0 errors.

**Design history of the attribution rule (all on the seed-42 pilot, before any evaluation run).**
Every variant is kept: `results/e9/trust_calibration_v1..v3.json` and `calibrate_trust_v1.py.txt`.
- **v1: per-client CUSUM on max_t (LOO detection gain).** H = 1.25 x the clean-run maximum. Honest
  small-type noise (Forge dos_deauth; WUSTL Backdoor / CommInj, where one row is 4-5%) forced
  H = 2.04, so 11% of attackers were caught within 10 rounds.
- **v2: per-type scaling by clean-run noise** (q99, floor 2 rows). 37% caught, but 117 honest
  clients in attack runs would be revoked.
- **v3: minus the round median (peer comparison).** 38% caught, 144 false. The false alarms were
  not common-mode. They were sporadic spikes, often shared by an honest and a malicious client
  (Forge mitm_arp / mitm_ndp), and Multi-Krum's selection flipping when one client is left out.
- **v4: winsorised increments.** Best 41% caught, still 144 false.
  - Per-aggregator H made it worse: clean federations are quieter than honest clients under
    attack. Edge clean H ~ 0, and half of the honest clients would be revoked under attack.
  - Diagnosis: separability is real but relative. Per-client mean evidence gives an attacker-vs-honest
    AUC of 0.95-1.00 for the FedAvg backdoor, and attackers outrank every honest client in 100% of
    those runs. It is ~0.5 under Multi-Krum (attackers excluded, no signal) and 0.67-0.79 for label
    flip.
  - The problem is that honest evidence grows during an attack, so no clean-calibrated threshold
    works.
- **v5: peer-relative cumulative rule** (robust z of cumulative evidence >= 8 and gap >= 3; zero
  clean alarms). FedAvg: 24% caught, 2.3% false. Edge lost all separation under clipping.
- **v6 (evaluated): counterfactual attribution, triggered only by a rejected round.**
  `client_trust.CounterfactualTrust`:
  - When stat_slo rejects round r (from round 6), the server greedily finds the smallest exclusion
    set that makes the aggregate pass the same thresholds, up to the revocation budget of 4. The
    deficit is canary rows short of the thresholds plus benign rows over.
  - Those clients are implicated; a client implicated in 2 rejected rounds is revoked.
  - Single-exclusion replay on the pilot, FedAvg: 46 / 72 backdoor and adaptive attackers implicated
    twice, 0 honest in clean runs, 3 honest under backdoor attacks, 12 under label flip (Forge
    onset 1).
  - Multi-Krum: 6 / 72 attackers but 10 honest even in clean runs. Its 22% honest rejection churn
    makes counterfactual implication meaningless.
  - So revocation is a FedAvg mechanism. Robust aggregators already neutralise the attack; their
    runs are reported as a check.
  - Pre-registered: R_IMPL 2, START 6, MAX_REVOKED 4.
  - Why it works where v1-v5 failed: it asks a causal question ("would this round pass without
    you?") only when there is something to explain (a failed verdict). A statistical gate rarely
    fails on honest churn, so honest clients are rarely examined at all. The ledger records the
    counterfactual as the proof.

**Smoke run** (seed 42, m = 3, FedAvg; final backdoor success of the last-round model, E8 "last"
in brackets):
- Edge backdoor onset 1: 0.0% (97.7%), clients 3, 4 and honest 1 revoked.
- Edge backdoor onset 11: 0.8% (97.7%), 3 and 4 revoked.
- WUSTL backdoor onset 1 / 11: 37% (95%; clean ~28%), 3 and 4 revoked.
- WUSTL adaptive onset 1: 79%, only client 3 revoked. The attacker sits under the 21-row floor
  (5 / 21 rows detected passes), so most rounds are never rejected. Same small-type hole as E8b.

**Evaluation run** (launched 2026-11-05): `scripts/e9_trust_queue.sh`, `--variant trust`, 630 runs
(3 datasets x 7 attack/onset x FedAvg / Multi-Krum x m 1-3 x seeds 42-46). Seeds 43-46 are the
evaluation; seed 42 is reported apart. No-attribution baselines on the same seeds:
- E8 runs replayed (`results/defense_replay`) for the non-adaptive attacks;
- `scripts/e9_pilot_adaptive_queue.sh` (144 pilot-variant runs, adaptive vs stat_slo, seeds 43-46).
Summary: `src/summarize_e9.py` -> `results/e9/summary.md`.

**Completed** 2026-11-05: 630 / 630 trust runs and 144 baseline runs, 0 errors. Ledger chain
verified, and the revocations on it match the run's, in 630 / 630 runs; the gateway ran the registry
head in 630 / 630. All numbers below are from **evaluation seeds 43-46** (seed 42, the design seed,
is in `results/e9/summary.md`). "baseline" = the same federation without attribution (E8 runs
replayed; adaptive: pilot-variant runs).

**Table E9-1. Backdoor success excess of the final deployed model, pp** (FedAvg, m 1-3 pooled, 12
runs per cell).

| dataset | attack | onset | last-round FedAvg | best-val | E8 canary | stat_slo canary | **full system (E9)** |
|---|---|---|---|---|---|---|---|
| Edge | backdoor | 1 | 97.8 | 0.0 | 14.9 | 4.0 | **0.3** |
| Edge | backdoor | 11 | 97.8 | 0.0 | 0.0 | 0.0 | **0.1** |
| Edge | adaptive | 1 | 53.7 | 52.6 | 53.5 | 53.3 | **5.6** |
| Edge | adaptive | 11 | 3.7 | 0.0 | 3.6 | 3.6 | **1.3** |
| Forge | backdoor | 1 | 87.2 | 63.3 | 72.2 | 6.8 | **0.9** |
| Forge | backdoor | 11 | 91.9 | 2.2 | 0.1 | 1.6 | **1.0** |
| Forge | adaptive | 1 | 51.9 | 47.9 | 51.0 | 41.7 | **21.9** |
| Forge | adaptive | 11 | 4.8 | 2.3 | 3.8 | 3.8 | **3.4** |
| WUSTL | backdoor | 1 | 75.2 | 36.6 | 30.0 | 30.4 | **13.0** |
| WUSTL | backdoor | 11 | 67.1 | 8.9 | 5.4 | 23.8 | **11.4** |
| WUSTL | adaptive | 1 | 51.2 | 36.6 | 38.0 | 41.3 | **33.9** |
| WUSTL | adaptive | 11 | 24.8 | 10.3 | 4.8 | 24.8 | **22.7** |

Label flip: every cell of the full system is <= 2.3 pp (last-round FedAvg up to 14.1). The
adaptive attacker in the "baseline" columns plays against stat_slo, except in the "E8 canary" column
(E8 runs, where it played against the E8 gate). Under Multi-Krum every cell is <= 3.9 pp for every
practice, with or without attribution.

**Table E9-2. Revocations by the full system** (FedAvg, seeds 43-46, 24 attackers and 96 honest
clients per cell).

| dataset | backdoor on1 / on11 | adaptive on1 / on11 | label flip on1 / on11 | no attack |
|---|---|---|---|---|
| Edge: attackers revoked / honest revoked | 21 / 22; 0 / 0 | 17 / 14; 0 / 0 | 1 / 0; 0 / 0 | 0 honest |
| Forge | 23 / 21; **17** / 2 | 13 / 5; 7 / 2 | 10 / 7; 2 / 2 | 0 honest |
| WUSTL | 15 / 14; 0 / 0 | 8 / 3; 1 / 1 | 7 / 4; 4 / 0 | 0 honest |

First true revocation: round 7-9 for onset 1 and 12-14 for onset 11 (1-3 rounds after the
attack starts, given the round-6 start and two implications). Multi-Krum: no attacker revoked on
Edge / WUSTL (nothing to explain: Multi-Krum already excluded them). On Forge, 12 honest clients were
revoked in clean runs, as predicted from the pilot, so revocation must be off under robust
aggregators.

**Gateway** (target streams, cusum_sprt_mix, FedAvg, attack events granted %; full system with
E5c monotone / E5e balanced evidence vs E8 last-round FedAvg and best-val, both monotone):
- rho 1: Forge backdoor onset 1: 1.70 / **0.03** vs 81.1 (last) and 60.1 (best); WUSTL onset 1:
  0.65 / 0.30 vs 6.5 / 1.7.
- rho 0.2, backdoor onset 1: Edge 0.17 vs 38.7 / 0.02; Forge 2.30 / **1.80** vs 88.8 / 64.9;
  WUSTL 19.1 / **11.0** vs 88.9 / 48.9.
- rho 0.2, backdoor onset 11: Forge 2.33 / 1.32 vs 93.5 / 3.0; WUSTL 18.2 / 9.7 vs 80.4 / 6.5.
- rho 0.2, adaptive onset 1: Forge 23.3 / 13.9; WUSTL 45.1 / 23.5.
- False isolation (all streams, rho 1): one of 504 deployed-head cells above 1% (max 1.25%), with
  both evidence models.
Clean F1 is unchanged (to 0.0003) on every dataset.

**Findings.**
1. **Attribution and rollback clean the training itself, not only the deployment.** In the full
   system the last-round model is as clean as the deployed head (Table E9-1: "last" under trust
   equals the canary column to within 0.5 pp, except Forge onset 1: 2.3 vs 0.9). The canary checks
   of E8 / E8b can only freeze deployment while training stays poisoned; revoking the culprits
   lets the federation recover.
2. **First defence in this project that handles an attack from round 1 everywhere.** FedAvg
   onset-1 backdoor: Edge 0.3, Forge 0.9, WUSTL 13.0 pp (best-val 0.0 / 63.3 / 36.6; E8 canary
   14.9 / 72.2 / 30.0). Against the adaptive attacker from round 1 it cuts Edge from 53 to 5.6 and
   Forge from 42-52 to 21.9 pp.
3. **At onset 11 best-val is still as good or better on WUSTL** (8.9 vs 11.4 pp; gateway rho 0.2
   6.5 vs 9.7%), because best-val freezes on the pre-attack model, and the E8 canary (5.4) as well.
   The full system's WUSTL residual comes from the 21-row Backdoor canary: a backdoor that keeps
   >= 5 of 21 rows detected and stays inside the Fisher tolerance is never rejected, so it is
   never attributed. This is the same small-type limit as E8b finding 3, now the main limit of the
   system: a type can only be protected to the precision of its canary.
4. **False revocations are rare except in one setting.** No honest client was revoked in any clean
   FedAvg run (0 / 360 client-runs). Under attack: 0-4 per cell of 96 honest clients, except Forge
   backdoor onset 1 (17 / 96). There, the model poisoned from round 1 fails on several types at
   once, and the greedy exclusion set needed to pass includes honest clients. The cost is losing
   their data. The attack is still removed (0.9 pp) and clean F1 is not visibly affected.
5. **The adaptive attacker remains the hardest case, but it is boxed in.** Passing the check bounds
   it to the canary tolerance, and exceeding it gets it revoked (Edge 31 / 48, Forge 18 / 48 revoked).
   What gets through is set by the canary size: Edge 1.3-5.6 pp, Forge 3.4-21.9, WUSTL 22.7-33.9
   (onset 11 / 1).
6. **E5e's balanced evidence compounds with the defence at the gateway.** With the full system, it
   halves the target-stream grants at rho 0.2 (WUSTL backdoor 19.1 -> 11.0%, adaptive 45.1 -> 23.5%;
   Forge adaptive 23.3 -> 13.9%) with no added false isolation. Adopted as the primary evidence
   model for the final system; E5c stays reported.
7. **Scope.** Counterfactual revocation is a FedAvg mechanism. Under Multi-Krum it catches nothing
   that Multi-Krum has not already excluded and revokes honest clients on Forge (12 in clean runs).

**Final system for Stage 4/5** (decided on these results): FedAvg + stat_slo canary + counterfactual
revocation and rollback on the ledger + gateway with monotone_balanced evidence and Lorden's h.
Stated limits: canary types under ~60 rows (tolerance >= 0.13); attacks staying inside the
tolerance; Forge onset-1 false revocations.

## E5e -- Evidence-model variants for rare attack types (done 2026-11-05)

**Decision (2026-11-05):** run alongside E8, as labelled variants; E5c (monotone + Lorden)
stays the primary.

**Variants** (`closed_loop.Evidence`). Same E5d sweep (`src/operating_curves.py --llr ...`, output
`results/closed_loop/curves_<llr>/`), paired with E5d seed by seed.
- `monotone_balanced`: the attack likelihood is the equal-weight mixture of the per-type validation
  histograms, so a rare type's score region is not drowned by frequent types. It is still a
  density, so Lorden's bound holds.
- `monotone_floor`: LLR >= 0 for scores >= 0.5, so a flagged event never counts as benign evidence.
  This breaks E_0[e^LLR] <= 1 slightly.

**Question.** Does the rare Forge type (mitm_dhcp: 0% of its devices isolated in E5d) get
isolated, and at what false-isolation cost at Lorden's h?

**Completed** 2026-11-05: 2 x 15 runs, 0 errors. Summary `src/summarize_e5e.py` (reuses
`summarize_curves.load`, which now takes a results directory) -> `results/closed_loop/e5e_summary.md`.

**Table E5e-1. cusum_sprt_mix at Lorden's h = 10.82** (mean over seeds; monotone (E5d) /
balanced / floor).

| dataset | rho | false isolation % | attack events granted % | attackers isolated % |
|---|---|---|---|---|
| Forge | 1 | 0 / 0 / 0 | 3.56 / **0.10** / 3.56 | 94.9 / **100** / 94.9 |
| Forge | 0.5 | 0 / 0 / 0 | 6.51 / **1.76** / 6.49 | 86.0 / **99.6** / 86.5 |
| Forge | 0.2 | 0 / 0 / 0 | 6.06 / 4.88 / 6.06 | 80.0 / 89.3 / 80.1 |
| WUSTL | 1 / 0.2 | 0 / 0 / 0 | 0.06 / 0.06 / 0.06; 1.43 / 1.37 / 1.43 | 100; 99.1 / 99.5 / 99.1 |
| Edge | 1 / 0.2 | 0 / 0 / 0 | 0 / 0 / 0 | 100; 98.0 (all three) |

Worst seed, false isolation at Lorden's h: <= 0.12% for every mode and cell (Edge rho 0.5, the
same for all three). Time-to-isolation is unchanged (within 1.3 events).

**Findings.**
1. **The balanced mixture fixes the rare type.** Forge mitm_dhcp devices isolated at rho 1:
   0% -> **100%**; their attack events granted 62.1% -> 1.2%. Overall Forge grants at rho 1 fall
   3.56% -> 0.10%, with no false isolation at Lorden's h. Under the pooled histogram, mitm_dhcp's
   score region (41 training rows) was outweighed by benign mass. The equal-weight mixture gives it
   the same weight as every other type.
2. **It helps the other low-support Forge types when evidence is sparse.** At rho 0.2, devices
   isolated rise for dos_deauth 1.3% -> 49%, mitm_arp 3.2% -> 74% and malw_back 83.5% -> 100%.
   mitm_dhcp at rho 0.2 stays at 5.4%: one attack event in five is too little evidence for it.
3. **The floor variant changes nothing.** Only 38% of mitm_dhcp events score >= 0.5; the other 62%
   still carry negative LLR. Results equal E5d to within 0.1 pp.
4. **Edge and WUSTL are unaffected** (their attack types are separable already).
5. **Cost at equal realised false isolation** (oracle threshold, analysis only): to reach its lowest
   grants the balanced mode sits at a higher, still in-budget, false isolation (Forge 0.62% vs
   0.05%). Its grants there are 0.07% vs 3.51% at rho 1. At Lorden's h, the threshold the system
   actually uses, false isolation is 0 for both.
6. **Recommendation:** make monotone_balanced the primary evidence model
   for Stage 4/5. It is still a likelihood ratio of two densities, so the Lorden false-alarm bound
   keeps holding, and it needs only the per-type labels the server's validation split already has.
   E5c stays reported as the pre-registered baseline.

## E10 -- emulated device testbed (Stage 4, done 2026-11-06)

**Question.** Does the final system (E9) hold up end to end when device identity, event timing and
enforcement are real instead of i.i.d. draws, and what are the facts the simulation cannot give:
per-event detector latency and provenance-chain write latency on a real node?

**Method.** `stage4/` on the laptop (Docker Desktop, 12 CPU / 16 GB). Services: `eclipse-mosquitto`
broker; N device containers (each its own network identity and MQTT client id); a gateway container
(the policy enforcement point); `foundry`/anvil for the EVM ledger. The gateway loads the deployed
detector (the stat_slo canary registry head of a clean federated run -- the E9 final system) and
scores every event online, runs the per-device `cusum_sprt_mix` authoriser, grants/denies each
event and isolates compromised devices, and records every decision batch to the provenance ledger
tagged with the deployed model hash (C3). The last m devices are compromised at a mid-session onset
tau in [100, 300] with the backdoor target type and attack rate rho (C1).

Faithfulness is enforced by construction, not re-tuned: `stage4/export_testbed.py` copies the
monotone_balanced LLR table, the Lorden CUSUM threshold and the SPRT constants verbatim from
`closed_loop.py`; `stage4/common.DeviceAuthorizer` is a streaming rewrite of the `cusum_sprt_mix`
branch of `closed_loop.gate`, checked **bit-identical** to it (0 mismatches on 200 random 400-event
streams). Each event's content is a held-out TEST feature vector (the public tshark feature space
cannot be reconstructed from raw MQTT/Modbus packets -- see caveats); everything else is live.
Code: `stage4/{export_testbed,common,run_e10}.py`, `stage4/{gateway,device}/app.py`; summary
`src/summarize_e10.py` -> `stage4/results/summary.md`. Edge-IIoTSet, Forge-IIoT and WUSTL-IIoT,
seed 42, 10 devices (m = 2 compromised at a mid-session onset tau in [100, 300], except the clean
run), 500 events each (5000 per session). All three bundles exported on the server (GPU, code
version 31b0e7d91fce) so the deployed models match the E9 training environment.

**Table E10-1. Access-control outcomes, live sessions (full sweep, deployed round 30).**

| dataset | rho | wrongful grant | detection | tti median (events) | false iso | false reauth | lateral reach | benign deny |
|---|---|---|---|---|---|---|---|---|
| edge | clean | - | - | - | 0 | - | - | 0.48% |
| edge | 1.0 | 0 | 1.00 | 2 | 0 | 0 | 0 | 0.43% |
| edge | 0.5 | 0 | 1.00 | 5.5 | 0 | 0 | 0 | 0.43% |
| edge | 0.2 | 0 | 1.00 | 35 | 0 | 0 | 0 | 0.43% |
| forge | clean | - | - | - | 0 | - | - | 1.24% |
| forge | 1.0 | 0 | 1.00 | 2 | 0 | 0 | 0 | 1.15% |
| forge | 0.5 | 0 | 1.00 | 5.5 | 0 | 0 | 0 | 1.15% |
| forge | 0.2 | 0 | 1.00 | 35 | 0 | 0 | 0 | 1.15% |
| wustl | clean | - | - | - | 0 | - | - | 0% |
| wustl | 1.0 | 0.19% | 1.00 | 2 | 0 | 0 | 0.5 | 0% |
| wustl | 0.5 | 0.35% | 1.00 | 5.5 | 0 | 0 | 0.5 | 0% |
| wustl | 0.2 | 5.74% | 1.00 | 41 | 0 | 0 | 3.5 | 0% |

**Table E10-2. Facts the simulation cannot give** (5000 events per session; unconstrained gateway
on the 12-core laptop).

| | detector latency (ms/event, CPU) | ledger blocks | chain | write latency | hash-chain verified |
|---|---|---|---|---|---|
| memory ledger (12 runs) | 0.25 - 0.40 | 51 | hash chain | ~2.5 ms / session | yes (12/12) |
| edge rho 1.0, EVM (anvil) | 0.31 | 51 | real EVM node | 1.02 s median / batch | yes |

**Findings.**
1. **The final system transfers to the real closed loop.** Over real MQTT sessions with real
   identity and timing, every compromised device on all three datasets is detected and isolated
   (detection 1.0), no benign device is ever falsely isolated, and no compromised device is
   re-authorised -- the E5/E9 `cusum_sprt_mix` behaviour reproduced end to end. On edge and forge
   not one attack event is granted at any rate (lateral reach 0).
2. **Time-to-isolation tracks the attack rate as the Lorden bound predicts.** 2 events at rho 1.0,
   5.5 at 0.5, 35-41 at 0.2, identically across datasets. The conservative threshold trades speed
   for the zero-false-isolation guarantee; a low-rate attacker needs more events to accumulate
   evidence -- the E5d trade-off, now in wall-clock device sessions.
3. **WUSTL exposes the access-control cost of a weaker per-event detector -- the honest finding.**
   Isolation still always happens (detection 1.0), but WUSTL backdoor events that the clean detector
   scores below 0.5 are granted in the window *before* the device is isolated: 0.19% of attack
   events at rho 1.0, rising to 5.74% at rho 0.2, where isolation takes 41 events, and reaching
   0.5-3.5 other devices. This is the runtime face of WUSTL's weak Backdoor separation seen in E9
   (the 21-row canary). The sequential gate bounds the leak and still isolates, but does not zero it
   on WUSTL; a lower per-event threshold or the best-val model would trade benign denials for less
   pre-isolation leakage. Edge and forge separate the target type cleanly, so their leak is zero.
4. **No collateral isolation.** The benign per-event deny rate equals each detector's own benign
   flag floor (edge 0.43%, forge 1.15%, wustl 0%); Zero-Trust's continuous check isolates no benign
   device anywhere.
5. **Enforcement is local; provenance is asynchronous and verifiable.** The hash-chained ledger
   costs ~2.5 ms over a session. On a real EVM node (anvil, 2 s block time) decision batches confirm
   in a median of 1.02 s, written off the decision path, so enforcement latency is the detector's
   ~0.3 ms, not the chain's second. All 13 ledgers verified. C3 as designed: decide now, prove later.
6. **Detector cost is edge-realistic** (see E10-bench below): 0.25-0.40 ms/event unconstrained.
7. **The testbed result is not a single-seed artifact (R3).** Re-exporting the deployed bundle and
   rerunning the headline attacked config (m=2, rho 1.0) for seeds 43-46 reproduces it on every seed
   and dataset: detection 1.00, false-isolation and false-reauth 0 throughout, time-to-isolation
   2-4.5 events, and wrongful-grant 0 on most seeds (at most 0.2% on a few Forge/WUSTL seeds, lateral
   reach ≤ 0.5). Full per-seed table in `REVIEW_NOTES.md` (R3).

**E10-bench -- Pi-class constraint and arm64 readiness.** `run_e10.py --gateway-cpus 1.0
--gateway-threads 1` pins the gateway to one core and one BLAS thread (a conservative Raspberry-Pi
stand-in). The result is unchanged -- detection 1.0, 0 wrongful grants on 5000 events -- at **0.375
ms/event (~2 700 events/s on one core)**, barely above the unconstrained 0.25-0.40 ms because the
deployed MLP is tiny. So a single Pi-class core sustains the detector plus the continuous-auth gate
with large headroom. `Dockerfile.arm64` cross-builds for linux/arm64 (buildx + QEMU); the build
succeeds, but the default aarch64 torch wheel bundles CUDA libs (~2 GB, server-ARM), so the
Dockerfile pins the CPU index -- the final CPU-only image is to be confirmed natively on the Pi.

**Decision.** Stage 4 confirms the final system across all three datasets in the emulated testbed,
with WUSTL's pre-isolation leakage the one honest cost, consistent with E9. Next: the Pi-class
benchmark above, then Stage 5 moves the containers onto the laptop-as-edge and the Raspberry Pi when
it arrives. A packet-level firewall drop (routing device traffic through the gateway) is a possible
Stage 4b hardening.

## Planned
- **E10-bench (Pi-class + arm64); Stage 5 laptop-as-edge then Raspberry Pi.**

## Deviations and caveats to state in the manuscript

- The public datasets have no device field, so FL clients are partitioned by traffic type
  (Dirichlet), not by physical device.
- Scaling statistics are fitted on the pooled training split. They are federated-exact (sums and
  squared sums), so the result is identical to a secure-aggregated fit.
- Class weights come from summed client class counts, which reveals per-client label counts to
  the server.
- The FL simulation runs in-process with deterministic client order. Deployment uses Flower.
- Edge-IIoTSet has a 0.46-0.53% benign label-noise floor: identical packets carry both labels.
