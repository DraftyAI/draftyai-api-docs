#!/usr/bin/env bash
# ============================================================================
# DraftyAI Drafting API — Bash Example
#
# Generates a complete legal draft (with an auto-built exhibit list) from
# case documents, then downloads the Word document.
#
# Drafting is LONG-RUNNING BY DESIGN (multi-pass drafting + quality review):
# budget 10-30 minutes. This script uses async mode (the API default) and
# polls every 45 seconds, printing live progress.
#
# Requirements:
#   - curl (pre-installed on Mac/Linux)
#   - jq   (optional, for pretty-printing JSON)
#         Install: brew install jq  OR  apt-get install jq
#
# Usage:
#   1. Set your API key below (or export it as an environment variable)
#   2. Run from the repo root:  bash examples/drafting_example.sh
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY="${DRAFTYAI_API_KEY:-YOUR_KEY_HERE}"
BASE_URL="https://papi.draftyai.com"

DOCUMENT_TYPE="eb2_niw"   # a catalog key, or a free label like "Motion to Continue"
DOCUMENTS_DIR="test-kit/evidence"

CLIENT_FIRST_NAME="Karina"
CLIENT_LAST_NAME="Velasquez"
CLIENT_GENDER="Female"
MATTER_TYPE="eb2_niw"
VENUE="uscis"             # REQUIRED: where THIS document is filed (GET /api/v1/drafting/venues)

POLL_SECONDS=45           # drafts run 10-30+ minutes — poll gently

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------

if [ "$API_KEY" = "YOUR_KEY_HERE" ]; then
    echo "ERROR: Set your API key first."
    echo "  Option 1: Edit API_KEY in this script"
    echo "  Option 2: export DRAFTYAI_API_KEY=dfy_live_..."
    exit 1
fi

if [ ! -d "$DOCUMENTS_DIR" ]; then
    echo "ERROR: Documents folder not found: $DOCUMENTS_DIR"
    echo "  Make sure you run this from the repo root directory."
    exit 1
fi

# Check if jq is available (used for JSON parsing)
if command -v jq &> /dev/null; then
    JQ="jq"
else
    echo "NOTE: 'jq' is not installed. JSON output will be raw."
    echo "  Install it with: brew install jq  OR  apt-get install jq"
    echo ""
    JQ="cat"
fi

# ---------------------------------------------------------------------------
# Build the curl command with all case documents
# ---------------------------------------------------------------------------

echo "============================================"
echo "DraftyAI Drafting API"
echo "============================================"
echo ""
echo "Submitting job (async mode — this is the default)..."
echo "  Document type: $DOCUMENT_TYPE"

DOCUMENT_ARGS=""
DOCUMENT_COUNT=0
for file in "$DOCUMENTS_DIR"/*.pdf; do
    if [ -f "$file" ]; then
        DOCUMENT_ARGS="$DOCUMENT_ARGS -F documents=@$file"
        DOCUMENT_COUNT=$((DOCUMENT_COUNT + 1))
    fi
done
echo "  Documents: $DOCUMENT_COUNT file(s)"
echo ""

# ---------------------------------------------------------------------------
# Submit the job (async mode is the default — no ?wait needed)
# ---------------------------------------------------------------------------

SUBMIT_RESPONSE=$(eval curl -s -X POST \
    "\"$BASE_URL/api/v1/drafting/generate\"" \
    -H "\"X-API-Key: $API_KEY\"" \
    -F "\"document_type=$DOCUMENT_TYPE\"" \
    $DOCUMENT_ARGS \
    -F "\"client_first_name=$CLIENT_FIRST_NAME\"" \
    -F "\"client_last_name=$CLIENT_LAST_NAME\"" \
    -F "\"client_gender=$CLIENT_GENDER\"" \
    -F "\"matter_type=$MATTER_TYPE\"" \
    -F "\"venue=$VENUE\"")

# Check for errors
if echo "$SUBMIT_RESPONSE" | $JQ -e '.job_id' > /dev/null 2>&1; then
    JOB_ID=$(echo "$SUBMIT_RESPONSE" | $JQ -r '.job_id')
    POLL_PATH=$(echo "$SUBMIT_RESPONSE" | $JQ -r '.poll_url')
    echo "Job submitted: $JOB_ID"
else
    echo "ERROR: Failed to submit job."
    echo "$SUBMIT_RESPONSE" | $JQ .
    exit 1
fi

# ---------------------------------------------------------------------------
# Poll for the result (drafts take 10-30 minutes — be patient)
# ---------------------------------------------------------------------------

echo ""
echo "Polling for result (checking every ${POLL_SECONDS} seconds)..."
echo "Drafting typically takes 10-30 minutes. Go get a coffee."
echo ""

while true; do
    sleep "$POLL_SECONDS"

    POLL_RESPONSE=$(curl -s \
        -H "X-API-Key: $API_KEY" \
        "$BASE_URL$POLL_PATH")

    STATUS=$(echo "$POLL_RESPONSE" | $JQ -r '.status')

    if [ "$JQ" = "jq" ]; then
        PHASE=$(echo "$POLL_RESPONSE" | jq -r '.progress.phase // "-"')
        DONE=$(echo "$POLL_RESPONSE" | jq -r '.progress.sections_completed // empty')
        TOTAL=$(echo "$POLL_RESPONSE" | jq -r '.progress.sections_total // empty')
        if [ -n "$TOTAL" ]; then
            echo "  Status: $STATUS  |  phase: $PHASE  |  sections: ${DONE:-0}/$TOTAL"
        else
            echo "  Status: $STATUS  |  phase: $PHASE"
        fi
    else
        echo "  Status: $STATUS"
    fi

    if [ "$STATUS" = "completed" ]; then
        echo ""
        echo "============================================"
        echo "DRAFT GENERATED SUCCESSFULLY"
        echo "============================================"
        echo ""

        # Extract key info
        if [ "$JQ" = "jq" ]; then
            DRAFT_ID=$(echo "$POLL_RESPONSE" | jq -r '.result.draft_id')
            OUTLINE_MODE=$(echo "$POLL_RESPONSE" | jq -r '.result.outline_mode_used')
            DOCX_URL=$(echo "$POLL_RESPONSE" | jq -r '.result.docx_download_url')
            EXHIBIT_STATUS=$(echo "$POLL_RESPONSE" | jq -r '.result.exhibit_list.status // "none"')

            echo "  Draft ID:     $DRAFT_ID"
            echo "  Outline mode: $OUTLINE_MODE"
            echo ""

            # Show section titles
            echo "$POLL_RESPONSE" | jq -r '.result.content.sections[] | "  Section: \(.title // .id)"'
            echo ""

            # Show the exhibit list (arrives in "draft" status — approval is
            # the attorney's explicit act via .../exhibits/approve)
            if [ "$EXHIBIT_STATUS" != "none" ]; then
                echo "  Exhibit list (status: $EXHIBIT_STATUS — attorney approval pending):"
                echo "$POLL_RESPONSE" | jq -r '.result.exhibit_list.exhibits[] | "    Exhibit \(.label // "?"): \(.title)"'
                echo ""
            fi

            # Download the DOCX
            if [ "$DOCX_URL" != "null" ] && [ -n "$DOCX_URL" ]; then
                echo "Downloading Word document..."
                curl -s \
                    -H "X-API-Key: $API_KEY" \
                    "$BASE_URL$DOCX_URL" \
                    -o draft.docx
                echo "  Saved to: draft.docx"
            fi
        else
            echo "Full response:"
            echo "$POLL_RESPONSE"
        fi
        break

    elif [ "$STATUS" = "failed" ]; then
        echo ""
        echo "ERROR: Job failed."
        echo "$POLL_RESPONSE" | $JQ .
        exit 1
    fi
done

echo ""
echo "Done!"
echo "Next: review + approve the exhibit list — see docs/DRAFTING_QUICKSTART.md (Step 6)."
