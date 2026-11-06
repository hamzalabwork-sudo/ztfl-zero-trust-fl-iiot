# Datasets

The three public IIoT datasets are **not redistributed** here. Download them from their publishers and
place the CSV files in `data/raw/` with exactly these names:

| Dataset | Source | File to place in `data/raw/` | Size (bytes) |
|---|---|---|---|
| Edge-IIoTset (Ferrag et al., 2022) | Kaggle: [edgeiiotset-cyber-security-dataset-of-iot-iiot](https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot), file `ML-EdgeIIoT-dataset.csv` from the "Selected dataset for ML and DL" folder | `ML-EdgeIIoT-dataset.csv` | 82,184,390 |
| IoTForge Pro (Kumar et al., IEEE IoT-J 2025) | IEEE DataPort, DOI [10.21227/c4z1-yc52](https://doi.org/10.21227/c4z1-yc52) (access requires an IEEE DataPort subscription) | `Forge_IIOT_Pro.csv` | 440,251,255 |
| WUSTL-IIoT-2021 (Zolanvari et al., 2021) | [Washington University in St. Louis](https://www.cse.wustl.edu/~jain/iiot2/index.html) | `wustl_iiot_2021.csv` | 409,800,698 |

## Verify you have the exact files

```bash
python scripts/check_data.py
```

The script compares each file's SHA-256 with the files used for every reported result:

```
53101fad091af20bee815860962a5016b802ee45d456a141042f6183094c3c1a  ML-EdgeIIoT-dataset.csv
173f33313cdbcfa848c09fd9c586dd3106b2df517b6717068379b852d538d243  Forge_IIOT_Pro.csv
f897b24578cc6fdeb3e7a0e9ff63efd5bbdc926a545abbda725e0dbb348c6bca  wustl_iiot_2021.csv
```

If a publisher has re-released a dataset, the checksum will differ; the cleaning pipeline still runs,
but numbers may not match the reported ones exactly.

## What happens to the data

`src/datasets.py` applies the versioned cleaning rules (`PREP_VERSION`): one canonical numeric parser
(which removes the "0" vs. "0.0" label leak found by the audit in E0), removal of identifier, timestamp
and checksum columns, IANA service categories for ports, and a signed-log plus z-score scaling that is
fit on the training split only. Each attack type is capped at 50,000 rows and the data are split
70/10/20 (stratified) per seed. Prepared splits are cached in `data/cache/`.
