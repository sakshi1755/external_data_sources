# PLFS — Cleaned Microdata + Code Maps

This repository converts official PLFS (Periodic Labour Force Survey) unit-level
fixed-width text files from MoSPI/NSO into per-table CSVs, with every coded
column joined to a corresponding code-map CSV. Use it as a starting point for
analysis (no transformations beyond column slicing and code lookups) or as a
load layer for a warehouse (BigQuery is the next step).

## Releases supported

| Release                      | Catalog | Reference period | Files                          | Contains                                             |
| ---------------------------- | :-----: | ---------------- | ------------------------------ | ---------------------------------------------------- |
| **Annual Jul23-Jun24**       |   213   | Jul 2023–Jun 2024 | `HHV1`, `HHRV`, `PERV1`, `PERRV` | First-visit + revisits → annual + quarterly CWS       |
| **Calendar Year 2024**       |   254   | Jan–Dec 2024      | `CHHV1`, `CPERV1`               | First-visit only, all 4 quarters of Panel 4 (Q3–Q6)   |
| **Calendar Year 2025**       |   284   | Jan–Dec 2025      | `CHHV1`, `CPERV1`               | First-visit only, simpler weight rule, new variance fields |

## Status

| Release          | Docs     | Layouts  | Code maps | Data fetched | Parsed CSVs |
| ---------------- | :------: | :------: | :-------: | :----------: | :---------: |
| annual_2023_24   | ✅       | ✅       | ✅        | ⏳ user step | ⏳          |
| calendar_2024    | ✅       | ✅       | ✅        | ✅           | ✅          |
| calendar_2025    | ✅       | ✅       | ✅        | ✅           | ✅          |

---

## Repository layout

```
PLFS/
├── README.md                      ← this file
├── WEIGHTS.md                     ← weights methodology, per release
│
├── raw/
│   ├── docs/                      ← annual 2023-24 official documentation
│   ├── docs_calendar_2024/        ← CY2024 docs (catalog 254)
│   ├── docs_calendar_2025/        ← CY2025 docs (catalog 284)
│   ├── data/                      ← annual 2023-24 unit-level (gitignored, fetch yourself)
│   ├── data_calendar_2024/        ← CY2024 unit-level (gitignored — too big for git)
│   ├── data_calendar_2025/        ← CY2025 unit-level (gitignored — too big for git)
│   └── external/                  ← non-PLFS sources (NIC 2008, NCO 2015 PDFs)
│
├── clean/
│   ├── annual_2023_24/
│   │   ├── layout/                ← per-file fixed-width schema (4 files)
│   │   └── {hhv1,hhrv,perv1,perrv}.csv  ← parsed (built on demand)
│   ├── calendar_2024/
│   │   ├── layout/                ← 2 files
│   │   └── {chhv1,cperv1}.csv     ← parsed
│   └── calendar_2025/
│       ├── layout/                ← 2 files
│       └── {chhv1,cperv1}.csv     ← parsed
│
├── codemaps/                      ← (code, description) lookup CSVs (release-agnostic — work for all)
│
└── scripts/
    ├── releases.py                ← release config (paths, byte totals, file lists)
    ├── build_layouts.py           ← writes clean/<release>/layout/*.csv from XLSX
    ├── build_codemaps.py          ← writes most codemaps/*.csv from instruction manual
    ├── parse_nco_2015.py          ← writes codemaps/nco_*.csv from NCO Vol-I PDF
    └── parse_plfs_data.py         ← slices fixed-width .txt → per-file CSV
```

---

## Usage

### One-time setup

Layouts and code maps don't need data — they're already committed:

```bash
python3 scripts/build_layouts.py    # rebuilds all releases' layouts
python3 scripts/build_codemaps.py   # rebuilds codemaps/ from instruction manual
python3 scripts/parse_nco_2015.py   # rebuilds codemaps/nco_*
```

### Fetch the data

Data is gated behind a free [microdata.gov.in](https://microdata.gov.in)
login. For each release you want:

| Release        | Catalog page                                                      | Data goes in                |
| -------------- | ----------------------------------------------------------------- | --------------------------- |
| Annual         | [catalog 213](https://microdata.gov.in/NADA/index.php/catalog/213) | `raw/data/`                 |
| Calendar 2024  | [catalog 254](https://microdata.gov.in/NADA/index.php/catalog/254) | `raw/data_calendar_2024/`   |
| Calendar 2025  | [catalog 284](https://microdata.gov.in/NADA/index.php/catalog/284) | `raw/data_calendar_2025/`   |

Click the catalog page → "Get Microdata" → log in → download → unzip the
`.txt`/`.TXT` files into the matching folder. (File-name casing varies; the
parser handles both.)

Or use the official Python client:

```bash
pip install mospi-unitdata
export MOSPI_API_KEY=...   # microdata.gov.in profile → API key
python -c "from MospiUnitdata import download_dataset; \
  download_dataset('DDI-IND-CSO-PLFS-2023-24', 'raw/data', '$MOSPI_API_KEY')"
```

### Parse

```bash
python3 scripts/parse_plfs_data.py                          # everything
python3 scripts/parse_plfs_data.py calendar_2025            # one release
python3 scripts/parse_plfs_data.py calendar_2024 --only chhv1
```

---

## Differences between the three releases

### Annual Jul-Jun vs Calendar Jan-Dec

Both have the **same Schedule 10.4** content (same blocks, same questions,
same coding). The differences are organisational:

- **Reference period** — Jul-Jun vs. Jan-Dec.
- **File structure**:
  - Annual: 4 files (first-visit `HHV1` + revisits `HHRV` separately).
  - Calendar: 2 files (`CHHV1` + `CPERV1`, **first-visit only**).
- **Sample composition** — different panels rotate in/out at different times.

The annual release is what MoSPI's official **Annual Report PLFS 2023-24**
tabulates against. Calendar is the freshest snapshot if you don't need
quarterly CWS panel data.

### Calendar Year 2025 — redesigned

CY2025 (catalog 284) is a structural redesign:

- **Simpler weight rule**: `MULT/100` only. No `nss/nsc/no_qtr` complexity.
- **New design-based variance fields**: `bstrm`, `zst`, `caph`, `smallh`,
  `nsc` — for proper RSE calculation at district / NSS-region level.
- **Month, not quarter**: identification key uses month (offset 11, 2 bytes)
  instead of quarter.
- **218-byte CHHV1** records (vs. CY2024's 129 bytes) — additional fields
  packed in.

See `raw/docs_calendar_2025/README2025.docx` and `FV_Data_Layout_2025.xlsx`
for the precise CY2025 layout.

### Quarterly bulletins (not in this repo)

MoSPI also publishes **quarterly urban-only CWS bulletins** (catalogs like
292, 291). Those have a smaller schedule (only Block 6 / CWS, urban only)
and aren't covered by this repo — add them under a new release config in
`scripts/releases.py` if you need them.

---

## Tables produced (after parsing)

### `annual_2023_24/`

| File              | Grain                                       | Rows (per MoSPI) | Bytes/row |
| ----------------- | ------------------------------------------- | ---------------: | --------: |
| `hhv1.csv`        | One row per **household × Visit-1**         |          101,920 |       126 |
| `hhrv.csv`        | One row per **household × Visit-{2,3,4}**   |          132,844 |        86 |
| `perv1.csv`       | One row per **person × Visit-1**            |          418,159 |       330 |
| `perrv.csv`       | One row per **person × Visit-{2,3,4}**      |          504,440 |       275 |

### `calendar_2024/`

| File              | Grain                                | Rows    | Bytes/row |
| ----------------- | ------------------------------------ | ------: | --------: |
| `chhv1.csv`       | One row per **household × Visit-1**  | 101,957 |       129 |
| `cperv1.csv`      | One row per **person × Visit-1**     | 415,549 |       333 |

### `calendar_2025/`

| File              | Grain                                | Rows      | Bytes/row |
| ----------------- | ------------------------------------ | --------: | --------: |
| `chhv1.csv`       | One row per **household × Visit-1**  |   270,472 |       218 |
| `cperv1.csv`      | One row per **person × Visit-1**     | 1,148,634 |       371 |

### Joining tables

**Household primary key** (annual & CY2024):
```
qtr × visit × sec × fsu_no × hg_sb × sss × hh_no
```

**Person primary key**: adds `srl_no` to the household key.

For CY2025, replace `qtr` with `month` (per the new layout).

> Source for keys: each release's README in `raw/docs*/`.

---

## Code-map index

Every coded column in the data tables joins to one of these CSVs on `code`.
**All codes are stored as zero-padded text** (so `01` joins, not `1`).

> Code maps are mostly release-agnostic — Schedule 10.4 codes are stable
> across PLFS releases. Where CY2025 introduced new fields (e.g., `bstrm`),
> they're noted below.

### Identifiers

| Code map                                                              | Used by columns           | Source                       |
| --------------------------------------------------------------------- | ------------------------- | ---------------------------- |
| [state.csv](codemaps/state.csv)                                       | `st`                      | Annual layout XLSX           |
| [district.csv](codemaps/district.csv)                                 | `(st, dc)`                | District_codes_PLFS_Panel_4  |
| [sector.csv](codemaps/sector.csv)                                     | `sec`                     | Vol I §1.4                   |
| [quarter.csv](codemaps/quarter.csv)                                   | `qtr`                     | README §A                    |
| [visit.csv](codemaps/visit.csv)                                       | `visit`                   | README §A                    |
| [sub_sample.csv](codemaps/sub_sample.csv)                             | `ss`                      | Vol I §1.2.12                |

### Block 3 — household characteristics

| Code map                                                                       | Used by             | Source         |
| ------------------------------------------------------------------------------ | ------------------- | -------------- |
| [household_type_rural.csv](codemaps/household_type_rural.csv)                  | `hh_type` if `sec=1` | Vol I §3.3.2  |
| [household_type_urban.csv](codemaps/household_type_urban.csv)                  | `hh_type` if `sec=2` | Vol I §3.3.2  |
| [religion.csv](codemaps/religion.csv)                                          | `religion`          | Vol I §3.3.3   |
| [social_group.csv](codemaps/social_group.csv)                                  | `social_grp`        | Vol I §3.3.4   |

### Block 4 — demographics

| Code map                                                                       | Used by             | Source                |
| ------------------------------------------------------------------------------ | ------------------- | --------------------- |
| [membership_status.csv](codemaps/membership_status.csv)                        | `whether_member`    | Vol I §3.4.3 (revisit only) |
| [relation_to_head.csv](codemaps/relation_to_head.csv)                          | `rel_head`          | Vol I §3.4.4          |
| [sex.csv](codemaps/sex.csv)                                                    | `sex`               | Vol I §3.4.5          |
| [marital_status.csv](codemaps/marital_status.csv)                              | `mar_st`            | Vol I §3.4.7          |
| [general_education.csv](codemaps/general_education.csv)                        | `gen_edu`           | Vol I §3.4.9          |
| [technical_education.csv](codemaps/technical_education.csv)                    | `tedu_lvl`          | Vol I §3.4.10         |
| [vocational_training_received.csv](codemaps/vocational_training_received.csv)  | `voc`               | Vol I §3.4.13         |

### Block 4.1 — formal vocational/technical training

| Code map                                                                       | Used by              | Source             |
| ------------------------------------------------------------------------------ | -------------------- | ------------------ |
| [vt_field_of_training.csv](codemaps/vt_field_of_training.csv)                  | `vt_field`           | Vol I §3.4.1.3     |
| [vt_duration.csv](codemaps/vt_duration.csv)                                    | `vt_dur`             | Vol I §3.4.1.4     |
| [vt_type_of_training.csv](codemaps/vt_type_of_training.csv)                    | `vt_type`            | Vol I §3.4.1.5     |
| [vt_funding_source.csv](codemaps/vt_funding_source.csv)                        | `vt_fund`            | Vol I §3.4.1.6     |

### Block 5.1 / 5.2 / 6 — economic activity

| Code map                                                                       | Used by                                         | Source                  |
| ------------------------------------------------------------------------------ | ----------------------------------------------- | ----------------------- |
| [activity_status.csv](codemaps/activity_status.csv)                            | `sts_pas`, `sts_sas`, `aps_cws` & per-day CWS   | Vol I §3.5.1.7          |
| [enterprise_type.csv](codemaps/enterprise_type.csv)                            | `ent_pas`, `ent_sas`, `ent_cws`                 | Vol I §3.5.1.16         |
| [no_of_workers.csv](codemaps/no_of_workers.csv)                                | `wkr_pas`, `wkr_sas`, `wkr_cws`                 | Vol I §3.5.1.17         |
| [job_contract.csv](codemaps/job_contract.csv)                                  | `jc_pas`, `jc_sas`                              | Vol I §3.5.1.19         |
| [paid_leave_eligible.csv](codemaps/paid_leave_eligible.csv)                    | `pl_pas`, `pl_sas`                              | Vol I §3.5.1.20         |
| [social_security.csv](codemaps/social_security.csv)                            | `ss_pas`, `ss_sas`                              | Vol I §3.5.1.21         |
| [product_destination.csv](codemaps/product_destination.csv)                    | `prdest_pas`                                    | Vol I §3.5.1.22         |

### Industry & occupation (external)

| Code map                                                | Used by                                             | Source       |
| ------------------------------------------------------- | --------------------------------------------------- | ------------ |
| [nic_division.csv](codemaps/nic_division.csv)           | `aind_*` (2-digit)                                  | NIC 2008 XLSX |
| [nic_group.csv](codemaps/nic_group.csv)                 | (3-digit aggregation)                                | NIC 2008 XLSX |
| [nic_class.csv](codemaps/nic_class.csv)                 | (4-digit aggregation)                                | NIC 2008 XLSX |
| [nic_subclass.csv](codemaps/nic_subclass.csv)           | `ind_*` (5-digit)                                    | NIC 2008 XLSX |
| [nco_division.csv](codemaps/nco_division.csv)           | (1-digit)                                            | NCO 2015 Vol-I |
| [nco_subdivision.csv](codemaps/nco_subdivision.csv)     | (2-digit)                                            | NCO 2015 Vol-I |
| [nco_group.csv](codemaps/nco_group.csv)                 | `ocu_*` (3-digit)                                    | NCO 2015 Vol-I |
| [nco_family.csv](codemaps/nco_family.csv)               | (4-digit aggregation)                                | NCO 2015 Vol-I |
| [nco_full.csv](codemaps/nco_full.csv)                   | (8-digit detailed; with NCO 2004 mapping)            | NCO 2015 Vol-I |

---

## Weights

See [WEIGHTS.md](WEIGHTS.md). One-line summary per release:

```
annual_2023_24 + calendar_2024:
  weight_quarterly_subsample = mult / 100 / 100
  weight_quarterly_combined  = mult / IF(nss = nsc, 100, 200) / 100
  weight_annual              = mult / no_qtr / 100

calendar_2025:
  weight = mult / 100   (no NSS=NSC dance, no NO_QTR)
```

The `/100` at the end strips the 2 implied decimals from `mult`.

---

## Sources

- **PLFS catalogs (NADA portal):**
  - [213 — Annual Jul23-Jun24](https://microdata.gov.in/NADA/index.php/catalog/213)
  - [254 — Calendar 2024](https://microdata.gov.in/NADA/index.php/catalog/254)
  - [284 — Calendar 2025](https://microdata.gov.in/NADA/index.php/catalog/284)
- **MoSPI annual report 2023-24:** https://www.mospi.gov.in/annual-report-periodic-labour-force-survey-plfs-2023-24
- **NIC 2008 (XLSX):** https://www.mospi.gov.in/sites/default/files/main_menu/national_product_classification/NIC_2008.xlsx
- **NCO 2015 Vol-I (PDF, code structure):** https://www.ncs.gov.in/Documents/National%20Classification%20of%20Occupations%20_Vol%20I-%202015.pdf
- **`mospi-unitdata` Python client:** https://pypi.org/project/mospi-unitdata/

## License

PLFS data are released by MoSPI under their standard terms (research use
only, citation required). The scripts in this repo are MIT.
