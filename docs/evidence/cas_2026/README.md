# NSE Closing Auction Session (CAS) evidence — retrieved 2026-10-01

Supports `docs/protocols/ORB_v1_verification_20261001.md` Part 1. Checksums are in `SHA256SUMS`.

| File | Source |
|---|---|
| `SEBI_circular_CAS_20260116.pdf` | SEBI circular HO/47/11/11(3)2025-MRD-POD2/I/2765/2026 (16 Jan 2026), https://www.sebi.gov.in/sebi_data/attachdocs/jan-2026/1768576287344.pdf |
| `nse_fo_mktlots_retrieved_20261001.csv` | https://nsearchives.nseindia.com/content/fo/fo_mktlots.csv (NSE F&O underlyings and lot sizes; OCT-26 onward) |
| `bhavcopy_YYYYMMDD_nifty50_frozen.csv` | NSE UDiFF CM bhavcopy, https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip. Filtered to EQ rows of the 50 frozen symbols. All dates are before 2026-10-01. |
| `verify_exit_bar_semantics_output.txt` | Output of `scripts/verify_exit_bar_semantics.py` |

**Broker pages** (not archived; quoted in the verification document):
- Zerodha support, "What is SEBI's Closing Auction Session (CAS), and how does it affect you?"
- Upstox announcement, "Important update: Intraday square-off timings are changing".
