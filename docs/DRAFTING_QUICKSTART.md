# Drafting API — Quickstart

A step-by-step walkthrough of your first Drafting API call. By the end, you'll have generated a complete legal draft — structured JSON, a reviewable exhibit list, and a downloadable Word document.

> **Before anything else, know this: drafting is long-running by design.** The API runs multi-pass legal drafting plus citation verification and a quality-review pass. A draft typically takes **10–30 minutes** (sometimes longer for large documents). That's why the Drafting API is **async by default**: you submit a job, then poll for the result. Don't fight this — build your integration around polling from day one.

## Before you begin

You need:

- [ ] Your **API key** (shared via 1Password, starts with `dfy_live_`), authorized for the Drafting API — the Drafting and Outlines APIs are available to authorized partners; contact **api@draftyai.com** if your key isn't enabled yet
- [ ] **curl** installed (comes pre-installed on Mac and Linux; [download for Windows](https://curl.se/windows/))
- [ ] This repo cloned locally (`git clone git@github.com:DraftyAI/draftyai-api-docs.git`)

Optional but helpful:

- [jq](https://jqlang.github.io/jq/download/) for pretty-printing JSON in the terminal
- Python 3.7+ if you want to use the Python examples

---

## Step 1: Verify your API key works

Run this command, replacing `YOUR_KEY_HERE` with your actual key:

```bash
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  -X POST https://papi.draftyai.com/api/v1/drafting/generate \
  -H "X-API-Key: YOUR_KEY_HERE"
```

**What to expect:**

| You see | What it means |
|---|---|
| `HTTP Status: 400` or `422` | Your key is valid and authorized. The error is expected because we didn't send any fields yet. |
| `HTTP Status: 401` | No key was received. Check the header name: `X-API-Key`. |
| `HTTP Status: 403` | Your key is invalid, or it isn't authorized for the Drafting API (see [Scopes](API_REFERENCE.md#scopes)). Contact api@draftyai.com. |

---

## Step 2: Submit your first drafting job

Navigate into the repo folder, then run this command. It uses the sample evidence files included in this repo as case documents:

```bash
cd draftyai-api-docs

curl -X POST https://papi.draftyai.com/api/v1/drafting/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "document_type=eb2_niw" \
  -F "documents=@test-kit/evidence/1_Employment_Role_Salary.pdf" \
  -F "documents=@test-kit/evidence/2_Awards_Membership_Synthetic.pdf" \
  -F "documents=@test-kit/evidence/3_Publications_Media_Synthetic.pdf" \
  -F "client_first_name=Karina" \
  -F "client_last_name=Velasquez" \
  -F "client_gender=Female" \
  -F "matter_type=eb2_niw"
```

**What each flag means:**

| Flag | Purpose |
|---|---|
| `-F "document_type=..."` | What to draft. Use a key from [`GET /api/v1/drafting/document-types`](API_REFERENCE.md#get-apiv1draftingdocument-types), or a free-form label like `"Motion to Continue"` — the API plans a tailored structure for labels it doesn't recognize |
| `-F "documents=@..."` | Case documents to draft from. Repeat the field for multiple files (PDF, DOCX, DOC, TXT, MD, RTF; max 64 MB each) |
| `-F "client_first_name=..."` etc. | Creates a client record. If you already have one, pass `client_id` instead |
| `-F "matter_type=..."` | The kind of matter. Use an ID from [`GET /api/v1/drafting/matter-types`](API_REFERENCE.md#get-apiv1draftingmatter-types) or free text (it's classified automatically). If you already have a matter, pass `case_id` instead |

The response comes back **immediately** — it's a job ticket, not the draft:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "poll_url": "/api/v1/drafting/jobs/550e8400-e29b-41d4-a716-446655440000"
}
```

> **Why no `?wait=true`?** Async is the default for drafting (the opposite of the RFE API). Sync mode exists but most proxies kill connections held open for 10+ minutes — use it only for testing, if at all.

---

## Step 3: Poll for the result

Poll the `poll_url` every **30–60 seconds**:

```bash
curl -H "X-API-Key: YOUR_KEY_HERE" \
  "https://papi.draftyai.com/api/v1/drafting/jobs/550e8400-e29b-41d4-a716-446655440000"
```

While the job runs, the response includes a `progress` object so you can show live status:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": {
    "phase": "drafting",
    "sections_completed": 3,
    "sections_total": 9,
    "elapsed_seconds": 412.7
  },
  "result": null,
  "error": null
}
```

**Progress phases you'll see (in rough order):**

| `progress.phase` | What's happening |
|---|---|
| `preparing_matter` | Creating/loading the client and matter |
| `processing_documents` | Uploading and extracting text from your documents (`documents_total` included) |
| `planning` | Planning the document's section structure |
| `starting_generation` | Billing checks; handing off to the drafting engine |
| `starting` | Generation beginning (`sections_total` included) |
| `drafting` | Writing sections — `sections_completed` / `sections_total` track progress |
| `formatting` | Normalizing formatting |
| `verifying_citations` | Checking every legal citation in the draft |
| `reviewing_placeholders` | Checking for unresolved placeholders |
| `quality_review` | Multi-pass quality review of the full draft |
| `building_exhibit_list` | Auto-building the exhibit list from your documents |
| `assembling` | Assembling the final Word document |

Keep polling until `status` changes:

| Status | Meaning |
|---|---|
| `processing` | Still working — check again in 30–60 seconds |
| `completed` | Done — the `result` field contains the full response (Step 4) |
| `failed` | Something went wrong — check the `error` field |

A job still `processing` after **90 minutes** is reported as `failed` (interrupted by a service restart) — resubmit the request if that happens.

---

## Step 4: Read the result

When `status` is `completed`, `result` contains the full draft:

```json
{
  "draft_id": 4211,
  "client_id": 587,
  "case_id": 902,
  "document_type": "eb2_niw",
  "status": "completed",
  "content": {
    "sections": [
      {
        "id": "section-0",
        "title": "Introduction",
        "content": "This letter is respectfully submitted in support of..."
      }
    ],
    "full_text": null
  },
  "docx_download_url": "/api/v1/drafting/4211/download",
  "exhibit_list": {
    "list_id": 77,
    "status": "draft",
    "label_scheme": "LETTER",
    "exhibits": [
      {
        "id": 1,
        "label": "A",
        "title": "Employment Verification Letter",
        "description": "Verification of role and salary from current employer",
        "excluded": false
      }
    ]
  },
  "attorney_review": {
    "attach_markers": [],
    "provide_markers_present": false
  },
  "billing": {
    "billed": true,
    "charged_now": true
  },
  "outline_mode_used": "auto",
  "elapsed_seconds": 1180.4
}
```

**What each field means:**

| Field | Description |
|---|---|
| `draft_id` | Unique ID for this draft — used in every follow-up call (download, exhibits) |
| `client_id` / `case_id` | The client and matter records used. Reuse them on future calls to keep work on the same matter |
| `content.sections` | The draft, section by section: `id`, `title`, `content` |
| `content.full_text` | Full plain text of the draft when available; otherwise `null` (use `sections`) |
| `docx_download_url` | URL path to download the assembled Word document (Step 5) |
| `exhibit_list` | The auto-built exhibit list. **Its `status` is `"draft"` — it is NOT auto-approved.** Approval is your attorney's explicit act (Step 6). `null` if you sent `include_exhibit_list=false` |
| `attorney_review.attach_markers` | Evidence the draft references that your attorney must physically attach before filing |
| `attorney_review.provide_markers_present` | `true` if the draft contains `[ATTORNEY TO PROVIDE ...]` markers — facts only your attorney can supply |
| `billing` | `billed`: whether this call was subject to billing; `charged_now`: whether this matter was charged by this call (a matter is charged once — an outline and a draft on the same matter is one charge) |
| `outline_mode_used` | Which planning mode actually ran: `auto`, `full`, or `none` (may differ from what you requested — see the [API Reference](API_REFERENCE.md#outline-modes)) |
| `elapsed_seconds` | Total generation time |

> **The attorney is always in the loop.** The API produces a draft for attorney review — `attach_markers`, `[ATTORNEY TO PROVIDE]` markers, and the unapproved exhibit list are all there so a reviewing attorney resolves them before anything is filed.

---

## Step 5: Download the Word document

```bash
curl -H "X-API-Key: YOUR_KEY_HERE" \
  "https://papi.draftyai.com/api/v1/drafting/4211/download" \
  -o draft.docx
```

Replace `4211` with your `draft_id`. You can re-download at any time — the document is stored durably. You can also re-fetch the draft's JSON at any time with `GET /api/v1/drafting/{draft_id}`.

---

## Step 6: Review and finalize the exhibit list

The draft came with an exhibit list in `"draft"` status. The intended flow is: **review → edit → approve → reconcile → export**.

**1. Review it** (returns the full list with page ranges and source documents):

```bash
curl -H "X-API-Key: YOUR_KEY_HERE" \
  "https://papi.draftyai.com/api/v1/drafting/4211/exhibits"
```

**2. Edit as needed** — rename, describe, set page ranges, or exclude an exhibit:

```bash
curl -X PATCH https://papi.draftyai.com/api/v1/drafting/4211/exhibits/1 \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"title": "Employment Verification Letter — Acme Corp", "page_start": 1, "page_end": 4}'
```

Reorder them (labels re-derive automatically):

```bash
curl -X POST https://papi.draftyai.com/api/v1/drafting/4211/exhibits/reorder \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"exhibit_ids": [3, 1, 2]}'
```

**3. Approve it** — this is the attorney's explicit sign-off (any later edit reverts the list to `draft`):

```bash
curl -X POST https://papi.draftyai.com/api/v1/drafting/4211/exhibits/approve \
  -H "X-API-Key: YOUR_KEY_HERE"
```

**4. Reconcile the draft** — rewrites every "see Exhibit X" reference in the draft to match the final exhibit order:

```bash
curl -X POST https://papi.draftyai.com/api/v1/drafting/4211/exhibits/reconcile \
  -H "X-API-Key: YOUR_KEY_HERE"
```

**5. Export and download the exhibit list document:**

```bash
curl -X POST https://papi.draftyai.com/api/v1/drafting/4211/exhibits/export \
  -H "X-API-Key: YOUR_KEY_HERE"
# → {"document_id": 5150, "filename": "...", "download_url": "/api/v1/drafting/4211/exhibits/download?document_id=5150"}

curl -H "X-API-Key: YOUR_KEY_HERE" \
  "https://papi.draftyai.com/api/v1/drafting/4211/exhibits/download?document_id=5150" \
  -o exhibit_list.docx
```

If you reconciled after downloading the draft, re-download the draft DOCX (Step 5) to pick up the updated exhibit references.

---

## What just happened?

Behind the scenes, that single API call did all of this:

1. **Created a client** record for "Karina Velasquez"
2. **Created a matter** of type EB-2 NIW linked to the client
3. **Uploaded your documents** to secure cloud storage and extracted their text
4. **Planned the document** — a section structure tailored to the matter and your documents
5. **Drafted every section**, then verified citations and ran a quality review
6. **Built an exhibit list** from your documents, with AI-generated titles, left in `draft` status for attorney review
7. **Assembled a formatted Word document** and stored it durably
8. **Returned everything** — structured JSON, exhibit list, and download URLs

---

## Using Python instead of curl

For a complete, ready-to-run script with polling and progress display, see [examples/drafting_example.py](../examples/drafting_example.py). The short version:

```python
import time
import requests

API_KEY = "YOUR_KEY_HERE"
BASE_URL = "https://papi.draftyai.com"
headers = {"X-API-Key": API_KEY}

# Submit (async is the default — no ?wait needed)
resp = requests.post(
    f"{BASE_URL}/api/v1/drafting/generate",
    headers=headers,
    files=[("documents", open("test-kit/evidence/1_Employment_Role_Salary.pdf", "rb"))],
    data={
        "document_type": "eb2_niw",
        "client_first_name": "Karina",
        "client_last_name": "Velasquez",
        "client_gender": "Female",
        "matter_type": "eb2_niw",
    },
    timeout=120,
)
resp.raise_for_status()
poll_url = f"{BASE_URL}{resp.json()['poll_url']}"

# Poll every 30 seconds — drafts take 10-30 minutes
while True:
    time.sleep(30)
    status = requests.get(poll_url, headers=headers, timeout=60).json()
    progress = status.get("progress") or {}
    print(f"{status['status']}  phase={progress.get('phase', '-')}")
    if status["status"] == "completed":
        result = status["result"]
        break
    if status["status"] == "failed":
        raise RuntimeError(status["error"])

print(f"Draft {result['draft_id']} done in {result['elapsed_seconds']}s")
```

---

## Common errors

| Error | What it means | How to fix |
|---|---|---|
| `400 Bad Request` | Missing/invalid fields — no `document_type`, unsupported file extension, file over 64 MB, `outline_mode` not one of `auto`/`full`/`none`, or `case_id` doesn't belong to the client | Check the `detail` message; fix the field it names |
| `401 Unauthorized` | API key is missing | Add the `-H "X-API-Key: ..."` header |
| `402 Payment Required` | The account behind the key can't generate right now — `detail.code` is `subscribe_required` (no active subscription) or `overage_block` (matter allowance used up) | Resolve billing in the DraftyAI app, or contact api@draftyai.com |
| `403 Forbidden` | Invalid key, a JWT instead of an API key, or `detail.code: "scope_denied"` — the key isn't authorized for the Drafting API | Check the key; for scope changes contact api@draftyai.com |
| `404 Not Found` | Unknown `job_id`, `draft_id`, `client_id`, or `case_id` | Check the ID; jobs and drafts are only visible to the key that created them |
| `429 Too Many Requests` | Rate limit exceeded | Poll less often (every 30–60 s is plenty) and retry after a minute |
| `500 Internal Server Error` | Generation didn't complete | Retry the request; if persistent, contact api@draftyai.com |
| `502 Bad Gateway` | The drafting engine reported an error | Retry; if persistent, contact api@draftyai.com |

---

## Next steps

- [Full Flow Guide](FULL_FLOW_GUIDE.md) — add the Outlines API for a strategy-first enterprise workflow
- [API Reference](API_REFERENCE.md) — every endpoint, field, and error code, including the catalogs (`/document-types`, `/matter-types`, `/venues`)
- [examples/](../examples/) — `drafting_example.py`, `drafting_example.sh`, `outline_example.py`
