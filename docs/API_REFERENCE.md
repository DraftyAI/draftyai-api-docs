# API Reference

Complete technical reference for the DraftyAI RFE Response Builder API.

**Base URL:** `https://papi.draftyai.com`

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

---

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

---

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

---

## Response Modes

| Mode | When to use | What happens |
|---|---|---|
| `with_evidence` | You have supporting documents (employment letters, awards, publications, etc.) | The API analyzes your evidence, creates exhibits, and cites them in the draft |
| `arguments_only` | You don't have documents to upload right now | The AI generates legal arguments for each issue without exhibit citations |

**Which should I choose?**

- If you have **any** supporting files for the case, use `with_evidence`. The draft will be stronger because it references specific evidence.
- If you only have the RFE notice and want a quick first draft, use `arguments_only`. You can always re-generate later with evidence.
- If you **omit** the `response_mode` field, the API decides automatically: it uses `with_evidence` if you sent evidence files, `arguments_only` if you didn't.

---

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

---

## Granular Endpoints

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

## Error Reference

All errors return JSON with a `detail` field:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning | Common causes |
|---|---|---|
| `400` | Bad Request | Missing required field, invalid file type, invalid `response_mode` value |
| `401` | Unauthorized | No API key provided |
| `403` | Forbidden | Invalid API key, or using a JWT token instead of an API key |
| `404` | Not Found | The project, client, or resource ID doesn't exist |
| `413` | Payload Too Large | A file exceeds the 64 MB limit |
| `429` | Too Many Requests | Rate limit exceeded — wait and retry |
| `500` | Internal Server Error | Unexpected server issue — retry or contact support |
| `504` | Gateway Timeout | Generation took too long — use async mode (`?wait=false`) |

---

## Rate Limits

| Limit | Default |
|---|---|
| Requests per minute | 60 |
| Requests per day | 1,000 |

When you exceed the limit, the API returns `429 Too Many Requests`. Wait for the limit to reset (1 minute for per-minute limits) and retry.

---

## File Requirements

| Constraint | Value |
|---|---|
| Maximum file size | 64 MB per file |
| Supported notice formats | PDF, DOCX, DOC, TXT |
| Supported evidence formats | PDF, DOCX, DOC, TXT |
| Multiple evidence files | Yes — repeat the `evidence_files` field |

---

## Glossary

Terms you'll encounter when working with immigration RFE responses:

| Term | Definition |
|---|---|
| **RFE** | Request for Evidence — a letter from USCIS asking for additional documentation to support a petition |
| **NOID** | Notice of Intent to Deny — USCIS indicates they plan to deny the petition unless the applicant responds |
| **NOIR** | Notice of Intent to Revoke — USCIS indicates they plan to revoke a previously approved petition |
| **Petitioner** | The person or company filing the immigration petition (often the employer) |
| **Beneficiary** | The person who would benefit from the petition (the applicant/employee) |
| **Issue** | A specific concern raised by USCIS in the notice that must be addressed |
| **Exhibit** | A labeled piece of evidence (e.g., "Exhibit A: Employment Verification Letter") referenced in the response |
| **Notice** | The official USCIS document (RFE, NOID, or NOIR) that the response addresses |
| **Draft** | The generated response letter, formatted as a professional legal document |
| **Response mode** | How the API generates the draft: `with_evidence` (cites exhibits) or `arguments_only` (legal arguments without citations) |

---

## Support

For API access, key provisioning, or technical questions: **api@draftyai.com**
