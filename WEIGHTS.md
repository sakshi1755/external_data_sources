# PLFS — Weights / Multipliers

This file is the operational reference for applying the survey weight when
you tabulate PLFS estimates. It covers all three releases this repo handles
and reproduces the official rule from the **README** that ships with each
release plus the **Estimation Procedure** booklet.

> **Important:** the rule changed between CY2024 and CY2025. Use the table
> below to pick the right formula for your release.

## TL;DR — by release

| Release                          | Weight columns in record                       | Formula                                                                  |
| -------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------ |
| **Annual Jul23-Jun24** (213)     | `nss`, `nsc`, `mult`, `no_qtr`                 | Quarterly sub-sample: `mult/100`. Quarterly combined: `mult/IF(nss=nsc, 100, 200)`. **Annual: `mult/no_qtr`**. |
| **Calendar Year 2024** (254/251) | `nss`, `nsc`, `mult`, `no_qtr`                 | Same as Annual.                                                          |
| **Calendar Year 2025** (284)     | `mult`, plus `bstrm`/`zst`/`caph`/`smallh`/`nsc` for variance | **`mult/100`** — that's it. No NSS=NSC dance. No NO_QTR.                 |

`mult` is stored as integer hundredths in every release — the values you see in
`mult` already encode 2 decimal places. Divide by **100** to get the float weight,
then divide by the additional release-specific factor below to convert to a
population-unit weight.

## Annual (213) and Calendar 2024 (254/251)

Every record carries four pre-computed fields at the **end** of the row:

| field    | length | meaning                                                                                         |
| -------- | -----: | ----------------------------------------------------------------------------------------------- |
| `nss`    | 3      | # of FSUs surveyed in (sector × state × stratum × sub-stratum) **for one sub-sample**           |
| `nsc`    | 3      | # of FSUs surveyed in (sector × state × stratum × sub-stratum) **combined** across sub-samples  |
| `mult`   | 10     | Sub-sample-wise multiplier (raw weight, with 2 implied decimals — divide by 100 to get a float) |
| `no_qtr` | 1      | Count of contributing (sector × state × stratum × sub-stratum) cells across the 4 quarters      |

| You want…                                                                | Divisor              | Formula                  |
| ------------------------------------------------------------------------ | -------------------- | ------------------------ |
| **Quarterly, single sub-sample** (filter to one of `ss=1` or `ss=2` only) | `100`                | `weight = mult / 100 / 100`    |
| **Quarterly, both sub-samples combined**                                 | `100` if `nss = nsc` else `200` | `weight = mult / IF(nss=nsc, 100, 200) / 100` |
| **Annual** (Jul23-Jun24 or Jan-Dec 2024)                                 | `no_qtr` (per-record)           | `weight = mult / no_qtr / 100`                |

(The trailing `/100` strips the 2 implied decimals from `mult`.)

### Why it works that way

PLFS draws **two independent sub-samples** in every (sector × state × stratum
× sub-stratum) cell. Each sub-sample independently estimates the cell's total,
so combining them by simple addition would double-count — hence the `÷200`
when both are present, and `÷100` when only one happens to be in the cell
(`nss = nsc`). For an annual estimate the contributing cells are summed
across quarters and divided by the number of quarters that contributed,
which `no_qtr` gives you per-record.

## Calendar Year 2025 (284) — simpler

CY2025 is a redesign. The README states bluntly:

> Since the weight (MULT) is calculated at two places of decimal, the final
> weight will be: **Final Weight = MULT / 100**.

That's it. No sub-sample combination. No annual-vs-quarterly distinction.
Each record's `mult` is already the final calibrated weight to estimate the
full population for the calendar year.

CY2025 also introduces new fields for **design-based variance estimation**
(important if you're computing standard errors or relative-SE):

| field    | meaning                                                                              |
| -------- | ------------------------------------------------------------------------------------ |
| `bstrm`  | Basic stratum code. Starts with `D` → district is basic stratum; starts with `N` → NSS region (multiple smaller districts) is basic stratum. |
| `zst`    | Size of basic stratum (`bstrm`).                                                     |
| `caph`   | Total households listed in the SSS × FSU.                                            |
| `smallh` | Sample households actually surveyed in that SSS × FSU.                               |
| `nsc`    | FSUs surveyed in (sector × state × stratum × group × substratum) for the SSS panel.  |

For design-based RSE you need `zst`, `nsc`, `caph`, `smallh` (see CY2025 README
§B for the full procedure). The `Bstrm_file.xlsx` ships in catalog 284 if you
need to pull district-level estimates.

## On the formula a researcher shared

Some users (and Stata snippets) re-derive the `÷100 vs ÷200` divisor by
*grouping*, like:

```
mult / IF(Sector × Stratum × Sub-Stratum
        = Sector × Stratum × Sub-Stratum × Sub-Sample, 100, 200)
```

That formula has three issues you should know about before using it:

1. **It drops `state`.** The official cell key is `Sector × State × Stratum
   × Sub-Stratum` (PLFS stratum codes reset within each state, so dropping
   state collapses unrelated strata together).
2. **It re-does work the file already did.** PLFS already provides `nss`
   (one sub-sample's count) and `nsc` (combined count) per record. Just use
   `IF(nss = nsc, 100, 200)` — also more robust under filtering, since
   `nss/nsc` were computed on the full sample before any filter.
3. **It only gives the *quarterly combined* weight.** For an **annual**
   estimate, the divisor is `no_qtr`. The two are not interchangeable.
4. **It doesn't apply at all to CY2025** — CY2025 just uses `mult/100`.

## Worked examples

```python
import pandas as pd

# --- Annual (Jul23-Jun24) or Calendar 2024 ---
per = pd.read_csv("clean/calendar_2024/cperv1.csv", dtype=str)
for col in ["mult", "nss", "nsc", "no_qtr"]:
    per[col] = pd.to_numeric(per[col])

# Annual estimate (use mult / no_qtr)
per["weight_annual"] = per["mult"] / per["no_qtr"] / 100

# Quarterly combined estimate (filter to one quarter first)
q1 = per[per["qtr"] == "Q3"].copy()
q1["divisor"] = q1.apply(lambda r: 100 if r.nss == r.nsc else 200, axis=1)
q1["weight_q"] = q1["mult"] / q1["divisor"] / 100

# Sub-sample 1 only
q1_ss1 = q1[q1["ss"] == "1"].copy()
q1_ss1["weight"] = q1_ss1["mult"] / 100 / 100

# --- Calendar 2025 ---
per25 = pd.read_csv("clean/calendar_2025/cperv1.csv", dtype=str)
per25["mult"] = pd.to_numeric(per25["mult"])
per25["weight"] = per25["mult"] / 100   # done.
```

## Validation checks

- **Sum of annual weights** ≈ India's projected adult+child population for
  the survey year (~1.4 billion). MoSPI's published figures use this.
- **`nss <= nsc`** always (annual / CY2024). If you see `nss > nsc` it's a
  parse error.
- **`mult > 0`** for every record (no zero or negative weights).
- For sub-sample-wise tabulation in annual / CY2024, the **two sub-samples
  should give similar estimates** (their difference is the basis of variance
  estimates — see Estimation Procedure §3.8.1, §4.1.6).

## Sources

- [README.docx for annual 2023-24](raw/docs/README.docx)
- [README_Calendar_2024.docx](raw/docs_calendar_2024/README_Calendar_2024.docx)
- [README2025.docx](raw/docs_calendar_2025/README2025.docx)
- [Estimation Procedure_PLFS.pdf](raw/docs/EstimationProcedure_PLFS.pdf) — variance derivations
- Each release's data layout XLSX confirms `nss`, `nsc`, `mult`, `no_qtr` (or for CY2025: `mult`, `bstrm`, `zst`, etc.) at end-of-record.
