# DraftyAI — RFE Response Builder API

Generate complete USCIS Request for Evidence (RFE) response drafts programmatically.

Send an RFE notice and supporting documents to the API. Get back a fully drafted legal response — including legal arguments, exhibit citations, and a downloadable Word document — in about two minutes.

## How It Works

```
                         ┌─────────────────────────────┐
  Your files             │     DraftyAI API             │           What you get back
  ─────────              │                              │           ──────────────────
                         │  1. Reads the RFE notice     │
  ┌──────────────┐       │  2. Identifies each issue    │       ┌───────────────────┐
  │ RFE Notice   │──────>│  3. Analyzes your evidence   │──────>│ JSON with the     │
  │ (PDF/DOCX)   │       │  4. Writes legal arguments   │       │ full draft + a    │
  └──────────────┘       │  5. Cites your exhibits      │       │ DOCX download URL │
                         │  6. Exports a Word document  │       └───────────────────┘
  ┌──────────────┐       │                              │
  │ Evidence     │──────>│                              │
  │ (optional)   │       │                              │
  └──────────────┘       └─────────────────────────────┘
```

## Getting Started

### 1. Get your API key

Your API key will be shared with you via 1Password. It looks like this:

```
dfy_live_abc123...
```

Keep it secret. It controls access to your account and usage limits.

### 2. Clone this repo

```bash
git clone git@github.com:DraftyAI/draftyai-api-docs.git
cd draftyai-api-docs
```

This gives you test files and working code examples you can run immediately.

### 3. Run your first test

From inside the repo, replace `YOUR_KEY_HERE` with your actual API key and run:

```bash
curl -X POST https://papi.draftyai.com/api/v1/rfe/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "notice_file=@test-kit/notice/drafty_simulated_rfe_i140_e11.pdf" \
  -F "client_first_name=Karina" \
  -F "client_last_name=Velasquez" \
  -F "client_gender=Female"
```

This sends a sample RFE notice to the API. After about 60–120 seconds, you'll get back a JSON response containing the complete draft and a URL to download the Word document.

If you prefer Python, see [examples/python_example.py](examples/python_example.py) — it does the same thing in a script you can adapt.

## What's in this repo

| Folder | What's inside |
|---|---|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | Step-by-step walkthrough of your first API call, with explanations |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | Full technical reference — every endpoint, field, and error code |
| [examples/](examples/) | Working Python and bash scripts you can copy into your project |
| [test-kit/](test-kit/) | Sample RFE notice, evidence files, and a test client profile |

## Two ways to use the API

**Simple (recommended to start):** One API call does everything. Send files, get a draft back.

```
POST /api/v1/rfe/generate
```

**Advanced:** Use individual endpoints for fine-grained control over each step (create clients, upload notices, manage exhibits, generate drafts separately). See the [API Reference](docs/API_REFERENCE.md#granular-endpoints).

## Support

Questions or issues? Reach out to **api@draftyai.com**

## Website

draftyai.com
