#!/usr/bin/env python3
"""
DraftyAI Drafting API — Python Example

Generates a complete legal draft (with an auto-built exhibit list) from case
documents, then downloads the Word document.

Drafting is LONG-RUNNING BY DESIGN (multi-pass drafting + quality review):
budget 10-30 minutes. This script uses async mode (the API default) and polls
every 45 seconds, printing live progress.

Requirements:
    pip install requests

Usage:
    1. Set your API key below (or as an environment variable)
    2. Run from the repo root:  python examples/drafting_example.py
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

DOCUMENT_TYPE = "eb2_niw"  # a catalog key, or a free label like "Motion to Continue"

DOCUMENTS = [
    "test-kit/evidence/1_Employment_Role_Salary.pdf",
    "test-kit/evidence/2_Awards_Membership_Synthetic.pdf",
    "test-kit/evidence/3_Publications_Media_Synthetic.pdf",
]

CLIENT_FIRST_NAME = "Karina"
CLIENT_LAST_NAME = "Velasquez"
CLIENT_GENDER = "Female"
MATTER_TYPE = "eb2_niw"
VENUE = "uscis"  # REQUIRED: where THIS document is filed (GET /api/v1/drafting/venues)

# Optional free-form drafting instructions (tone, emphasis, points to include)
INSTRUCTIONS = None

# "auto" (default, fast tailored plan) | "full" (outline engine first) | "none"
OUTLINE_MODE = "auto"

# Polling: drafts run 10-30+ minutes. Poll gently, wait generously.
POLL_SECONDS = 45
MAX_WAIT_SECONDS = 90 * 60


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def headers():
    return {"X-API-Key": API_KEY}


def submit_job():
    """Submit the drafting job (async — returns a job ticket immediately)."""
    print("Submitting drafting job (async mode)...")
    print(f"  Document type: {DOCUMENT_TYPE}")
    print(f"  Documents:     {len(DOCUMENTS)} file(s)")
    print()

    files = [("documents", open(path, "rb")) for path in DOCUMENTS]

    data = {
        "document_type": DOCUMENT_TYPE,
        "client_first_name": CLIENT_FIRST_NAME,
        "client_last_name": CLIENT_LAST_NAME,
        "client_gender": CLIENT_GENDER,
        "matter_type": MATTER_TYPE,
        "venue": VENUE,
        "outline_mode": OUTLINE_MODE,
    }
    if INSTRUCTIONS:
        data["instructions"] = INSTRUCTIONS

    resp = requests.post(
        f"{BASE_URL}/api/v1/drafting/generate",
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
    """Poll every POLL_SECONDS, printing progress, until the job finishes."""
    print(f"Polling every {POLL_SECONDS}s (drafts take 10-30 minutes)...")
    print()
    deadline = time.time() + MAX_WAIT_SECONDS

    while time.time() < deadline:
        time.sleep(POLL_SECONDS)
        resp = requests.get(f"{BASE_URL}{poll_url}", headers=headers(), timeout=60)
        resp.raise_for_status()
        job = resp.json()

        line = f"  Status: {job['status']}"
        progress = job.get("progress") or {}
        if progress:
            line += f"  |  phase: {progress.get('phase', '?')}"
            if progress.get("sections_total"):
                line += (
                    f"  |  sections: {progress.get('sections_completed', 0)}"
                    f"/{progress['sections_total']}"
                )
            if progress.get("elapsed_seconds") is not None:
                line += f"  |  elapsed: {progress['elapsed_seconds']:.0f}s"
        print(line)

        if job["status"] == "completed":
            return job["result"]
        if job["status"] == "failed":
            print(f"  Error: {job.get('error', 'Unknown error')}")
            sys.exit(1)

    print(f"  Gave up after {MAX_WAIT_SECONDS}s.")
    sys.exit(1)


def download_docx(download_path, output_filename="draft.docx"):
    """Download the assembled Word document."""
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
    print("DRAFT GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"  Draft ID:      {result['draft_id']}")
    print(f"  Client ID:     {result['client_id']}")
    print(f"  Matter ID:     {result['case_id']}")
    print(f"  Outline mode:  {result['outline_mode_used']}")
    print(f"  Time:          {result.get('elapsed_seconds', 'N/A')}s")
    print()

    # Print each section title with a preview
    for i, section in enumerate(result["content"]["sections"], 1):
        title = section.get("title") or section.get("id") or "Untitled"
        preview = (section.get("content") or "")[:100]
        print(f"  Section {i}: {title}")
        print(f"    {preview}...")
        print()

    # The exhibit list arrives in "draft" status — approval is the attorney's
    # explicit act (POST /api/v1/drafting/{draft_id}/exhibits/approve).
    exhibit_list = result.get("exhibit_list")
    if exhibit_list:
        print(f"  Exhibit list {exhibit_list['list_id']} "
              f"(status: {exhibit_list['status']} — attorney approval pending):")
        for item in exhibit_list["exhibits"]:
            print(f"    Exhibit {item.get('label') or '?'}: {item['title']}")
        print()

    # Items for the reviewing attorney
    review = result["attorney_review"]
    for marker in review["attach_markers"]:
        print(f"  ATTORNEY: attach before filing -> {marker}")
    if review["provide_markers_present"]:
        print("  ATTORNEY: the draft contains [ATTORNEY TO PROVIDE] markers")

    # Download the DOCX
    if result.get("docx_download_url"):
        print()
        download_docx(result["docx_download_url"])
    else:
        print("  No DOCX URL in response (content is still available as JSON)")


if __name__ == "__main__":
    main()
