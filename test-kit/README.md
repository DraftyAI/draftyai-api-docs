# Test Kit

Sample files for testing the DraftyAI API — all three products. Everything here is synthetic — no real personal information.

## How to use these files

These files let you make real API calls without needing actual case documents. The example scripts in [examples/](../examples/) are pre-configured to use these files, so you can run them immediately after cloning the repo.

The notice file is specific to the RFE Response Builder, but the **evidence PDFs work as inputs for every product** — send them as `evidence_files` to the RFE API, or as `documents` to the Drafting and Outlines APIs.

You can also reference these files directly in your own `curl` commands:

```bash
curl -X POST https://papi.draftyai.com/api/v1/rfe/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "notice_file=@test-kit/notice/drafty_simulated_rfe_i140_e11.pdf" \
  -F "client_first_name=Karina" \
  -F "client_last_name=Velasquez" \
  -F "client_gender=Female"
```

---

## Test Client Profile

Use these values for the `client_*` fields in your API requests:

| Field | Value |
|---|---|
| `client_first_name` | `Karina` |
| `client_last_name` | `Velasquez` |
| `client_gender` | `Female` |

**Full profile (for reference only — the API extracts most details from the notice automatically):**

| Detail | Value |
|---|---|
| Full name | Karina Solene Velasquez |
| Date of birth | 1988-06-15 |
| Birth country | Mexico |
| Nationality | Mexican |
| Resides | San Diego, California, USA |
| Receipt number | 2591234567 |
| Case type | I-140 EB-1A (Extraordinary Ability) |

> **Note:** the evidence PDFs are benefit-type-agnostic. The Drafting and Outlines examples in this repo demonstrate an **EB-2 NIW** (`eb2_niw`) petition support letter, but the same files work for any `document_type` — including `eb1a_petition`, which matches this client's actual EB-1A case. Choose the `document_type`/`matter_type` that fits your matter.

---

## Files

### RFE Notice (required for every request)

| File | Description |
|---|---|
| `notice/drafty_simulated_rfe_i140_e11.pdf` | Simulated I-140 EB-1A RFE notice from USCIS |

This is the main document that the API analyzes. It contains several issues that USCIS has raised about the petition.

### Evidence Documents (optional — for `with_evidence` mode)

| File | What it contains |
|---|---|
| `evidence/1_Employment_Role_Salary.pdf` | Employment verification, role description, and salary documentation |
| `evidence/2_Awards_Membership_Synthetic.pdf` | Professional awards and membership certificates |
| `evidence/3_Publications_Media_Synthetic.pdf` | Published articles and media coverage |
| `evidence/4_Judging_Contributions_Synthetic.pdf` | Peer review and judging contributions |
| `evidence/5_Translations_Synthetic.pdf` | Document translations |
| `evidence/A5_Beneficiary_Statement_Synthetic.pdf` | Personal statement from the beneficiary |

When you send evidence files, the API creates labeled exhibits from them and cites them in the response draft. You can send all of them, some of them, or none.

**These same evidence PDFs also work as drafting and outline inputs** — see the Drafting API test call below.

---

## Quick commands

### Arguments-only mode (fastest — no evidence needed)

```bash
curl -X POST https://papi.draftyai.com/api/v1/rfe/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "notice_file=@test-kit/notice/drafty_simulated_rfe_i140_e11.pdf" \
  -F "client_first_name=Karina" \
  -F "client_last_name=Velasquez" \
  -F "client_gender=Female" \
  -F "response_mode=arguments_only"
```

### With evidence (full pipeline)

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
  -F "client_gender=Female"
```

### Download the generated DOCX

After a successful generation, use the `docx_download_url` from the JSON response:

```bash
curl -H "X-API-Key: YOUR_KEY_HERE" \
  "https://papi.draftyai.com/notice-responses/{project_id}/exports/{artifact_id}/download" \
  -o rfe_response.docx
```

Replace `{project_id}` and `{artifact_id}` with the actual values from your response.

### Drafting API test call (uses the same evidence files)

Generate a full EB-2 NIW support letter draft from the test evidence. This submits an async job — poll the returned `poll_url` every 30–60 seconds and budget 10–30 minutes (see the [Drafting Quickstart](../docs/DRAFTING_QUICKSTART.md)):

```bash
curl -X POST https://papi.draftyai.com/api/v1/drafting/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "document_type=eb2_niw" \
  -F "documents=@test-kit/evidence/1_Employment_Role_Salary.pdf" \
  -F "documents=@test-kit/evidence/2_Awards_Membership_Synthetic.pdf" \
  -F "documents=@test-kit/evidence/3_Publications_Media_Synthetic.pdf" \
  -F "documents=@test-kit/evidence/4_Judging_Contributions_Synthetic.pdf" \
  -F "documents=@test-kit/evidence/A5_Beneficiary_Statement_Synthetic.pdf" \
  -F "client_first_name=Karina" \
  -F "client_last_name=Velasquez" \
  -F "client_gender=Female" \
  -F "matter_type=eb2_niw" \
  -F "venue=uscis"
```

The same call against `/api/v1/outlines/generate` (drop `document_type`) produces a case-strategy outline in 1–4 minutes — a faster way to verify your key and documents before committing to a full draft.

---

## Using the example scripts instead

For a more complete experience, use the ready-made scripts:

- **RFE (Python):** `python examples/python_example.py` — handles both sync and async, plus DOCX download
- **RFE (Bash):** `bash examples/bash_example.sh` — async mode with automatic polling and download
- **Drafting (Python):** `python examples/drafting_example.py` — async job, live progress, exhibit list, DOCX download
- **Drafting (Bash):** `bash examples/drafting_example.sh` — async mode with progress polling and download
- **Outlines (Python):** `python examples/outline_example.py` — outline job, plus how to feed the outline into a draft

See [examples/](../examples/) for details.
