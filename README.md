# DraftyAI Partner API

Generate complete immigration legal documents programmatically — case strategy outlines, full legal drafts with exhibit lists, and USCIS RFE responses.

One API key. Three products. Everything returns structured JSON plus a downloadable Word document.

## The three products

| Product | One call | What you get back | Typical time |
|---|---|---|---|
| **Drafting API** | `POST /api/v1/drafting/generate` | A complete legal draft (brief, motion, cover letter, petition support letter, ...) with an auto-built exhibit list | 10–30 minutes |
| **Outlines API** | `POST /api/v1/outlines/generate` | A finalized case-strategy outline (elements, evidence map, gaps, recommended actions) | 1–4 minutes |
| **RFE Response Builder** | `POST /api/v1/rfe/generate` | A complete USCIS Request for Evidence response with legal arguments and exhibit citations | 1–2 minutes |

The products compose: generate an outline first, then pass its `outline_run_id` to the Drafting API and the draft is built on top of that reviewed strategy. See the [Full Flow Guide](docs/FULL_FLOW_GUIDE.md).

## How it works

```
                          ┌──────────────────────────────┐
  Your files              │       DraftyAI API           │          What you get back
  ─────────               │                              │          ──────────────────
                          │  1. Creates client + matter  │
  ┌───────────────┐       │  2. Reads your documents     │      ┌────────────────────┐
  │ Case documents│──────>│  3. Plans the document       │─────>│ JSON with the full │
  │ (PDF/DOCX/...)│       │  4. Drafts every section     │      │ draft + exhibit    │
  └───────────────┘       │  5. Verifies citations       │      │ list + DOCX        │
                          │  6. Runs quality review      │      │ download URLs      │
  ┌───────────────┐       │  7. Builds the exhibit list  │      └────────────────────┘
  │ Instructions  │──────>│  8. Assembles the Word doc   │
  │ (optional)    │       │                              │
  └───────────────┘       └──────────────────────────────┘
```

> **Drafting is long-running by design.** The Drafting API runs multi-pass legal drafting plus a quality-review pass — budget **10–30 minutes** per draft and use async mode (the default). The Outlines and RFE APIs are much faster.

## Getting started

### 1. Get your API key

Your API key will be shared with you via 1Password. It looks like this:

```
dfy_live_abc123...
```

Keep it secret. It controls access to your account and usage limits. Keys can be scoped to specific products (see [Scopes](docs/API_REFERENCE.md#scopes)).

### 2. Clone this repo

```bash
git clone git@github.com:DraftyAI/draftyai-api-docs.git
cd draftyai-api-docs
```

This gives you test files and working code examples you can run immediately.

### 3. Run your first test

The fastest first win is the RFE Response Builder (results in ~2 minutes). Replace `YOUR_KEY_HERE` with your actual API key and run:

```bash
curl -X POST https://papi.draftyai.com/api/v1/rfe/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "notice_file=@test-kit/notice/drafty_simulated_rfe_i140_e11.pdf" \
  -F "client_first_name=Karina" \
  -F "client_last_name=Velasquez" \
  -F "client_gender=Female"
```

Then try a full draft with the Drafting API — see the [Drafting Quickstart](docs/DRAFTING_QUICKSTART.md).

## What's in this repo

| Path | What's inside |
|---|---|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | RFE Response Builder quickstart — your first API call, step by step |
| [docs/DRAFTING_QUICKSTART.md](docs/DRAFTING_QUICKSTART.md) | Drafting API quickstart — first full draft, polling, exhibits |
| [docs/FULL_FLOW_GUIDE.md](docs/FULL_FLOW_GUIDE.md) | The complete integration: outline → draft → exhibits → downloads, with a runnable script |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | Full technical reference — every endpoint, field, and error code for all three products |
| [examples/](examples/) | Working Python and bash scripts you can copy into your project |
| [test-kit/](test-kit/) | Sample notice, evidence files, and a test client profile — works with every product |
| [CHANGELOG.md](CHANGELOG.md) | What's new in the API and these docs |

## Two ways to use the API

**Simple (recommended to start):** One API call per product does everything. Send files, get a finished document back.

```
POST /api/v1/drafting/generate     # full legal draft + exhibit list
POST /api/v1/outlines/generate     # case-strategy outline
POST /api/v1/rfe/generate          # RFE response
```

**Advanced:** Use individual endpoints for fine-grained control — browse the document-type catalog, reuse existing clients and matters, edit/approve/export exhibit lists, feed an outline into a draft. See the [API Reference](docs/API_REFERENCE.md).

## Availability

The Drafting and Outlines APIs are available to authorized partners. The RFE Response Builder API is generally available to API customers. To request access or change what your key can reach, contact **api@draftyai.com**.

## Support

Questions or issues? Reach out to **api@draftyai.com**

## Website

[DraftyAI.com](https://draftyai.com)
