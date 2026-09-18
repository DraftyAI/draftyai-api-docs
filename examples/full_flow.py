#!/usr/bin/env python3
"""
DraftyAI Partner API — Full Flow: outline -> draft -> exhibits -> downloads.

Requirements:
    pip install requests

Run from the repo root of draftyai-api-docs (uses the test-kit files):
    export DRAFTYAI_API_KEY=dfy_live_...
    python examples/full_flow.py
"""

import os
import sys
import time

import requests

API_KEY = os.environ.get("DRAFTYAI_API_KEY", "YOUR_KEY_HERE")
BASE_URL = "https://papi.draftyai.com"

DOCUMENTS = [
    "test-kit/evidence/1_Employment_Role_Salary.pdf",
    "test-kit/evidence/2_Awards_Membership_Synthetic.pdf",
    "test-kit/evidence/3_Publications_Media_Synthetic.pdf",
]

CLIENT = {
    "client_first_name": "Karina",
    "client_last_name": "Velasquez",
    "client_gender": "Female",
}
MATTER_TYPE = "eb2_niw"
DOCUMENT_TYPE = "eb2_niw"
VENUE = "uscis"  # REQUIRED on every generate: where THIS document is filed

# Generous polling budgets. Outlines run 1-4 minutes; drafts run 10-30+.
OUTLINE_POLL_SECONDS = 15
OUTLINE_MAX_WAIT = 30 * 60
DRAFT_POLL_SECONDS = 45
DRAFT_MAX_WAIT = 90 * 60


def headers():
    return {"X-API-Key": API_KEY}


def poll_job(poll_url, interval, max_wait, label):
    """Poll a job URL until completed/failed. Returns the result dict."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        time.sleep(interval)
        resp = requests.get(f"{BASE_URL}{poll_url}", headers=headers(), timeout=60)
        resp.raise_for_status()
        job = resp.json()
        progress = job.get("progress") or {}
        detail = ""
        if progress:
            detail = f"  phase={progress.get('phase', '?')}"
            if progress.get("sections_total"):
                detail += (
                    f"  sections={progress.get('sections_completed', 0)}"
                    f"/{progress['sections_total']}"
                )
        print(f"  [{label}] {job['status']}{detail}")
        if job["status"] == "completed":
            return job["result"]
        if job["status"] == "failed":
            print(f"  [{label}] ERROR: {job.get('error')}")
            sys.exit(1)
    print(f"  [{label}] Gave up after {max_wait}s")
    sys.exit(1)


def download(path, filename):
    resp = requests.get(f"{BASE_URL}{path}", headers=headers(), timeout=120)
    resp.raise_for_status()
    with open(filename, "wb") as f:
        f.write(resp.content)
    print(f"  Saved: {filename}")


def main():
    if API_KEY == "YOUR_KEY_HERE":
        print("Set DRAFTYAI_API_KEY first.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 1: Outline (async submit + poll; 1-4 minutes)
    # ------------------------------------------------------------------
    print("Step 1: Generating case-strategy outline...")
    files = [("documents", open(p, "rb")) for p in DOCUMENTS]
    resp = requests.post(
        f"{BASE_URL}/api/v1/outlines/generate",
        headers=headers(),
        files=files,
        data={**CLIENT, "matter_type": MATTER_TYPE},
        timeout=120,
    )
    resp.raise_for_status()
    outline = poll_job(
        resp.json()["poll_url"], OUTLINE_POLL_SECONDS, OUTLINE_MAX_WAIT, "outline"
    )

    outline_run_id = outline["outline_run_id"]
    client_id = outline["client_id"]
    case_id = outline["case_id"]
    print(f"  Outline run {outline_run_id} on matter {case_id} (client {client_id})")
    download(outline["docx_download_url"], "strategy_outline.docx")

    # >>> In a real integration, the attorney reviews the outline here. <<<

    # ------------------------------------------------------------------
    # Step 2: Draft from the outline (async submit + poll; 10-30 minutes)
    # ------------------------------------------------------------------
    print("\nStep 2: Generating the draft (10-30 minutes — be patient)...")
    resp = requests.post(
        f"{BASE_URL}/api/v1/drafting/generate",
        headers=headers(),
        data={
            "document_type": DOCUMENT_TYPE,
            "client_id": client_id,
            "case_id": case_id,
            "outline_run_id": outline_run_id,
            "venue": VENUE,
        },
        timeout=120,
    )
    resp.raise_for_status()
    draft = poll_job(
        resp.json()["poll_url"], DRAFT_POLL_SECONDS, DRAFT_MAX_WAIT, "draft"
    )

    draft_id = draft["draft_id"]
    print(f"  Draft {draft_id}: {len(draft['content']['sections'])} sections, "
          f"outline_mode_used={draft['outline_mode_used']}, "
          f"{draft['elapsed_seconds']}s")
    for marker in draft["attorney_review"]["attach_markers"]:
        print(f"  ATTORNEY: attach before filing -> {marker}")
    if draft["attorney_review"]["provide_markers_present"]:
        print("  ATTORNEY: draft contains [ATTORNEY TO PROVIDE] markers")

    # ------------------------------------------------------------------
    # Step 3: Exhibits — review -> approve -> reconcile -> export
    # ------------------------------------------------------------------
    print("\nStep 3: Exhibit list lifecycle...")
    ex_base = f"{BASE_URL}/api/v1/drafting/{draft_id}/exhibits"

    listing = requests.get(ex_base, headers=headers(), timeout=60).json()
    print(f"  {len(listing['exhibits'])} exhibits, status={listing['status']}")
    for item in listing["exhibits"]:
        print(f"    Exhibit {item['label']}: {item['title']}")

    # >>> In a real integration, the attorney edits here:
    #     PATCH {ex_base}/{exhibit_id}   (title/description/pages/excluded)
    #     POST  {ex_base}/reorder        {"exhibit_ids": [...]}            <<<

    approved = requests.post(f"{ex_base}/approve", headers=headers(), timeout=60)
    approved.raise_for_status()
    print(f"  Approved (status={approved.json()['status']})")

    reconciled = requests.post(f"{ex_base}/reconcile", headers=headers(), timeout=300)
    reconciled.raise_for_status()
    rec = reconciled.json()
    print(f"  Reconciled: {rec['replacements']} reference(s) updated, "
          f"all_verified={rec['all_verified']}")

    exported = requests.post(f"{ex_base}/export", headers=headers(), timeout=120)
    exported.raise_for_status()
    download(exported.json()["download_url"], "exhibit_list.docx")

    # ------------------------------------------------------------------
    # Step 4: Download the final draft (after reconcile)
    # ------------------------------------------------------------------
    print("\nStep 4: Downloading the draft...")
    download(f"/api/v1/drafting/{draft_id}/download", "draft.docx")

    print("\nDone. Deliverables: strategy_outline.docx, draft.docx, exhibit_list.docx")


if __name__ == "__main__":
    main()
