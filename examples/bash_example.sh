#!/usr/bin/env bash
# ============================================================================
# DraftyAI RFE Response Builder — Bash Example
#
# Generates a complete RFE response draft from a notice file.
# Uses async mode with polling so the request doesn't time out.
#
# Requirements:
#   - curl (pre-installed on Mac/Linux)
#   - jq   (optional, for pretty-printing JSON)
#         Install: brew install jq  OR  apt-get install jq
#
# Usage:
#   1. Set your API key below (or export it as an environment variable)
#   2. Run from the repo root:  bash examples/bash_example.sh
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY="${DRAFTYAI_API_KEY:-YOUR_KEY_HERE}"
BASE_URL="https://papi.draftyai.com"

NOTICE_FILE="test-kit/notice/drafty_simulated_rfe_i140_e11.pdf"
EVIDENCE_DIR="test-kit/evidence"

CLIENT_FIRST_NAME="Karina"
CLIENT_LAST_NAME="Velasquez"
CLIENT_GENDER="Female"

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------

if [ "$API_KEY" = "YOUR_KEY_HERE" ]; then
    echo "ERROR: Set your API key first."
    echo "  Option 1: Edit API_KEY in this script"
    echo "  Option 2: export DRAFTYAI_API_KEY=dfy_live_..."
    exit 1
fi

if [ ! -f "$NOTICE_FILE" ]; then
    echo "ERROR: Notice file not found: $NOTICE_FILE"
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
# Build the curl command with all evidence files
# ---------------------------------------------------------------------------

echo "============================================"
echo "DraftyAI RFE Response Builder"
echo "============================================"
echo ""
echo "Submitting job (async mode)..."
echo "  Notice:   $NOTICE_FILE"

EVIDENCE_ARGS=""
EVIDENCE_COUNT=0
for file in "$EVIDENCE_DIR"/*.pdf; do
    if [ -f "$file" ]; then
        EVIDENCE_ARGS="$EVIDENCE_ARGS -F evidence_files=@$file"
        EVIDENCE_COUNT=$((EVIDENCE_COUNT + 1))
    fi
done
echo "  Evidence: $EVIDENCE_COUNT file(s)"
echo ""

# ---------------------------------------------------------------------------
# Submit the job (async mode)
# ---------------------------------------------------------------------------

SUBMIT_RESPONSE=$(eval curl -s -X POST \
    "\"$BASE_URL/api/v1/rfe/generate?wait=false\"" \
    -H "\"X-API-Key: $API_KEY\"" \
    -F "\"notice_file=@$NOTICE_FILE\"" \
    $EVIDENCE_ARGS \
    -F "\"client_first_name=$CLIENT_FIRST_NAME\"" \
    -F "\"client_last_name=$CLIENT_LAST_NAME\"" \
    -F "\"client_gender=$CLIENT_GENDER\"")

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
# Poll for the result
# ---------------------------------------------------------------------------

echo ""
echo "Polling for result (checking every 10 seconds)..."
echo ""

while true; do
    sleep 10

    POLL_RESPONSE=$(curl -s \
        -H "X-API-Key: $API_KEY" \
        "$BASE_URL$POLL_PATH")

    STATUS=$(echo "$POLL_RESPONSE" | $JQ -r '.status')
    echo "  Status: $STATUS"

    if [ "$STATUS" = "completed" ]; then
        echo ""
        echo "============================================"
        echo "DRAFT GENERATED SUCCESSFULLY"
        echo "============================================"
        echo ""

        # Extract key info
        if [ "$JQ" = "jq" ]; then
            PROJECT_ID=$(echo "$POLL_RESPONSE" | jq -r '.result.project_id')
            ISSUE_COUNT=$(echo "$POLL_RESPONSE" | jq -r '.result.issue_count')
            DOCX_URL=$(echo "$POLL_RESPONSE" | jq -r '.result.docx_download_url')

            echo "  Project ID: $PROJECT_ID"
            echo "  Issues:     $ISSUE_COUNT"
            echo ""

            # Show issue titles
            echo "$POLL_RESPONSE" | jq -r '.result.content.issues[] | "  Issue: \(.title)"'
            echo ""

            # Download the DOCX
            if [ "$DOCX_URL" != "null" ] && [ -n "$DOCX_URL" ]; then
                echo "Downloading Word document..."
                curl -s \
                    -H "X-API-Key: $API_KEY" \
                    "$BASE_URL$DOCX_URL" \
                    -o rfe_response.docx
                echo "  Saved to: rfe_response.docx"
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
