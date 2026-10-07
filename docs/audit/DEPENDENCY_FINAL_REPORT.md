# Dependency report and reproducibility contract — finding F-06 (2026-10-07)

Files: `release/s2_mom_v1/environment.yml`, `release/s2_mom_v1/conda-osx-arm64.lock`, `release/s2_mom_v1/ENVIRONMENT.json`, `requirements-lock.txt`.
Code: `src/registry/integrity.py::environment_report`, `src/registry/experiments.py::environment`, step 1 of the reproduction.
Tests: `tests/test_environment.py` (9).

## 1. The official reproducibility contract

| Question | Answer |
|---|---|
| Official supported environment | **Conda, platform `osx-arm64`** (macOS on Apple silicon), packages from the Anaconda `defaults` channel |
| Exact Python version | **3.13.5**, build `h2eb94d5_100_cp313` |
| Exact package versions | numpy **2.1.3** (`py313h7c57ca2_0`), pandas **2.2.3** (`py313hcf29cfe_0`), scipy **1.15.3** (`py313hd7edaaf_0`), pyarrow **19.0.0** (`py313h313beb8_1`, arrow-cpp 19.0.0 `h0b7d223_2`), libopenblas 0.3.29 (`hea593b9_0`), python-dateutil 2.9.0.post0, pytz 2024.1, tzdata 2025.2, six 1.17.0 |
| Installation mechanism | `conda create -n s2mom --file release/s2_mom_v1/conda-osx-arm64.lock` (explicit list of all 90 packages with URL and MD5 — byte-exact), or `conda env create -n s2mom -f release/s2_mom_v1/environment.yml` (exact builds of Python and the numerical packages; conda resolves the rest) |
| Is pip installation supported? | **No.** `requirements-lock.txt` lists the same version numbers for reference and for the verifier. It says in its first lines that it is not the installation contract. |
| Is the pip failure a release blocker? | **No** for the integrity of the registered results: no number depends on pip, and the failure is closed (the reproduction refuses to run). It **was** a documentation defect — the first version of the lock file suggested `pip install` — and that is corrected. It remains a limit for readers on other platforms (section 4). |

## 2. Why the pinned SciPy failed under pip — verified by inspection

1. `pip install scipy==1.15.3` on this machine (macOS 27.0, arm64, Python 3.13.5) installs the wheel tagged `cp313-cp313-macosx_14_0_arm64`.
2. `import scipy.stats` fails while loading `scipy/sparse/linalg/_propack/_spropack.cpython-313-darwin.so`:
   `dlopen … section '__DATA/__thread_bss' has a zero-fill section type, but offset field is not zero`.
3. `otool -l` on that file shows the section `__thread_bss` (flags `0x12`, zero-fill thread-local) with file `offset 115000`. A zero-fill section has no bytes in the file, so its offset should be 0. The macOS 27 loader rejects the library for this.
4. The Conda build of the same SciPy version (`py313hd7edaaf_0`, minimum OS 11.1) has `offset 0` in the same section and loads.
5. So this is a packaging property of that one PyPI wheel meeting a stricter loader. It is not a version conflict and not a defect of the lab's code. Whether the wheel loads on older macOS versions, and the Linux and Windows wheels, were **not tested**.

The versions were not changed to get around it.

## 3. What was run, and the result

| Run | Environment | Result | Label |
|---|---|---|---|
| A | registered interpreter, `/opt/anaconda3` base, normal shell | PASS | PROVEN BY TEST |
| B | registered interpreter, empty process environment (`env -i`, `-E -s -B`, other directory) | PASS | PROVEN BY TEST (`test_reproduction_command_in_a_clean_process`) |
| C | fresh venv, `pip install` of the pins | FAIL at "dependency installed but not loadable" — fails closed | PROVEN BY TEST (manual run; the mechanism is unit-tested) |
| D | **clean Conda environment created from `environment.yml`** in a scratch directory, empty process environment | **PASS**, exit 0, same largest difference 6.7e-14 | PROVEN BY TEST (manual run 2026-10-07; report in `docs/audit/remediation/reproduction_report_clean_conda_env.json`) |
| E | another machine, another OS or CPU | not run | UNVERIFIED |

Run D is the demonstration that the registered environment can be reconstructed from the specification. The explicit lock file was written from that environment. Creating it downloaded some transitive packages into the Conda package cache of this machine; the scratch environment itself was removed afterwards.

Between run A and run D the recomputed numbers are not bit-identical: 11 of the 117 compared quantities differ in the last digits (all below 1e-13), although Python and the four numerical packages are the same builds. The transitive libraries differ. This is why the contract is a tolerance, not byte equality.

## 4. What a third-party researcher must do

1. Use a Mac with Apple silicon (the only platform shown to work). On any other platform the steps below are untested; the reproduction will say that the environment differs and will still compare at the same tolerance.
2. Install Conda (Miniconda is enough).
3. Clone the repository.
4. `conda create -n s2mom --file release/s2_mom_v1/conda-osx-arm64.lock` and `conda activate s2mom`.
5. Obtain the data archive `s2-mom-v1-data-baa0b47040101031.tar` and run `python3 scripts/release_archive.py materialize <tar>`.
6. `python3 scripts/reproduce_s2_mom_v1.py` — exit code 0 and the line `REPRODUCTION OF S2-MOM-v1: PASS [full reproduction]`.

Numerical acceptance, as enforced by the command: absolute difference ≤ 1e-9 for returns, statistics and p-values; ≤ 1e-12 for step E costs; counts, labels and portfolio membership exactly equal.

Two things in this list do not exist yet outside this laptop: the repository (not pushed) and the archive (not packed). See F-01.

## 5. What was changed in the repository

1. `release/s2_mom_v1/environment.yml` and `conda-osx-arm64.lock` — the contract.
2. `release/s2_mom_v1/ENVIRONMENT.json` — tested environment, with a `contract` block that states everything in section 1 and 3 in machine-readable form.
3. `requirements-lock.txt` — exact `==` pins; header now says "THIS FILE IS NOT THE INSTALLATION CONTRACT".
4. `requirements.txt` — two comment lines: it is the loose list of the local app, not the research environment.
5. `REPRODUCIBILITY.md` — the procedure of section 4.
6. Registry anchors: line 60 anchored the first version of the two environment files; line 61 (`environment_files_sha256_v2`) anchors the four corrected files and says in its reason that it supersedes line 60 for verification and why. Line 60 stays in the registry. No package version differs between the two.
7. `environment()` in the registry module records scipy, pyarrow, platform and architecture for any future registration.
8. The verifier reports Python version, OS, architecture, each dependency version, missing packages, version mismatches, libraries that are installed but cannot be loaded, and optimised mode. A test parses the research code and fails if an import appears that is not pinned; another checks that the exact builds in `environment.yml`, the lock file and `ENVIRONMENT.json` agree.

## 6. Is the recorded environment the one of the registered runs?

Partly proven. The run-time registry records of 2026-10-05 and 2026-10-06 contain Python 3.13.5, pandas 2.2.3 and numpy 2.1.3. scipy was first recorded at run time on 2026-10-07 (C2 run: 1.15.3). pyarrow was first recorded during remediation. The anchors say "observed after the fact" in their own text. That the base environment did not change between 5 and 7 October is plausible (the registered numbers are reproduced in it) but cannot be proved afterwards. Label: SUPPORTED BY HASH for the files, VERIFIED BY INSPECTION for the versions, UNVERIFIED for "unchanged since the runs".

## 7. Risks that remain

1. **The lab still runs in the shared Anaconda base environment.** A `conda update` there changes the study's environment. The verifier will show it at the next reproduction; nothing prevents it. Recommended: do the daily work in the dedicated `s2mom` environment.
2. Library versions are not part of the registered code hashes (F-09). The numerical comparison is the control.
3. Byte-identity checks inside the frozen code (sensitivity mode, rebuild-and-compare of Stage 2 and 3) can refuse in a different environment even when the numbers agree (F-29). The reproduction uses the tolerance instead.
4. One platform only (run E).

## 8. Status

F-06: **FIXED + REGRESSION PROTECTED.**
N-01 (found during remediation): the pip route is unsupported and documented as such; the Conda rebuild is demonstrated; a second machine is not — **OPEN (P3)**.
