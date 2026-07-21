# API Reference

Complete technical reference for the DraftyAI Partner API — three products, one authentication scheme:

| Product | Section | Simplified endpoint |
|---|---|---|
| RFE Response Builder | [RFE Response Builder API](#rfe-response-builder-api) | `POST /api/v1/rfe/generate` |
| Drafting | [Drafting API](#drafting-api) | `POST /api/v1/drafting/generate` |
| Outlines | [Outlines API](#outlines-api) | `POST /api/v1/outlines/generate` |

The Drafting and Outlines APIs are available to authorized partners.

**Base URL:** `https://papi.draftyai.com`

All `*_download_url` values returned by the API are paths — prepend the base URL when requesting them.

---

## Authentication

Every request must include your API key in the `X-API-Key` header:

```
X-API-Key: dfy_live_abc123...
```

**curl:**

```bash
curl -H "X-API-Key: dfy_live_abc123..." https://papi.draftyai.com/...
```

**Python:**

```python
import requests

headers = {"X-API-Key": "dfy_live_abc123..."}
response = requests.get("https://papi.draftyai.com/...", headers=headers)
```

API keys are provisioned by DraftyAI. Each key is tied to one user account and has rate limits (default: 60 requests/minute, 1,000 requests/day).

### Scopes

Keys may be restricted to specific products. A key scoped to the RFE product can call `/api/v1/rfe/...` but gets `403` with `{"detail": {"code": "scope_denied", "message": "This API key is not authorized for this endpoint."}}` on `/api/v1/drafting/...`, and vice versa. Unrestricted keys can call everything they're provisioned for.

To check or change what your key can reach, contact **api@draftyai.com**.

---

## Rate Limits

| Limit | Default |
|---|---|
| Requests per minute | 60 |
| Requests per day | 1,000 |

When you exceed the limit, the API returns `429 Too Many Requests`. Wait for the limit to reset (1 minute for per-minute limits) and retry. Limits are per key; higher limits are available on request.

Polling well within these limits is easy: drafting jobs only need a poll every 30–60 seconds.

---

# RFE Response Builder API

Generate a complete USCIS Request for Evidence response from a notice file and optional evidence. Typical generation time: **60–120 seconds**, so synchronous mode is the default for this product.

## How it works

When you call the simplified endpoint, the API runs this pipeline internally:

```
1. Create client record          (from the name you provide)
2. Create RFE project            (linked to the client)
3. Upload notice to storage      (the PDF you send)
4. AI analyzes the notice        (extracts issues, names, dates)
5. Process evidence              (if you sent evidence files)
   └── Upload files, create exhibits, link to issues
6. Generate draft                (AI writes the full response)
7. Export Word document          (formatted DOCX)
8. Return everything to you      (JSON + download URL)
```

You don't need to understand this pipeline to use the API — the simplified endpoint handles it all in one call.

## Simplified Endpoint (recommended)

### `POST /api/v1/rfe/generate`

One call to generate a complete RFE response draft.

#### Request format: `multipart/form-data`

| Field | Required | Type | Description |
|---|---|---|---|
| `notice_file` | Yes | File | The RFE notice document (PDF, DOCX, DOC, or TXT; max 64 MB) |
| `evidence_files` | No | File(s) | Supporting case documents. Repeat the field for multiple files. |
| `client_first_name` | Yes | String | Client's first name |
| `client_last_name` | Yes | String | Client's last name |
| `client_gender` | No | String | Client's gender (default: `"Unknown"`) |
| `response_mode` | No | String | `"with_evidence"` or `"arguments_only"` (see below). Auto-detected if omitted. |
| `wait` | No | Query param | `true` (default) = wait for result; `false` = return a job ID immediately |

#### curl example

```bash
curl -X POST https://papi.draftyai.com/api/v1/rfe/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "notice_file=@rfe_notice.pdf" \
  -F "evidence_files=@employment_letter.pdf" \
  -F "evidence_files=@awards.pdf" \
  -F "client_first_name=Juan" \
  -F "client_last_name=Garcia" \
  -F "client_gender=Male"
```

#### Python example

```python
import requests

resp = requests.post(
    "https://papi.draftyai.com/api/v1/rfe/generate",
    headers={"X-API-Key": "YOUR_KEY_HERE"},
    files=[
        ("notice_file", ("notice.pdf", open("notice.pdf", "rb"), "application/pdf")),
        ("evidence_files", ("letter.pdf", open("letter.pdf", "rb"), "application/pdf")),
        ("evidence_files", ("awards.pdf", open("awards.pdf", "rb"), "application/pdf")),
    ],
    data={
        "client_first_name": "Juan",
        "client_last_name": "Garcia",
        "client_gender": "Male",
    },
    timeout=300,
)
result = resp.json()
```

#### Sync response (`?wait=true`, the default)

The request blocks for ~60–120 seconds, then returns:

```json
{
  "project_id": 123,
  "client_id": 456,
  "draft_version_id": 789,
  "content": {
    "intro": "Dear USCIS Officer...",
    "issues": [
      {
        "title": "Extraordinary Ability - Original Contributions",
        "response": "The beneficiary has made original contributions..."
      }
    ],
    "conclusion": "For the foregoing reasons...",
    "legal_references": ["8 CFR § 204.5(h)(3)", "Matter of Dhanasar"]
  },
  "docx_download_url": "/notice-responses/123/exports/42/download",
  "issue_count": 3,
  "elapsed_seconds": 72.4
}
```

To download the Word document:

```bash
curl -H "X-API-Key: YOUR_KEY_HERE" \
  "https://papi.draftyai.com/notice-responses/123/exports/42/download" \
  -o response.docx
```

## Response Modes

| Mode | When to use | What happens |
|---|---|---|
| `with_evidence` | You have supporting documents (employment letters, awards, publications, etc.) | The API analyzes your evidence, creates exhibits, and cites them in the draft |
| `arguments_only` | You don't have documents to upload right now | The AI generates legal arguments for each issue without exhibit citations |

**Which should I choose?**

- If you have **any** supporting files for the case, use `with_evidence`. The draft will be stronger because it references specific evidence.
- If you only have the RFE notice and want a quick first draft, use `arguments_only`. You can always re-generate later with evidence.
- If you **omit** the `response_mode` field, the API decides automatically: it uses `with_evidence` if you sent evidence files, `arguments_only` if you didn't.

## Async Mode (Polling)

For long-running requests, or if your system prefers non-blocking calls, add `?wait=false` to the URL.

### Step 1: Submit the job

```bash
curl -X POST "https://papi.draftyai.com/api/v1/rfe/generate?wait=false" \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "notice_file=@rfe_notice.pdf" \
  -F "client_first_name=Juan" \
  -F "client_last_name=Garcia"
```

Returns immediately:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "poll_url": "/api/v1/rfe/jobs/550e8400-e29b-41d4-a716-446655440000"
}
```

### Step 2: Poll for the result

```bash
curl -H "X-API-Key: YOUR_KEY_HERE" \
  "https://papi.draftyai.com/api/v1/rfe/jobs/550e8400-e29b-41d4-a716-446655440000"
```

Keep polling every 10–15 seconds until `status` changes:

| Status | Meaning |
|---|---|
| `processing` | Still working — check again in 10 seconds |
| `completed` | Done — the `result` field contains the full response (same format as sync mode) |
| `failed` | Something went wrong — check the `error` field |

Jobs expire after **1 hour**. If you don't poll within that time, the result is lost.

### Python polling example

```python
import time
import requests

API_KEY = "YOUR_KEY_HERE"
headers = {"X-API-Key": API_KEY}

# Submit
resp = requests.post(
    "https://papi.draftyai.com/api/v1/rfe/generate?wait=false",
    headers=headers,
    files={"notice_file": open("notice.pdf", "rb")},
    data={"client_first_name": "Juan", "client_last_name": "Garcia"},
)
job = resp.json()
poll_url = f"https://papi.draftyai.com{job['poll_url']}"

# Poll
while True:
    status = requests.get(poll_url, headers=headers).json()
    print(f"Status: {status['status']}")
    if status["status"] == "completed":
        result = status["result"]
        print(f"Done! {result['issue_count']} issues addressed.")
        break
    elif status["status"] == "failed":
        print(f"Error: {status['error']}")
        break
    time.sleep(10)
```

## Granular Endpoints (RFE)

For advanced integrations that need control over individual steps. All endpoints use the same `X-API-Key` authentication.

### Clients

| Method | Path | Description |
|---|---|---|
| `POST` | `/clients` | Create a client record |
| `GET` | `/clients` | List all your clients |

### Projects

| Method | Path | Description |
|---|---|---|
| `POST` | `/notice-responses` | Create a new RFE project |
| `GET` | `/notice-responses?client_id={id}` | List projects for a client |
| `GET` | `/notice-responses/{id}` | Get project details |
| `PUT` | `/notice-responses/{id}` | Update project metadata |

### Notice Upload and Analysis

| Method | Path | Description |
|---|---|---|
| `POST` | `/notice-responses/{id}/notice` | Upload an RFE notice file (multipart) |
| `POST` | `/notice-responses/{id}/notice/parse` | Start AI analysis of the notice |
| `GET` | `/notice-responses/{id}/notice/parse-status` | Check analysis progress |

### Issues

| Method | Path | Description |
|---|---|---|
| `GET` | `/notice-responses/{id}/issues` | List issues extracted from the notice |
| `PUT` | `/notice-responses/{id}/issues/{issue_id}` | Update an issue (add notes, arguments) |
| `POST` | `/notice-responses/{id}/issues/let-ai-answer-all` | Let AI generate arguments for all issues |

### Response Mode

| Method | Path | Description |
|---|---|---|
| `GET` | `/notice-responses/{id}/response-mode` | Get the current response mode |
| `PUT` | `/notice-responses/{id}/response-mode` | Set to `with_evidence` or `arguments_only` |

### Evidence and Exhibits

| Method | Path | Description |
|---|---|---|
| `POST` | `/notice-responses/{id}/documents` | Upload an evidence document (multipart) |
| `GET` | `/notice-responses/{id}/documents` | List evidence documents |
| `POST` | `/notice-responses/{id}/exhibits` | Create an exhibit manually |
| `GET` | `/notice-responses/{id}/exhibits` | List all exhibits |
| `POST` | `/notice-responses/{id}/ai/auto-create-exhibits` | AI creates exhibits from your documents |
| `POST` | `/notice-responses/{id}/ai/suggest-exhibit-links` | AI suggests which exhibits support which issues |
| `POST` | `/notice-responses/{id}/issues/{issue_id}/exhibits` | Link specific exhibits to an issue |

### Draft Generation and Export

| Method | Path | Description |
|---|---|---|
| `POST` | `/notice-responses/{id}/drafts/generate` | Generate the RFE response draft |
| `GET` | `/notice-responses/{id}/drafts` | List all draft versions |
| `POST` | `/notice-responses/{id}/exports/response` | Export a draft as a Word document |
| `GET` | `/notice-responses/{id}/exports/{artifact_id}/download` | Download an exported file |

---

# Drafting API

Generate a complete legal draft — brief, motion, cover letter, petition support letter, and more — from case documents, with an auto-built exhibit list and an assembled Word document.

> **Generation is long-running by design.** Multi-pass legal drafting, citation verification, and quality review take **10–30 minutes** (sometimes more). Async mode (`?wait=false`) is the **default** for this product — submit a job, then poll every 30–60 seconds. Sync mode exists (`?wait=true`, server-side cap 15 minutes) but most proxies kill connections held open this long; use it only for testing.

## How it works

```
1. Create/reuse client            (client_id, or first+last name)
2. Create/reuse matter            (case_id, or matter_type — classified automatically)
3. Upload documents               (text extracted; linked to the matter)
4. Plan the document              (section plan — see outline modes)
5. Billing check                  (matter-based; a matter is charged once)
6. Generate                       (multi-pass drafting + citation verification + quality review)
7. Build exhibit list             (from your documents; left in "draft" status)
8. Assemble Word document         (stored durably; downloadable any time)
9. Return everything              (JSON + exhibit list + download URLs)
```

## `POST /api/v1/drafting/generate`

One call to generate a complete draft.

### Request format: `multipart/form-data`

| Field | Required | Type | Default | Description |
|---|---|---|---|---|
| `document_type` | Yes | String | — | What to draft. A key from [`/document-types`](#get-apiv1draftingdocument-types), or any free-form label (e.g. `"Motion to Continue"`) — unrecognized labels get a tailored section plan |
| `documents` | No | File(s) | — | Case documents to draft from. Repeat the field for multiple files. PDF, DOC, DOCX, TXT, MD, RTF; max 64 MB each |
| `client_id` | One of † | Integer | — | An existing client's ID |
| `client_first_name` | One of † | String | — | With `client_last_name`, creates a new client |
| `client_last_name` | One of † | String | — | See above |
| `client_gender` | No | String | `"Unknown"` | Used for pronouns in the draft |
| `client_background` | No | String | — | Background summary of the client/case; feeds planning and drafting |
| `case_id` | One of ‡ | Integer | — | An existing matter's ID. Must belong to the resolved client (otherwise `400`) |
| `matter_type` | One of ‡ | String | — | With no `case_id`, creates a matter. An ID from [`/matter-types`](#get-apiv1draftingmatter-types), or free text (classified automatically) |
| `venue` | No | String | — | Filing venue ID from [`/venues`](#get-apiv1draftingvenues) (e.g. `"eoir"`, `"ca9"`) |
| `jurisdiction` | No | String | — | Controlling circuit for legal authority (e.g. `"CA9"`) |
| `instructions` | No | String | — | Free-form drafting instructions (tone, emphasis, points to include) |
| `outline_mode` | No | String | `"auto"` | `auto` \| `full` \| `none` — see [Outline modes](#outline-modes) |
| `outline_run_id` | No | Integer | — | An outline from the [Outlines API](#outlines-api) to draft from. Implies `full` mode |
| `include_exhibit_list` | No | Boolean | `true` | Set `false` to skip building the exhibit list |
| `wait` | No | Query param | `false` | `false` (default) = async job; `true` = block until complete (testing only) |

† Provide either `client_id`, or both `client_first_name` and `client_last_name`.
‡ Provide either `case_id` or `matter_type`.

### Outline modes

| `outline_mode` | What happens | When to use |
|---|---|---|
| `auto` (default) | A fast, tailored section plan is built from the matter, your documents, and instructions | Most calls |
| `full` | The full Outline engine runs first (case-strategy derivation, adds 1–4 minutes) and its finalized outline feeds the draft. Passing `outline_run_id` also selects this mode and skips re-derivation | Deepest case analysis; the strategy-first enterprise flow |
| `none` | No tailored plan — the document's standard template structure is used as-is. Only possible for catalog `document_type` keys; free-form labels always need a plan, so the API falls back to `auto` | Fastest path for standard document types |

The response's `outline_mode_used` reports which mode actually ran — if the `full` outline step can't complete, the API degrades gracefully to `auto` rather than failing the draft.

### Response (async, the default)

Returns immediately:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "poll_url": "/api/v1/drafting/jobs/550e8400-e29b-41d4-a716-446655440000"
}
```

## `GET /api/v1/drafting/jobs/{job_id}`

Poll an async drafting job. Poll every **30–60 seconds**.

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

| Field | Description |
|---|---|
| `status` | `processing`, `completed`, or `failed` |
| `progress` | Present while `processing`: `phase` (see table below), `elapsed_seconds`, and during drafting `sections_completed` / `sections_total` (document-upload steps report `documents_total`) |
| `result` | On `completed`: the full [generate response](#the-generate-result) |
| `error` | On `failed`: a human-readable message |

**Progress phases** (rough order): `preparing_matter` → `processing_documents` → `planning` → `starting_generation` → `starting` → `drafting` → `formatting` → `verifying_citations` → `reviewing_placeholders` → `quality_review` → `building_exhibit_list` → `assembling`. Treat the set as open-ended — display the string, don't switch on it exhaustively.

A job still `processing` after **90 minutes** is reported as `failed` with an "interrupted" error (service restart) — resubmit the request. Completed results stay retrievable via the job, and the draft itself is always retrievable via `GET /api/v1/drafting/{draft_id}`.

## The generate result

Returned as `result` on a completed job (or directly in sync mode):

```json
{
  "draft_id": 4211,
  "client_id": 587,
  "case_id": 902,
  "document_type": "eb2_niw",
  "status": "completed",
  "content": {
    "sections": [
      {"id": "section-0", "title": "Introduction", "content": "..."},
      {"id": "section-1", "title": "Statement of Facts", "content": "..."}
    ],
    "full_text": null
  },
  "docx_download_url": "/api/v1/drafting/4211/download",
  "exhibit_list": {
    "list_id": 77,
    "status": "draft",
    "label_scheme": "LETTER",
    "exhibits": [
      {"id": 1, "label": "A", "title": "Employment Verification Letter", "description": "...", "excluded": false}
    ]
  },
  "attorney_review": {
    "attach_markers": [],
    "provide_markers_present": false
  },
  "billing": {"billed": true, "charged_now": true},
  "outline_mode_used": "auto",
  "elapsed_seconds": 1180.4
}
```

| Field | Type | Description |
|---|---|---|
| `draft_id` | Integer | The draft's ID — used in all follow-up endpoints |
| `client_id`, `case_id` | Integer | The client and matter used — pass them back on future calls to keep work on the same matter |
| `document_type` | String | Echo of what you requested |
| `status` | String | `"completed"` |
| `content.sections` | Array | The draft, section by section: `{id, title, content}` |
| `content.full_text` | String or null | Full plain text when available; use `sections` otherwise |
| `docx_download_url` | String | Path to download the assembled Word document |
| `exhibit_list` | Object or null | The auto-built exhibit list — `list_id`, `status` (**always starts as `"draft"`; never auto-approved**), `label_scheme`, and `exhibits` (`{id, label, title, description, excluded}`). `null` when `include_exhibit_list=false` or the draft has no matter documents |
| `attorney_review.attach_markers` | Array of strings | Evidence the draft references that the attorney must physically attach before filing |
| `attorney_review.provide_markers_present` | Boolean | `true` if the draft contains `[ATTORNEY TO PROVIDE ...]` markers for facts only the attorney can supply |
| `billing.billed` | Boolean | Whether this call was subject to billing (keys on partner agreements may not be) |
| `billing.charged_now` | Boolean | Whether this matter was charged by this call. A matter is charged **once** — an outline and a draft on the same matter is one charge |
| `outline_mode_used` | String | The planning mode that actually ran: `auto`, `full`, or `none` |
| `elapsed_seconds` | Number | Total pipeline time |

## `GET /api/v1/drafting/{draft_id}`

Retrieve a draft's status and content at any time after generation:

```json
{
  "draft_id": 4211,
  "case_id": 902,
  "client_id": 587,
  "document_type": "eb2_niw",
  "status": "completed",
  "content": {"sections": [{"id": "section-0", "title": "Introduction", "content": "..."}]},
  "docx_download_url": "/api/v1/drafting/4211/download"
}
```

`docx_download_url` is `null` if no Word document has been assembled for the draft.

## `GET /api/v1/drafting/{draft_id}/download`

Download the assembled Word document (`.docx`). Returns `404` if no document has been assembled yet. The file is stored durably — download it whenever you like.

```bash
curl -H "X-API-Key: YOUR_KEY_HERE" \
  "https://papi.draftyai.com/api/v1/drafting/4211/download" -o draft.docx
```

## Catalogs

Three read-only endpoints so you can populate pickers and validate inputs.

### `GET /api/v1/drafting/document-types`

Document types you can pass as `document_type`:

```json
{
  "document_types": [
    {"key": "eb2_niw", "display_name": "EB-2 NIW Petition Support Letter", "category": "..."}
  ],
  "note": "document_type also accepts free-form labels (e.g. 'Motion to Continue', 'Cover Letter') — the API plans a tailored structure."
}
```

Any value not in this catalog is treated as a free-form label and drafted from a tailored section plan.

### `GET /api/v1/drafting/matter-types`

Canonical matter types for the `matter_type` field (free text is also accepted — it's classified automatically):

```json
{"matter_types": [{"id": "eb2_niw", "label": "EB-2 National Interest Waiver"}]}
```

### `GET /api/v1/drafting/venues`

Filing venues for the `venue` field:

| `id` | Venue |
|---|---|
| `uscis` | USCIS (agency filing) |
| `uscis_asylum_office` | USCIS Asylum Office |
| `aao` | USCIS Administrative Appeals Office |
| `eoir` | EOIR Immigration Court |
| `bia` | Board of Immigration Appeals |
| `ca1` … `ca11` | U.S. Courts of Appeals, First through Eleventh Circuits |
| `cadc` | U.S. Court of Appeals, D.C. Circuit |
| `scotus` | Supreme Court of the United States |

## Exhibit endpoints

Every draft generated with `include_exhibit_list=true` (the default) gets an exhibit list built from its documents — **in `"draft"` status. Approval is the attorney's explicit act**; the API never auto-approves, and any edit after approval reverts the list to `draft`.

The intended lifecycle: **review → edit/reorder → approve → reconcile → export → download**.

All exhibit endpoints require the draft to be linked to a matter (drafts from this API always are) and return the full serialized exhibit list unless noted. The full list shape includes more detail than the generate response's summary: each exhibit carries `id`, `label` (server-derived from position — excluded items show `"—"`), `title`, `description`, `page_start`, `page_end`, `source_document_id`, `letter_override`, `excluded`, `is_manual`; the list carries `id`, `case_id`, `draft_id`, `title`, `label_scheme`, `style_instructions`, `status` (`draft` or `approved`), `approved_at`, `created_at`, `updated_at`.

### `GET /api/v1/drafting/{draft_id}/exhibits`

The draft's exhibit list (auto-created from its documents if missing).

### `POST /api/v1/drafting/{draft_id}/exhibits`

Add a manual exhibit — evidence you will attach yourself. JSON body:

| Field | Required | Type | Description |
|---|---|---|---|
| `title` | Yes | String | Exhibit title |
| `description` | No | String | What the exhibit shows |
| `page_start`, `page_end` | No | Integer | Page range within the assembled exhibit packet |

### `PATCH /api/v1/drafting/{draft_id}/exhibits/{exhibit_id}`

Update one exhibit. All fields optional — send only what changes:

| Field | Type | Description |
|---|---|---|
| `title` | String | Rename the exhibit |
| `description` | String | Update the description |
| `page_start`, `page_end` | Integer | Set the page range |
| `excluded` | Boolean | `true` removes it from the lettering sequence without deleting it |
| `letter_override` | String | Pin a specific label (e.g. `"A-1"`) regardless of position |
| `clear_pages` | Boolean | `true` clears the page range (distinct from "leave unchanged") |
| `clear_letter_override` | Boolean | `true` removes a label override |

### `POST /api/v1/drafting/{draft_id}/exhibits/reorder`

Reorder exhibits; labels re-derive automatically from the new order. Body:

```json
{"exhibit_ids": [3, 1, 2]}
```

### `POST /api/v1/drafting/{draft_id}/exhibits/approve`

Approve the exhibit list (status → `approved`, `approved_at` set). This is the attorney's explicit sign-off. Any later edit reverts the list to `draft`.

### `POST /api/v1/drafting/{draft_id}/exhibits/reconcile`

Rewrite the draft's "see Exhibit X" references to match the current exhibit list — run this after reorders/edits, before final export. Returns per-section results:

```json
{
  "draft_id": 4211,
  "sections": [{"section_id": "section-2", "changed": true, "verified": true, "flagged_reason": null}],
  "replacements": 4,
  "all_verified": true
}
```

If `all_verified` is `false`, check each flagged section's `flagged_reason` — those references need attorney attention.

### `POST /api/v1/drafting/{draft_id}/exhibits/export`

Export the exhibit list as a Word document:

```json
{
  "document_id": 5150,
  "filename": "exhibit_list.docx",
  "download_url": "/api/v1/drafting/4211/exhibits/download?document_id=5150"
}
```

### `GET /api/v1/drafting/{draft_id}/exhibits/download?document_id={document_id}`

Download an exported exhibit-list document (`.docx`).

---

# Outlines API

Generate a finalized case-strategy outline for a matter: eligibility elements, an evidence map against your documents, gaps and risks, and recommended actions — as JSON plus a Word export.

An outline generated here can feed the Drafting API: pass the returned `outline_run_id` as the `outline_run_id` form field of `POST /api/v1/drafting/generate` and the draft consumes the finalized outline instead of re-deriving. See the [Full Flow Guide](FULL_FLOW_GUIDE.md).

Derivation runs **1–4 minutes** on a fresh matter (repeat runs on unchanged material return in seconds), so async mode is the default here too. Sync mode is capped server-side at 8 minutes.

## `POST /api/v1/outlines/generate`

### Request format: `multipart/form-data`

| Field | Required | Type | Default | Description |
|---|---|---|---|---|
| `documents` | See note | File(s) | — | Case documents to analyze. Repeat the field for multiple files. PDF, DOC, DOCX, TXT, MD, RTF; max 64 MB each |
| `document_ids` | See note | String | — | Comma-separated IDs of **already-uploaded** documents (e.g. `"101,102,105"`) to include alongside any files in `documents` |
| `client_id` | One of † | Integer | — | An existing client's ID |
| `client_first_name` | One of † | String | — | With `client_last_name`, creates a new client |
| `client_last_name` | One of † | String | — | See above |
| `client_gender` | No | String | `"Unknown"` | — |
| `client_background` | See note | String | — | Background summary of the client/case |
| `case_id` | One of ‡ | Integer | — | An existing matter's ID |
| `matter_type` | One of ‡ | String | — | With no `case_id`, creates a matter (canonical ID or free text) |
| `jurisdiction` | No | String | — | Controlling circuit (e.g. `"CA9"`) |
| `wait` | No | Query param | `false` | `false` (default) = async job; `true` = block until complete |

† Provide either `client_id`, or both `client_first_name` and `client_last_name`.
‡ Provide either `case_id` or `matter_type`.
**Note:** an outline needs case material to work from — provide at least one of `documents`, `document_ids`, or `client_background`, or the API returns `400`.

Async submission returns the same job-ticket shape as drafting, with `poll_url` under `/api/v1/outlines/jobs/{job_id}`.

## `GET /api/v1/outlines/jobs/{job_id}`

Poll an async outline job every **10–15 seconds** (outlines are much faster than drafts):

```json
{
  "job_id": "...",
  "status": "processing",
  "result": null,
  "error": null
}
```

Outline jobs don't report a `progress` object. A job still `processing` after **30 minutes** is reported as `failed` (interrupted) — resubmit.

### The outline result

```json
{
  "outline_run_id": 3117,
  "client_id": 587,
  "case_id": 902,
  "matter_type": "EB-2 National Interest Waiver",
  "outline": {
    "benefit_type": "...",
    "jurisdiction": "...",
    "eligibility": {},
    "evidence_matrix": [],
    "gaps": {},
    "readiness": {},
    "landmines": [],
    "actions": []
  },
  "docx_download_url": "/api/v1/outlines/3117/download",
  "billing": {"billed": true, "charged_now": true},
  "elapsed_seconds": 143.9
}
```

| Field | Description |
|---|---|
| `outline_run_id` | The outline's ID — pass it to `POST /api/v1/drafting/generate` as `outline_run_id`, or use it with the endpoints below |
| `client_id`, `case_id` | The client and matter used — reuse them for the follow-up draft so the work (and billing) stays on one matter |
| `matter_type` | Display label of the matter type |
| `outline` | The full outline JSON: the benefit's eligibility elements, an evidence matrix mapping your documents to each element, identified gaps and risk items, a readiness summary, and recommended actions. Rich and structured — explore it with `jq` on your first call; the Word export renders the same content for human review |
| `docx_download_url` | Path to the outline's Word export |
| `billing` | Same semantics as drafting — a matter is charged once, so this outline plus a later draft on the same matter is one charge |

## `GET /api/v1/outlines/{run_id}`

Retrieve a generated outline's JSON at any time by its `outline_run_id`.

## `GET /api/v1/outlines/{run_id}/download`

Download the outline as a Word document (`.docx`).

---

## File Requirements

| Constraint | RFE | Drafting & Outlines |
|---|---|---|
| Maximum file size | 64 MB per file | 64 MB per file |
| Supported formats | PDF, DOCX, DOC, TXT | PDF, DOCX, DOC, TXT, MD, RTF |
| Multiple files | Yes — repeat `evidence_files` | Yes — repeat `documents` |

---

## Error Reference

All errors return JSON with a `detail` field. `detail` is a human-readable string, except where noted below (billing and scope errors return a structured object so you can branch on `code`):

```json
{"detail": "Human-readable error message"}
```

```json
{"detail": {"code": "subscribe_required", "message": "An active DraftyAI subscription is required..."}}
```

| Status Code | Meaning | Common causes |
|---|---|---|
| `400` | Bad Request | Missing required field, unsupported file type, file over 64 MB, invalid `outline_mode`/`response_mode`, `case_id` not belonging to the client, outline request with no case material, malformed `document_ids` |
| `401` | Unauthorized | No API key provided |
| `402` | Payment Required | The account can't generate right now. `detail.code` is `subscribe_required` (no active subscription) or `overage_block` (matter allowance used; overages not enabled). `detail.message` explains; additional fields (e.g. `cases_used`, `case_allowance`) give context |
| `403` | Forbidden | Invalid API key; a JWT token instead of an API key; the key's account has no attorney profile; or `detail.code: "scope_denied"` — the key isn't authorized for this endpoint (see [Scopes](#scopes)) |
| `404` | Not Found | The job, draft, outline run, client, or matter ID doesn't exist (or belongs to another account) |
| `413` | Payload Too Large | A file exceeds the 64 MB limit |
| `429` | Too Many Requests | Rate limit exceeded — wait and retry |
| `500` | Internal Server Error | Unexpected server issue, or generation didn't complete — retry or contact support |
| `502` | Bad Gateway | The generation engine reported an error — retry; if persistent, contact support |
| `503` | Service Unavailable | A catalog (e.g. `/document-types`) is temporarily unavailable — retry shortly |
| `504` | Gateway Timeout | Sync-mode generation took too long — use async mode (`?wait=false`) |

---

## Glossary

Terms you'll encounter when working with the DraftyAI API:

| Term | Definition |
|---|---|
| **RFE** | Request for Evidence — a letter from USCIS asking for additional documentation to support a petition |
| **NOID** | Notice of Intent to Deny — USCIS indicates they plan to deny the petition unless the applicant responds |
| **NOIR** | Notice of Intent to Revoke — USCIS indicates they plan to revoke a previously approved petition |
| **Petitioner** | The person or company filing the immigration petition (often the employer) |
| **Beneficiary** | The person who would benefit from the petition (the applicant/employee) |
| **Matter** | A legal matter (case) for a client — e.g. an EB-2 NIW petition. Drafts, outlines, documents, and billing all attach to a matter. `case_id` in the API |
| **Issue** | A specific concern raised by USCIS in an RFE notice that must be addressed |
| **Exhibit** | A labeled piece of evidence (e.g., "Exhibit A: Employment Verification Letter") referenced in a draft |
| **Exhibit list** | The ordered, labeled roster of exhibits attached to a draft. Built automatically; approved explicitly by the attorney |
| **Reconcile** | Rewriting a draft's "see Exhibit X" references to match the current exhibit list after edits or reorders |
| **Outline** | A case-strategy analysis for a matter: eligibility elements, evidence map, gaps, readiness, recommended actions. `outline_run_id` in the API |
| **Notice** | The official USCIS document (RFE, NOID, or NOIR) that an RFE response addresses |
| **Draft** | A generated legal document, formatted for attorney review — never a final filing |
| **Attach marker** | A flag in the drafting result telling the attorney which referenced evidence must be physically attached before filing |
| **Response mode** | RFE only: `with_evidence` (cites exhibits) or `arguments_only` (legal arguments without citations) |

---

## Support

For API access, key provisioning, scope changes, or technical questions: **api@draftyai.com**
