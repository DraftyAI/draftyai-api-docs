# Changelog

Notable changes to the DraftyAI Partner API and this documentation.

## 2026-07-14 — Drafting API + Outlines API

The API grows from one product to three. The **Drafting API** and **Outlines API** launch in beta for authorized partners; the RFE Response Builder API is unchanged.

### New: Drafting API (`/api/v1/drafting`) — beta for authorized partners

- `POST /api/v1/drafting/generate` — one multipart call produces a complete legal draft (brief, motion, cover letter, petition support letter, ...) from case documents: structured JSON sections, an auto-built exhibit list (delivered in `draft` status — attorney approval is explicit), an `attorney_review` block, and a durable Word document.
- **Async by default** (`?wait=false`) — generation runs 10–30+ minutes by design (multi-pass drafting, citation verification, quality review). Poll `GET /api/v1/drafting/jobs/{job_id}` every 30–60 seconds; while processing it reports a `progress` object with the current phase and section counts.
- Catalogs: `GET /document-types`, `GET /matter-types`, `GET /venues`. `document_type` also accepts free-form labels — the API plans a tailored structure.
- Retrieval any time later: `GET /api/v1/drafting/{draft_id}` and `GET /api/v1/drafting/{draft_id}/download`.
- Full exhibit-list lifecycle, keyed by draft: `GET/POST /{draft_id}/exhibits`, `PATCH /{draft_id}/exhibits/{exhibit_id}`, `POST .../reorder`, `POST .../approve`, `POST .../reconcile` (rewrites "see Exhibit X" references), `POST .../export`, `GET .../download`.

### New: Outlines API (`/api/v1/outlines`) — beta for authorized partners

- `POST /api/v1/outlines/generate` — a finalized case-strategy outline (eligibility elements, evidence map, gaps, readiness, recommended actions) as JSON plus a Word export. Async by default; derivation runs 1–4 minutes.
- `GET /api/v1/outlines/jobs/{job_id}`, `GET /api/v1/outlines/{run_id}`, `GET /api/v1/outlines/{run_id}/download`.
- Outlines feed drafting: pass the returned `outline_run_id` to `POST /api/v1/drafting/generate` and the draft is built on the finalized outline.

### API-wide

- **Scoped keys:** API keys may now be restricted to product prefixes. Out-of-scope requests return `403` with `detail.code: "scope_denied"`. Contact api@draftyai.com to change a key's scope.
- **Billing responses:** drafting and outline results include a `billing` object (`billed`, `charged_now`). A matter is charged once — an outline plus a draft on the same matter is one charge. Accounts that can't generate receive `402` with `detail.code` of `subscribe_required` or `overage_block`.
- **New error codes documented:** `402` (billing), `403 scope_denied`, `502` (generation engine).

### Documentation

- Repo restructured as the documentation home for the whole platform: new platform [README](README.md), [Drafting Quickstart](docs/DRAFTING_QUICKSTART.md), [Full Flow Guide](docs/FULL_FLOW_GUIDE.md) (outline → draft → exhibits → downloads, with a runnable script), expanded [API Reference](docs/API_REFERENCE.md) covering all three products.
- New examples: `examples/drafting_example.py`, `examples/drafting_example.sh`, `examples/outline_example.py`.
- Test kit extended: the evidence PDFs double as Drafting/Outlines inputs, with a suggested drafting test call.

## 2026-03-26 — Initial release

- RFE Response Builder API (`/api/v1/rfe`) documentation, quickstart, Python/bash examples, and synthetic test kit.
