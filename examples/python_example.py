#!/usr/bin/env python3
"""
DraftyAI RFE Response Builder — Python Example

Generates a complete RFE response draft from a notice file.
Supports both sync (blocking) and async (polling) modes.

Requirements:
    pip install requests

Usage:
    1. Set your API key below (or as an environment variable)
    2. Run from the repo root:  python examples/python_example.py
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

NOTICE_FILE = "test-kit/notice/drafty_simulated_rfe_i140_e11.pdf"
EVIDENCE_FILES = [
    "test-kit/evidence/1_Employment_Role_Salary.pdf",
    "test-kit/evidence/2_Awards_Membership_Synthetic.pdf",
    "test-kit/evidence/3_Publications_Media_Synthetic.pdf",
]

CLIENT_FIRST_NAME = "Karina"
CLIENT_LAST_NAME = "Velasquez"
CLIENT_GENDER = "Female"

# "with_evidence" or "arguments_only" (omit to auto-detect)
RESPONSE_MODE = None

# True = wait for the result (blocking); False = get a job ID and poll
SYNC_MODE = True


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def headers():
    return {"X-API-Key": API_KEY}


def generate_sync():
    """Submit a request and wait for the result (blocks for ~60-120 seconds)."""
    print("Generating RFE response (sync mode)...")
    print(f"  Notice:   {NOTICE_FILE}")
    print(f"  Evidence: {len(EVIDENCE_FILES)} file(s)")
    print()

    files = [("notice_file", open(NOTICE_FILE, "rb"))]
    for path in EVIDENCE_FILES:
        files.append(("evidence_files", open(path, "rb")))

    data = {
        "client_first_name": CLIENT_FIRST_NAME,
        "client_last_name": CLIENT_LAST_NAME,
        "client_gender": CLIENT_GENDER,
    }
    if RESPONSE_MODE:
        data["response_mode"] = RESPONSE_MODE

    resp = requests.post(
        f"{BASE_URL}/api/v1/rfe/generate",
        headers=headers(),
        files=files,
        data=data,
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()


def generate_async():
    """Submit a request, then poll for the result."""
    print("Generating RFE response (async mode)...")
    print(f"  Notice:   {NOTICE_FILE}")
    print(f"  Evidence: {len(EVIDENCE_FILES)} file(s)")
    print()

    files = [("notice_file", open(NOTICE_FILE, "rb"))]
    for path in EVIDENCE_FILES:
        files.append(("evidence_files", open(path, "rb")))

    data = {
        "client_first_name": CLIENT_FIRST_NAME,
        "client_last_name": CLIENT_LAST_NAME,
        "client_gender": CLIENT_GENDER,
    }
    if RESPONSE_MODE:
        data["response_mode"] = RESPONSE_MODE

    # Submit the job
    resp = requests.post(
        f"{BASE_URL}/api/v1/rfe/generate?wait=false",
        headers=headers(),
        files=files,
        data=data,
        timeout=60,
    )
    resp.raise_for_status()
    job = resp.json()
    job_id = job["job_id"]
    poll_url = f"{BASE_URL}{job['poll_url']}"
    print(f"  Job submitted: {job_id}")
    print(f"  Polling: {poll_url}")
    print()

    # Poll until complete
    while True:
        time.sleep(10)
        status_resp = requests.get(poll_url, headers=headers(), timeout=30)
        status_resp.raise_for_status()
        status = status_resp.json()
        current = status["status"]
        print(f"  Status: {current}")

        if current == "completed":
            return status["result"]
        elif current == "failed":
            print(f"  Error: {status.get('error', 'Unknown error')}")
            sys.exit(1)


def download_docx(download_path, output_filename="rfe_response.docx"):
    """Download the generated Word document."""
    url = f"{BASE_URL}{download_path}"
    print(f"Downloading DOCX from: {url}")
    resp = requests.get(url, headers=headers(), timeout=60)
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

    # Generate the draft
    if SYNC_MODE:
        result = generate_sync()
    else:
        result = generate_async()

    # Show results
    print()
    print("=" * 60)
    print("DRAFT GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"  Project ID:  {result['project_id']}")
    print(f"  Client ID:   {result['client_id']}")
    print(f"  Issues:      {result['issue_count']}")
    print(f"  Time:        {result.get('elapsed_seconds', 'N/A')}s")
    print()

    # Print each issue
    if "content" in result and "issues" in result["content"]:
        for i, issue in enumerate(result["content"]["issues"], 1):
            title = issue.get("title", "Untitled")
            preview = issue.get("response", "")[:120]
            print(f"  Issue {i}: {title}")
            print(f"    {preview}...")
            print()

    # Download the DOCX
    if result.get("docx_download_url"):
        download_docx(result["docx_download_url"])
    else:
        print("  No DOCX URL in response (may need to export separately)")


if __name__ == "__main__":
    main()
