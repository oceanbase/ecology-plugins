#!/usr/bin/env bash
# Test the Slow SQL list API (Digest auth), same as the plugin uses.
#
# Usage (from repository root):
#   export OCEANBASE_ACCESS_KEY_ID=... OCEANBASE_ACCESS_KEY_SECRET=... OCEANBASE_INSTANCE_ID=... OCEANBASE_TENANT_ID=...
#   ./example/curl_test_oceanbase_api.sh
#
# startTime/endTime are required. Override with START_TIME / END_TIME (UTC).

set -euo pipefail
ENDPOINT="${OCEANBASE_ENDPOINT:-api-cloud-cn.oceanbase.com}"
START="${START_TIME:-$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)}"
END="${END_TIME:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"

: "${OCEANBASE_ACCESS_KEY_ID:?set OCEANBASE_ACCESS_KEY_ID}"
: "${OCEANBASE_ACCESS_KEY_SECRET:?set OCEANBASE_ACCESS_KEY_SECRET}"
: "${OCEANBASE_INSTANCE_ID:?set OCEANBASE_INSTANCE_ID}"
: "${OCEANBASE_TENANT_ID:?set OCEANBASE_TENANT_ID}"

URL="https://${ENDPOINT}/api/v2/instances/${OCEANBASE_INSTANCE_ID}/tenants/${OCEANBASE_TENANT_ID}/slowSql?startTime=${START}&endTime=${END}&sqlTextLength=65535"

args=(
  -sS
  -w $'\nhttp_code:%{http_code}\n'
  --digest
  -u "${OCEANBASE_ACCESS_KEY_ID}:${OCEANBASE_ACCESS_KEY_SECRET}"
)
if [[ -n "${OCEANBASE_PROJECT_ID:-}" ]]; then
  args+=( -H "X-Ob-Project-Id: ${OCEANBASE_PROJECT_ID}" )
fi
args+=( "${URL}" )
exec curl "${args[@]}"
