# Daily Job Digest (Kenya + Remote)

A daily morning email with matching jobs for Nairobi/Kenya plus **international
100% remote** (English-language) roles, scraped from **MyJobMag**, **Corporate Staffing Services**,
**DevNetJobs**, **BrighterMonday** and (org-specific) **Workable** widgets, plus
remote boards **Jobicy**, **RemoteOK** and **Adzuna**. This fork is tuned for **Angular /
frontend / software development** roles. Runs every day at 06:00 EAT via GitHub
Actions and needs no server of yours. Jobs are ranked **newest-first**, with
deadlines shown so you never miss an application window.

## Setup (one-time, ~10 minutes)

### 1. Create a Gmail app password (only for sending)

Gmail will not accept your normal password over SMTP. You need an *app password*:

1. Turn on **2-Step Verification** for the sending Gmail: `myaccount.google.com` → Security → 2-Step Verification.
2. Then: Security → **App passwords** → name it `job-digest`.
3. Copy the 16-character password (e.g. `abcd efgh ijkl mnop`).

> The sending account can be the same as your inbox (`mikembugua.dev@gmail.com`).

### 2. Register the GitHub remote (your repo)

The repo already has git history. Point it at your own GitHub repo and push:

```bash
cd ~/job-digest
git remote set-url origin https://github.com/michaelmbugua-me/job-digest.git
git push -u origin main
```

### 3. Add the repository secrets

In the repo on GitHub: **Settings → Secrets and variables → Actions → New repository secret**:

| Secret               | Value                                              |
| -------------------- | -------------------------------------------------- |
| `GMAIL_SENDER`       | the Gmail address that sends (e.g. `mikembugua.dev@gmail.com`) |
| `GMAIL_APP_PASSWORD` | the 16-char app password (spaces optional)         |
| `DIGEST_TO`          | where the digest lands (e.g. `mikembugua.dev@gmail.com`) |
| `ADZUNA_APP_ID`      | *optional* — free from <https://developer.adzuna.com/notes/create> (adds ~10+ international remote jobs) |
| `ADZUNA_APP_KEY`     | *optional* — pair with `ADZUNA_APP_ID` above |

If either Adzuna secret is missing, the source is skipped gracefully.

The daily schedule is already configured in `.github/workflows/daily_digest.yml`.

### 4. Send a test digest

On GitHub go to **Actions → daily-digest → Run workflow → Run workflow**.
Check your inbox; it takes a minute or two. From then on it runs automatically at 06:00 EAT.

## Tuning the jobs you get

Edit `config.json`:

- `keywords` — role titles to match (matched in job titles or descriptions)
- `skills` — extra terms that boost relevance
- `locations` — city/country names; known non-matching locations are dropped
- `max_results` — how many jobs per email
- `brightermonday.lists` / `brightermonday.pages` — which career pages to crawl and how deep (default 2)
- `workable_accounts` — `[["slug", "Company Name"], ...]` pairs for org-specific Workable boards
- `remote.enabled` — switch international remote jobs on/off
- `remote.query` — the tech/role searched on the remote boards (default `angular`)
- `remote.sources` — which remote boards to use (`jobicy`, `remoteok`, `adzuna`; a `remotive` module exists but is noisy)
- `remote.max_days_old` — only include remote jobs posted in the last N days
- `remote.max_results` — reserved slots for remote jobs in each digest (e.g. 15)
- `remote.query` — the tech/role searched on the remote boards (default `angular`)
- `max_results` — total jobs per email (remote jobs get dedicated reserved slots)
- You can also drop a source from `sources` if you don't want it.

## Try it locally

```bash
cd ~/job-digest
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m jobdigest.main --dry-run     # preview, no email
GMAIL_SENDER=you@gmail.com GMAIL_APP_PASSWORD=... .venv/bin/python -m jobdigest.main
```