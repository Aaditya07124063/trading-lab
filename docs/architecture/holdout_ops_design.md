# ORB v1 holdout operations — proposed architecture (DESIGN ONLY, not implemented)

**Date:** 2026-10-03
**Scope:** keep the frozen ORB v1 prospective holdout collecting unattended until 250 standard NSE sessions, isolated from development and from ResQNet.
**Does not change:** the frozen protocol, ORB rules, evaluator methodology, data or universe.

## 0. Current state (inspected, not assumed)

| Item | Found |
|---|---|
| Collector | `update_intraday.py` (append-only; raw snapshot + checksum per fetch; `collection_log.jsonl`; existing bars always win; overlap must agree) |
| Scheduling | macOS launchd `com.tradinglab.intraday-collector` → `scripts/collect_intraday.sh`, 18:30 IST weekdays |
| Python | `/opt/anaconda3`, `requirements.txt` unpinned |
| Docker / compose / CI / deploy files | **none** |
| Status | `scripts/holdout_status.py` (structure only; no performance) |
| Holdout gate | `load_intraday(holdout_protocol=...)` opens holdout bars whenever `ORB_v1.md` reads FROZEN, which is **true since 2026-10-03** → any code could open the holdout today |
| Dev dashboard | `server.py` (FastAPI): intraday endpoints use the default loader (holdout dropped). `/api/add` + `/api/backtest` can download and backtest daily data up to today (post-cutoff price data) |
| Remote | GitHub `origin` holds only the initial commit; visibility unknown |
| ResQNet / Hostinger | nothing in this repo; **details needed from you (§H)** |

## A. Proposed architecture

**One rule: one canonical writer, read-only everything else.**

```
                   ┌─────────────── Hostinger VPS ───────────────┐
 Yahoo (15m) ─────►│ tradinglab-collector  (docker, one-shot)     │
 NSE archives ────►│   update_intraday.py (unchanged)             │
 (bhavcopy, index) │   → /srv/tradinglab/state  (bind dir)        │
                   │      data/india/*.csv  (append-only)         │
                   │      data/raw/yahoo/** (immutable snapshots) │
                   │      data/raw/collection_log.jsonl           │
                   │      data/raw/manifest.jsonl                 │
                   │   → holdout_status.py → status/status.json   │
                   │                        → status/index.html   │
                   │ tradinglab-status (docker, static, read-only)│
                   │   serves status/ on 127.0.0.1:8787 only      │
                   │ systemd timers (host) → start the one-shots  │
                   │ backup timer → /srv/tradinglab/backups (tar) │
                   └──────────────┬───────────────────────────────┘
                                  │ rsync over SSH (pulled BY the Mac; VPS holds no
                                  ▼                 Mac or GitHub credentials)
                   ┌──────────────── Mac (research) ─────────────────┐
                   │ holdout_mirror/  (verified copy of VPS state)    │
                   │ trading-lab repo: development, Stage 2           │
                   │ FINAL evaluation (only when authorised) runs     │
                   │ here, on the verified mirror                     │
                   └──────────────────────────────────────────────────┘
```

**Components**
1. **Collector (VPS, canonical writer).**
   - The **unchanged** `update_intraday.py` runs in a one-shot container started by host systemd timers.
   - It doesn't run as a long-lived daemon, so there is no scheduler code to maintain.
2. **Status layer** (`holdout_status.py`, extended).
   - Runs after every collection and writes `status.json` plus a static `index.html`.
   - Fields are **whitelisted**:
     - protocol status (FROZEN);
     - holdout start (2026-10-01);
     - sessions collected / 250 and remaining;
     - latest successful collection;
     - data health (last-run failures, STALE flag);
     - untradable stock-sessions (count + reasons);
     - whether the 2027 calendar is stored;
     - `READY FOR EXPLICIT FINAL EVALUATION` (yes/no).
   - It imports **no** strategy, portfolio or inference code. A test enforces both the import ban and the key whitelist.
3. **Final-evaluation gate.** A single choke point: the holdout branch of `load_intraday`, which every holdout read must pass.
   - The gate requires **both** `ORB_v1.md` FROZEN **and** a committed authorisation file `docs/protocols/ORB_v1_holdout_authorization.md`, written by you when you authorise the run.
   - Stage 2, dashboards and any accidental call are therefore blocked too.
   - At session 250 the status reads `READY FOR EXPLICIT FINAL EVALUATION`. **Nothing runs automatically.**
   - **⚠ Needs your approval:** this adds a stricter refusal to `src/intraday/data.py`. It does not touch the protocol or the evaluator methodology. If you prefer not to touch shared code, the fallback is a check in the evaluator only, which would **not** block other callers.
4. **VPS image excludes evaluators.** `.dockerignore` drops `evaluate_orb_v1.py`, `run_*.py`, `server.py`, `paper_bot.py`, `results/`, `docs/` and tests. The VPS physically cannot evaluate or serve a dashboard.
5. **Mac.**
   - Pulls the VPS state into `holdout_mirror/` and verifies every working file against the VPS `collection_log` `file_sha256_after`.
   - During the transition, keeps its own launchd collector as a **secondary** copy in its own directory (never auto-merged).
   - All development and Stage 2 happen here.

## B. Files and services to add

| File | Purpose |
|---|---|
| `deploy/vps/Dockerfile` | `python:3.12-slim`; pinned `requirements-collector.txt` (pandas, yfinance, numpy); non-root UID 10001; copies `src/`, `update_intraday.py`, `scripts/holdout_status.py`, `config/`, `data/metadata/` |
| `deploy/vps/.dockerignore` | Excludes evaluators, runners, server, paper bot, results, tests, docs, `.git` |
| `deploy/vps/requirements-collector.txt` | Exact pinned versions (copied from the Mac environment) |
| `deploy/vps/compose.yaml` | Project name `tradinglab`. Services: `collector` (one-shot) and `status` (`python -m http.server`, read-only mount, `127.0.0.1:8787`). Own network; no other ports; `read_only: true`, `cap_drop: [ALL]`, `no-new-privileges`, `restart: unless-stopped` (status only) |
| `deploy/vps/systemd/tradinglab-collect.service` + `.timer` | `docker compose run --rm collector`, Mon–Fri **13:00, 15:00, 17:00 UTC** (= 18:30 / 20:30 / 22:30 IST) and **03:00 UTC** next morning (08:30 IST). `Persistent=true` catches runs missed during a reboot. Idempotent: extra runs add 0 bars |
| `deploy/vps/systemd/tradinglab-backup.service` + `.timer` | Daily `tar` of state metadata + new raw snapshots → `/srv/tradinglab/backups/YYYY-MM-DD.tar.gz` (no deletion) |
| `deploy/vps/collect.sh` | Container entrypoint: run collector → run status → optional dead-man ping (`HC_PING_URL` from env; skipped if unset) |
| `deploy/vps/README.md` | Install, verify, recover, uninstall. All commands scoped to `tradinglab` |
| `scripts/holdout_status.py` (extend) | Add the fields above; `--html`; STALE logic from the stored NSE calendar |
| `scripts/pull_holdout_mirror.sh` (Mac) | `rsync -a --ignore-existing` for immutable raw snapshots; `rsync -a` for working files and logs into `holdout_mirror/`, then checksum verification against the VPS log; **never** writes into the repo's `data/` |
| `src/intraday/data.py` (+ test) | Authorisation-file requirement in the holdout gate **[approval needed]** |
| `tests/test_holdout_ops.py` | Status whitelist / no-performance imports; gate refuses without authorisation; status READY logic on synthetic logs |
| `.env.example` (no values) | `HC_PING_URL=`, `TZ=Asia/Kolkata`. The real `.env` lives only on the VPS (chmod 600, git-ignored) |

**Not added (YAGNI):** a database (files plus manifests are the store), message queues, a web framework for status, CI/CD, Kubernetes, a reverse proxy.

## C. Data flow

```
weekday 18:30/20:30/22:30/08:30 IST
  systemd timer ─► docker run collector (non-root, read-only rootfs, rw bind /srv/tradinglab/state)
     update_intraday.py
       fetch Yahoo 15m ─► data/raw/yahoo/<ds>/<ts>.csv  (new file; never overwritten)
                        ─► manifest.jsonl  (+sha256)
       append-only merge ─► data/india/<SYM>m15.csv (existing bars win; overlap must agree,
                                                    else REJECT + log)
       every attempt   ─► collection_log.jsonl (OK / OK_NO_NEW_BARS / FAILED / REJECTED, file_sha256_after)
     holdout_status.py ─► status/status.json, status/index.html  (structure only)
     curl HC_PING_URL  (only when the run succeeded; optional)
  status container ─► serves status/ on 127.0.0.1:8787 ─► you: ssh -L 8787:127.0.0.1:8787 vps
daily backup timer ─► backups/YYYY-MM-DD.tar.gz
Mac (manual or launchd weekly) ─► rsync pull ─► holdout_mirror/ ─► checksum verify
session 250 + your written authorisation ─► (Mac) commit authorization file
         ─► sync mirror into repo data (data commit) ─► python3 evaluate_orb_v1.py (once)
```

## D. Security and isolation plan (vs ResQNet)

**Separation**

| Layer | Trading Lab | Shared with ResQNet? |
|---|---|---|
| Unix user | `tradinglab` (no sudo), member of `docker` | No |
| Directory | `/srv/tradinglab/{app,state,backups}` | No |
| Compose project | `-p tradinglab`, separate file | No |
| Network | `tradinglab_default` bridge; no links to other networks | No |
| Volumes | Host bind dirs under `/srv/tradinglab` only | No |
| DB | none | No |
| Env | `/srv/tradinglab/app/.env` (600) | No |
| Ports | none public; `127.0.0.1:8787` status only (SSH tunnel) | No |
| systemd units | `tradinglab-*.service/.timer` | No |
| Deployment | manual `rsync` of a pinned commit + `docker compose build` by the `tradinglab` user | No shared CI/workflow |
| Reverse proxy / TLS | not used | No |

**Hardening**
- No secrets in git: Yahoo and NSE need none. The only optional secret is the dead-man URL, kept in `.env`.
- The VPS holds no GitHub or Mac credentials; the Mac pulls.
- Containers: non-root, `read_only`, `cap_drop: ALL`, `no-new-privileges`, outbound-only network, memory and CPU limits.
- Firewall: no new inbound rules. Verify ResQNet's existing rules are untouched (`ufw status` before and after).
- The status page shows operational fields only. No strategy, return or statistic code exists in the image.

## E. Failure and recovery plan

| Failure | Detection | Automatic response | Manual recovery (methodology unchanged) |
|---|---|---|---|
| Transient Yahoo/network error | `FAILED` row in the log | Next scheduled run (≤2 h later; 4 runs/weekday); adaptive lookback refills missed bars | none |
| Yahoo blocks VPS IP (datacenter) | Repeated `FAILED`; status STALE | Mac secondary collector keeps an independent copy | Switch canonical back to the Mac; data merged by the same append-only, overlap-must-agree rule |
| Conflicting overlap | `REJECTED` (never merged) | Raw snapshot kept | Investigate; nothing is overwritten |
| VPS reboot | — | Docker restarts `status`; timers `Persistent=true` run missed jobs | none |
| VPS disk full / VPS lost | Status stale; dead-man alert | — | Restore from the Mac mirror + daily backups. Gaps longer than about 60 days (Yahoo retention) become untradable stock-sessions under frozen §5.3 |
| Stale collection | `status.json` STALE = no successful run after the latest expected session's 22:30 IST run | Dead-man service emails you (if configured) | Run `collect.sh` manually; idempotent |
| Malformed data | Frozen §5.4 classification in status | — | none; reported, never repaired |
| 2027 calendar missing | Status shows "2027 calendar NOT stored"; counting pauses at 61 | — | Store the official list (procedure in memory/README) |

Destructive operations are never automated: no pruning, no `docker system prune`, no volume removal.

## F. Deployment plan (after approval)

1. **You provide §H.** I write the files above and test the image locally (Docker Desktop, if available).
2. **On the VPS, as `tradinglab`:**
   - copy a pinned commit (`git archive` or rsync);
   - `docker compose build`;
   - run `docker compose run --rm collector python update_intraday.py --dry-run`. This writes nothing; it proves Yahoo is reachable from the VPS IP.
3. **Seed state** from the Mac's committed data (`f54535d` or later), checksum-verified.
4. **Enable the timers.** Run **in parallel** with the Mac for at least 5 standard sessions; daily bars must be identical (checksums of overlapping rows).
5. **Declare the VPS canonical** in `RESEARCH_LOG.md`. The Mac collector continues as a secondary copy only.
6. **Run a weekly Mac mirror pull**, plus a monthly restore drill from a backup into a scratch directory.

## G. Local vs Hostinger

| Hostinger VPS | Mac (local) |
|---|---|
| Canonical holdout collection | All development, Stage 2, tests |
| Raw snapshots, manifests, collection log | Mirror of VPS state (verified) |
| Status JSON/HTML (structure only) | Dev dashboard `server.py` (never deployed) |
| Daily metadata backups | Off-host backup copy |
| — | Final ORB v1 evaluation, only after authorisation |
| — | Git history; nothing pushed without your instruction |

## H. Needed from you before implementation

1. VPS OS and version, CPU, RAM and free disk; whether Docker Engine and the compose plugin are installed.
2. How ResQNet is deployed: compose? which ports and reverse proxy? firewall tool? This is only so we don't collide, never to change it.
3. SSH access method for a new `tradinglab` user (key-based).
4. Whether the GitHub repository is private. It doesn't matter for this design, which uses rsync.
5. An alert channel: a dead-man email service (e.g. healthchecks.io free tier, URL in `.env`) or no alerts.
6. Approval of the authorisation-file gate in `load_intraday` (§A.3).
