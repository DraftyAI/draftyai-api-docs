# Quickstart Guide

A step-by-step walkthrough of your first API call. By the end, you'll have generated a real RFE response draft.

## Before you begin

You need:

- [ ] Your **API key** (shared via 1Password, starts with `dfy_live_`)
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
  -X POST https://papi.draftyai.com/api/v1/rfe/generate \
  -H "X-API-Key: YOUR_KEY_HERE"
```

**What to expect:**

| You see | What it means |
|---|---|
| `HTTP Status: 400` | Your key is valid. The 400 is expected because we didn't send any files yet. |
| `HTTP Status: 401` or `403` | Your key is invalid or missing. Double-check you copied it correctly. |

---

## Step 2: Generate your first draft

Navigate into the repo folder, then run this command. It sends the sample RFE notice to the API using the test files included in this repo:

```bash
cd draftyai-api-docs

curl -X POST https://papi.draftyai.com/api/v1/rfe/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "notice_file=@test-kit/notice/drafty_simulated_rfe_i140_e11.pdf" \
  -F "client_first_name=Karina" \
  -F "client_last_name=Velasquez" \
  -F "client_gender=Female"
```

**What each flag means:**

| Flag | Purpose |
|---|---|
| `-X POST` | This is a POST request (sending data to the server) |
| `-H "X-API-Key: ..."` | Your authentication header |
| `-F "notice_file=@..."` | The RFE notice file to analyze. The `@` means "read from this file path" |
| `-F "client_first_name=..."` | The client's first name (used in the generated draft) |
| `-F "client_last_name=..."` | The client's last name |
| `-F "client_gender=..."` | The client's gender |

**This will take about 60–120 seconds.** The API is reading the notice, identifying every issue USCIS raised, generating legal arguments for each one, and producing a Word document. Be patient — don't cancel the request.

> **Tip:** To pretty-print the JSON response, pipe it through jq: add `| jq .` at the end of the command.

---

## Step 3: Read the response

You'll get back a JSON object like this:

```json
{
  "project_id": 1042,
  "client_id": 587,
  "draft_version_id": 312,
  "content": {
    "intro": "Dear USCIS Officer, this letter is submitted in response to...",
    "issues": [
      {
        "title": "Extraordinary Ability - Original Contributions",
        "response": "The beneficiary has made original contributions of major significance..."
      }
    ],
    "conclusion": "For the foregoing reasons, we respectfully request...",
    "legal_references": ["8 CFR § 204.5(h)(3)", "Matter of Dhanasar, 26 I&N Dec. 884"]
  },
  "docx_download_url": "/notice-responses/1042/exports/89/download",
  "issue_count": 3,
  "elapsed_seconds": 78.2
}
```

**What each field means:**

| Field | Description |
|---|---|
| `project_id` | Unique ID for this RFE project (use it to access the project later) |
| `client_id` | Unique ID for the client record that was created |
| `draft_version_id` | Version number of the generated draft |
| `content` | The actual draft text, broken into sections (intro, issues, conclusion) |
| `content.issues` | Array of responses — one for each issue identified in the RFE notice |
| `docx_download_url` | URL path to download the formatted Word document (see Step 4) |
| `issue_count` | How many issues were found in the notice |
| `elapsed_seconds` | How long the generation took |

---

## Step 4: Download the Word document

Use the `docx_download_url` from the response to download the formatted DOCX file:

```bash
curl -H "X-API-Key: YOUR_KEY_HERE" \
  "https://papi.draftyai.com/notice-responses/1042/exports/89/download" \
  -o rfe_response.docx
```

Replace the URL path with the actual `docx_download_url` from your response. The file will be saved as `rfe_response.docx` in your current folder.

---

## What just happened?

Behind the scenes, that single API call did all of this:

1. **Created a client** record for "Karina Velasquez"
2. **Uploaded the notice** PDF to secure cloud storage
3. **Analyzed the notice** using AI to extract every issue USCIS raised, the receipt number, petitioner/beneficiary names, and deadlines
4. **Generated legal arguments** for each issue using a specialized legal AI model
5. **Produced a Word document** formatted as a professional response letter
6. **Returned everything** to you in one response

If you had also sent evidence files (employment letters, awards, publications, etc.), the API would have additionally created exhibits from those documents and cited them in the response.

---

## Try it with evidence files

The test kit includes sample evidence documents. To generate a draft that cites evidence:

```bash
curl -X POST https://papi.draftyai.com/api/v1/rfe/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "notice_file=@test-kit/notice/drafty_simulated_rfe_i140_e11.pdf" \
  -F "evidence_files=@test-kit/evidence/1_Employment_Role_Salary.pdf" \
  -F "evidence_files=@test-kit/evidence/2_Awards_Membership_Synthetic.pdf" \
  -F "evidence_files=@test-kit/evidence/3_Publications_Media_Synthetic.pdf" \
  -F "evidence_files=@test-kit/evidence/4_Judging_Contributions_Synthetic.pdf" \
  -F "evidence_files=@test-kit/evidence/A5_Beneficiary_Statement_Synthetic.pdf" \
  -F "client_first_name=Karina" \
  -F "client_last_name=Velasquez" \
  -F "client_gender=Female" \
  -F "response_mode=with_evidence"
```

Notice how `evidence_files` is repeated for each file — that's how you send multiple files in one request.

---

## Using Python instead of curl

If you prefer Python, here's the same thing:

```python
import requests

API_KEY = "YOUR_KEY_HERE"

response = requests.post(
    "https://papi.draftyai.com/api/v1/rfe/generate",
    headers={"X-API-Key": API_KEY},
    files={"notice_file": open("test-kit/notice/drafty_simulated_rfe_i140_e11.pdf", "rb")},
    data={
        "client_first_name": "Karina",
        "client_last_name": "Velasquez",
        "client_gender": "Female",
    },
    timeout=300,  # 5 minutes — the API needs time to generate
)

result = response.json()
print(f"Draft generated! {result['issue_count']} issues addressed.")
print(f"Download DOCX: https://papi.draftyai.com{result['docx_download_url']}")
```

For a complete, ready-to-run script, see [examples/python_example.py](../examples/python_example.py).

---

## Common errors

| Error | What it means | How to fix |
|---|---|---|
| `401 Unauthorized` | API key is missing | Add the `-H "X-API-Key: ..."` header |
| `403 Forbidden` | API key is invalid or this endpoint requires an API key | Double-check your key; JWT tokens from the web app don't work here |
| `400 Bad Request` | Missing required fields | Make sure you're sending `notice_file`, `client_first_name`, and `client_last_name` |
| `413 Payload Too Large` | File exceeds 64 MB | Reduce the file size or split into smaller documents |
| `429 Too Many Requests` | Rate limit exceeded | Wait a minute and try again (default: 60 requests/minute) |
| `500 Internal Server Error` | Something went wrong on our end | Retry the request; if persistent, contact api@draftyai.com |
| `504 Gateway Timeout` | The generation took too long | Use async mode: add `?wait=false` to the URL (see [API Reference](API_REFERENCE.md#async-mode-polling)) |

---

## Next steps

- [API Reference](API_REFERENCE.md) — full technical documentation with every endpoint and field
- [examples/](../examples/) — working Python and bash scripts to copy into your project
- [test-kit/](../test-kit/) — details on the sample files and test client profile
