# Test Kit

Sample files for testing the DraftyAI RFE Response Builder API. Everything here is synthetic — no real personal information.

## How to use these files

These files let you make real API calls without needing actual case documents. The example scripts in [examples/](../examples/) are pre-configured to use these files, so you can run them immediately after cloning the repo.

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

---

## Using the example scripts instead

For a more complete experience, use the ready-made scripts:

- **Python:** `python examples/python_example.py` — handles both sync and async, plus DOCX download
- **Bash:** `bash examples/bash_example.sh` — async mode with automatic polling and download

See [examples/](../examples/) for details.
