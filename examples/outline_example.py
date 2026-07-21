#!/usr/bin/env python3
"""
DraftyAI Outlines API — Python Example

Generates a finalized case-strategy outline (eligibility elements, evidence
map, gaps, recommended actions) from case documents, then downloads the Word
export.

Derivation runs 1-4 minutes on a fresh matter, so this script uses async mode
(the API default) and polls every 15 seconds.

The returned outline_run_id can feed the Drafting API: pass it as the
`outline_run_id` form field of POST /api/v1/drafting/generate and the draft
is built on this reviewed outline. See docs/FULL_FLOW_GUIDE.md.

Requirements:
    pip install requests

Usage:
    1. Set your API key below (or as an environment variable)
    2. Run from the repo root:  python examples/outline_example.py
"""

import os
import sys
import time
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("DRAFTYAI_API_KEY", "YOUR_KEY_HERE")
BASE_URL = "https://papi.draftyai.com"

DOCUMENTS = [
    "test-kit/evidence/1_Employment_Role_Salary.pdf",
    "test-kit/evidence/2_Awards_Membership_Synthetic.pdf",
    "test-kit/evidence/3_Publications_Media_Synthetic.pdf",
]

CLIENT_FIRST_NAME = "Karina"
CLIENT_LAST_NAME = "Velasquez"
CLIENT_GENDER = "Female"
MATTER_TYPE = "eb2_niw"

# Optional: controlling circuit, e.g. "CA9"
JURISDICTION = None

POLL_SECONDS = 15
MAX_WAIT_SECONDS = 30 * 60


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def headers():
    return {"X-API-Key": API_KEY}


def submit_job():
    """Submit the outline job (async — returns a job ticket immediately)."""
    print("Submitting outline job (async mode)...")
    print(f"  Documents: {len(DOCUMENTS)} file(s)")
    print(f"  Matter:    {MATTER_TYPE}")
    print()

    files = [("documents", open(path, "rb")) for path in DOCUMENTS]

    data = {
        "client_first_name": CLIENT_FIRST_NAME,
        "client_last_name": CLIENT_LAST_NAME,
        "client_gender": CLIENT_GENDER,
        "matter_type": MATTER_TYPE,
    }
    if JURISDICTION:
        data["jurisdiction"] = JURISDICTION

    resp = requests.post(
        f"{BASE_URL}/api/v1/outlines/generate",
        headers=headers(),
        files=files,
        data=data,
        timeout=120,
    )
    resp.raise_for_status()
    job = resp.json()
    print(f"  Job submitted: {job['job_id']}")
    print(f"  Polling: {BASE_URL}{job['poll_url']}")
    print()
    return job["poll_url"]


def poll_until_done(poll_url):
    """Poll every POLL_SECONDS until the job finishes."""
    print(f"Polling every {POLL_SECONDS}s (outlines take 1-4 minutes)...")
    print()
    deadline = time.time() + MAX_WAIT_SECONDS

    while time.time() < deadline:
        time.sleep(POLL_SECONDS)
        resp = requests.get(f"{BASE_URL}{poll_url}", headers=headers(), timeout=60)
        resp.raise_for_status()
        job = resp.json()
        print(f"  Status: {job['status']}")

        if job["status"] == "completed":
            return job["result"]
        if job["status"] == "failed":
            print(f"  Error: {job.get('error', 'Unknown error')}")
            sys.exit(1)

    print(f"  Gave up after {MAX_WAIT_SECONDS}s.")
    sys.exit(1)


def download_docx(download_path, output_filename="strategy_outline.docx"):
    """Download the outline's Word export."""
    url = f"{BASE_URL}{download_path}"
    print(f"Downloading DOCX from: {url}")
    resp = requests.get(url, headers=headers(), timeout=120)
    resp.raise_for_status()
    with open(output_filename, "wb") as f:
        f.write(resp.content)
    print(f"  Saved to: {output_filename}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if API_KEY == "YOUR_KEY_HERE":
        print("ERROR: Set your API key first.")
        print("  Option 1: Edit API_KEY in this script")
        print("  Option 2: export DRAFTYAI_API_KEY=dfy_live_...")
        sys.exit(1)

    poll_url = submit_job()
    result = poll_until_done(poll_url)

    # Show results
    print()
    print("=" * 60)
    print("OUTLINE GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"  Outline run ID: {result['outline_run_id']}")
    print(f"  Client ID:      {result['client_id']}")
    print(f"  Matter ID:      {result['case_id']}")
    print(f"  Matter type:    {result['matter_type']}")
    print(f"  Time:           {result.get('elapsed_seconds', 'N/A')}s")
    print()

    # The outline JSON is rich — print its top-level shape as a teaser
    outline = result.get("outline") or {}
    print("  Outline contents (top-level keys):")
    for key in outline:
        print(f"    - {key}")
    print()

    # Download the Word export (the attorney-review artifact)
    if result.get("docx_download_url"):
        download_docx(result["docx_download_url"])

    print()
    print("Next: feed this outline into the Drafting API —")
    print(f"  POST /api/v1/drafting/generate with "
          f"outline_run_id={result['outline_run_id']}, "
          f"client_id={result['client_id']}, case_id={result['case_id']}")
    print("  (see docs/FULL_FLOW_GUIDE.md)")


if __name__ == "__main__":
    main()
