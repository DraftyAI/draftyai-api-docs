# Full Flow Guide — Outline → Draft → Exhibits → Downloads

The complete enterprise integration story. This is how a firm-grade system uses the DraftyAI API end to end:

```
  ┌────────────────────┐      ┌────────────────────────┐      ┌───────────────────────┐
  │ 1. OUTLINE          │      │ 2. DRAFT               │      │ 3. EXHIBITS            │
  │                     │      │                        │      │                        │
  │ POST /outlines/     │      │ POST /drafting/        │      │ GET  .../exhibits      │
  │      generate       │─────>│      generate          │─────>│ PATCH/reorder edits    │
  │ poll 10-15 s        │ run  │      outline_run_id=…  │      │ POST .../approve       │
  │ → outline JSON+DOCX │  id  │ poll 30-60 s (10-30 m) │      │ POST .../reconcile     │
  └────────────────────┘      │ → draft JSON+DOCX      │      │ POST .../export        │
                               └────────────────────────┘      │ GET  .../download      │
                                                               └───────────────────────┘
```

**Why outline first?** The outline is the reviewable strategy artifact: eligibility elements, an evidence map against the documents you uploaded, gaps, and recommended actions. Your attorney reviews it (JSON in your UI, or the Word export) *before* you spend 10–30 minutes of drafting time. When you then pass its `outline_run_id` to the Drafting API, the draft is built on that reviewed strategy instead of re-deriving from scratch — and because billing is per matter, the outline and the draft on the same matter count as **one** charge.

You can skip straight to `POST /api/v1/drafting/generate` (its default `outline_mode=auto` plans a structure for you) — this guide is for integrations that want the strategy checkpoint in between.

---

## The flow, step by step

### Step 1: Generate the outline

```bash
curl -X POST https://papi.draftyai.com/api/v1/outlines/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "documents=@test-kit/evidence/1_Employment_Role_Salary.pdf" \
  -F "documents=@test-kit/evidence/2_Awards_Membership_Synthetic.pdf" \
  -F "documents=@test-kit/evidence/3_Publications_Media_Synthetic.pdf" \
  -F "client_first_name=Karina" \
  -F "client_last_name=Velasquez" \
  -F "client_gender=Female" \
  -F "matter_type=eb2_niw"
```

Returns a job ticket immediately. Poll `poll_url` every 10–15 seconds (derivation runs 1–4 minutes). The completed result gives you:

- `outline_run_id` — the handle for Step 2
- `client_id` and `case_id` — **save these**; passing them back keeps everything on one matter
- `outline` — the strategy JSON for your review UI
- `docx_download_url` — the same outline as a Word document for attorney review

> **Attorney checkpoint.** Show the outline to the reviewing attorney here. If the gaps or missing-evidence items are serious, gather more documents and generate a fresh outline before drafting.

### Step 2: Draft from the outline

Pass the outline's run ID, plus the same `client_id`/`case_id`, so nothing is re-derived and the matter isn't duplicated:

```bash
curl -X POST https://papi.draftyai.com/api/v1/drafting/generate \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -F "document_type=eb2_niw" \
  -F "client_id=587" \
  -F "case_id=902" \
  -F "outline_run_id=3117"
```

Documents already uploaded in Step 1 are attached to the matter — you don't need to re-send them. Poll the returned `poll_url` every **30–60 seconds**; the job reports a live `progress` object (`phase`, `sections_completed`/`sections_total`). Budget **10–30 minutes**.

The completed result's `outline_mode_used` will be `"full"` — confirmation the draft consumed your finalized outline.

### Step 3: Exhibits lifecycle

The draft arrives with an auto-built exhibit list in `"draft"` status — **never auto-approved**; approval is the attorney's explicit act.

1. `GET /api/v1/drafting/{draft_id}/exhibits` — review the full list (page ranges, source documents)
2. `PATCH .../exhibits/{exhibit_id}` and `POST .../exhibits/reorder` — titles, descriptions, page ranges, exclusions, order
3. `POST .../exhibits/approve` — the attorney signs off (any later edit reverts to `draft`)
4. `POST .../exhibits/reconcile` — rewrites the draft's "see Exhibit X" references to match the approved order; check `all_verified` in the response
5. `POST .../exhibits/export` then `GET .../exhibits/download?document_id=...` — the exhibit list as its own Word document

### Step 4: Downloads

- Draft: `GET /api/v1/drafting/{draft_id}/download` (re-download **after** reconciling so exhibit references are current)
- Exhibit list: the `download_url` from the export call
- Outline: `GET /api/v1/outlines/{run_id}/download`

Everything is stored durably — you can re-fetch JSON and re-download documents at any time.

---

## Complete runnable script

The whole flow is shipped as [examples/full_flow.py](../examples/full_flow.py) — the same script shown below. Set `DRAFTYAI_API_KEY` and run it from the repo root:

```bash
export DRAFTYAI_API_KEY=dfy_live_...
python examples/full_flow.py
```

```python
#!/usr/bin/env python3
"""
DraftyAI Partner API — Full Flow: outline -> draft -> exhibits -> downloads.

Requirements:
    pip install requests

Run from the repo root of draftyai-api-docs (uses the test-kit files).
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
```

---

## Integration tips

- **Persist IDs, not just files.** Store `client_id`, `case_id`, `draft_id`, and `outline_run_id` in your system. Every artifact is re-fetchable later (`GET /api/v1/drafting/{draft_id}`, `GET /api/v1/outlines/{run_id}`, and the download endpoints).
- **One matter = one charge.** Keep related work on the same `case_id`. The outline and draft above cost one matter charge, not two.
- **Poll politely.** 30–60 seconds for drafts, 10–15 seconds for outlines. Faster polling doesn't speed anything up and eats your rate limit.
- **Handle `failed` by resubmitting.** Jobs interrupted by a service restart report `failed` with an "interrupted" error (after 90 minutes for drafts, 30 for outlines). Resubmitting with the same `client_id`/`case_id` won't double-charge the matter.
- **Reconcile before final export.** If exhibits were edited or reordered, run reconcile, then re-download the draft DOCX.
- **The attorney is the finisher.** `attach_markers`, `[ATTORNEY TO PROVIDE]` markers, and exhibit approval are deliberate human checkpoints — surface them in your UI rather than hiding them.

## Next steps

- [API Reference](API_REFERENCE.md) — every field on every endpoint used above
- [Drafting Quickstart](DRAFTING_QUICKSTART.md) — the draft-only flow, explained step by step
- [examples/](../examples/) — smaller single-product scripts
