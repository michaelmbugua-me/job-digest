# Daily Job Digest (Kenya)

A daily morning email with matching jobs for Nairobi/Kenya, scraped from
**MyJobMag**, **Corporate Staffing Services** and **DevNetJobs**. Runs every day at
08:00 EAT via GitHub Actions and needs no server of yours.

## Setup (one-time, ~10 minutes)

### 1. Create a Gmail app password (only for sending)

Gmail will not accept your normal password over SMTP. You need an *app password*:

1. Turn on **2-Step Verification** for the sending Gmail: `myaccount.google.com` → Security → 2-Step Verification.
2. Then: Security → **App passwords** → name it `job-digest`.
3. Copy the 16-character password (e.g. `abcd efgh ijkl mnop`).

> The sending account can be the same as your inbox (`chrispinodhiambo5@gmail.com`).

### 2. Create a GitHub repo and upload this folder

```bash
cd ~/job-digest
git init
git add .
git commit -m "job digest"
# create an empty repo at github.com (e.g. job-digest), then:
git remote add origin https://github.com/<you>/job-digest.git
git push -u origin main
```

### 3. Add the repository secrets

In the repo on GitHub: **Settings → Secrets and variables → Actions → New repository secret**:

| Secret               | Value                                              |
| -------------------- | -------------------------------------------------- |
| `GMAIL_SENDER`       | the Gmail address that sends (e.g. `chrispinodhiambo5@gmail.com`) |
| `GMAIL_APP_PASSWORD` | the 16-char app password (spaces optional)         |
| `DIGEST_TO`          | where the digest lands (e.g. `chrispinodhiambo5@gmail.com`) |

The daily schedule is already configured in `.github/workflows/daily_digest.yml`.

### 4. Send a test digest

On GitHub go to **Actions → daily-digest → Run workflow → Run workflow**.
Check your inbox; it takes a minute or two. From then on it runs automatically at 08:00 EAT.

## Tuning the jobs you get

Edit `config.json`:

- `keywords` — role titles to match (matched in job titles or descriptions)
- `skills` — extra terms that boost relevance
- `locations` — city/country names; known non-matching locations are dropped
- `max_results` — how many jobs per email
- You can also drop a source from `sources` if you don't want it.

## Try it locally

```bash
cd ~/job-digest
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m jobdigest.main --dry-run     # preview, no email
GMAIL_SENDER=you@gmail.com GMAIL_APP_PASSWORD=... .venv/bin/python -m jobdigest.main
```