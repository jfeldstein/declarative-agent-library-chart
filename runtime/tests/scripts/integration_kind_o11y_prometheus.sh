#!/usr/bin/env bash
# Integration: kind + with-observability chart + prometheus-community/prometheus + PromQL assert.
# Purpose-built for pytest: tests/integration/test_kind_o11y_prometheus.py
# Prerequisites: docker, kind, kubectl, helm, curl, python3 (stdlib json).
#
# Usage (from repo root projects/config-first-hosted-agents):
#   ./runtime/tests/scripts/integration_kind_o11y_prometheus.sh
#
# Env:
#   KIND_CLUSTER_NAME   (default: cfha-o11y-it)
#   SKIP_KIND_CREATE=1  reuse existing cluster if present
#   CLEANUP_KIND=1      delete cluster on exit (success or failure)
#   NAMESPACE           (default: default)
#   PROM_CHART_VERSION  (default: 29.2.0)
#   HELM_WAIT_TIMEOUT   (default: 15m)
#   ROLLOUT_TIMEOUT     (default: 600s)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "$ROOT"

KIND_CLUSTER_NAME="${KIND_CLUSTER_NAME:-cfha-o11y-it}"
NAMESPACE="${NAMESPACE:-default}"
AGENT_RELEASE="${AGENT_RELEASE:-o11y-kind-it}"
PROM_RELEASE="${PROM_RELEASE:-cfha-prom-it}"
PROM_CHART_VERSION="${PROM_CHART_VERSION:-29.2.0}"
TRIGGER_COUNT="${TRIGGER_COUNT:-5}"
HELM_WAIT_TIMEOUT="${HELM_WAIT_TIMEOUT:-15m}"
ROLLOUT_TIMEOUT="${ROLLOUT_TIMEOUT:-600s}"

need() {
  command -v "$1" &>/dev/null || {
    echo "error: missing required command: $1" >&2
    exit 1
  }
}

need docker
need kind
need kubectl
need helm
need curl
need python3

TMP_VALUES=""

cleanup_pf() {
  if [[ -n "${PF_PROM_PID:-}" ]] && kill -0 "${PF_PROM_PID}" 2>/dev/null; then
    kill "${PF_PROM_PID}" 2>/dev/null || true
  fi
  if [[ -n "${PF_AGENT_PID:-}" ]] && kill -0 "${PF_AGENT_PID}" 2>/dev/null; then
    kill "${PF_AGENT_PID}" 2>/dev/null || true
  fi
  if [[ -n "${PF_RAG_PID:-}" ]] && kill -0 "${PF_RAG_PID}" 2>/dev/null; then
    kill "${PF_RAG_PID}" 2>/dev/null || true
  fi
}

cleanup_kind() {
  if [[ "${CLEANUP_KIND:-}" == "1" ]]; then
    kind delete cluster --name "${KIND_CLUSTER_NAME}" 2>/dev/null || true
  fi
}

cleanup_all() {
  cleanup_pf
  [[ -n "${TMP_VALUES}" ]] && rm -f "${TMP_VALUES}"
  cleanup_kind
}

trap cleanup_all EXIT

if [[ "${SKIP_KIND_CREATE:-}" != "1" ]]; then
  if ! kind get clusters 2>/dev/null | grep -qx "${KIND_CLUSTER_NAME}"; then
    kind create cluster --name "${KIND_CLUSTER_NAME}"
  fi
fi

kubectl config use-context "kind-${KIND_CLUSTER_NAME}"

echo "==> docker build"
docker build -t config-first-hosted-agents:local .

echo "==> kind load image"
kind load docker-image config-first-hosted-agents:local --name "${KIND_CLUSTER_NAME}"

echo "==> helm dependency (with-observability)"
(cd examples/with-observability && helm dependency build --skip-refresh)

echo "==> helm install agent (${AGENT_RELEASE})"
helm upgrade --install "${AGENT_RELEASE}" examples/with-observability \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --set declarative-agent-library.o11y.serviceMonitor.enabled=false \
  --wait \
  --timeout "${HELM_WAIT_TIMEOUT}"

kubectl rollout status deployment/"${AGENT_RELEASE}-declarative-agent-library" -n "${NAMESPACE}" --timeout="${ROLLOUT_TIMEOUT}"
kubectl rollout status deployment/"${AGENT_RELEASE}-declarative-agent-library-rag" -n "${NAMESPACE}" --timeout="${ROLLOUT_TIMEOUT}"

SCRAPE_TARGET_AGENT="${AGENT_RELEASE}-declarative-agent-library.${NAMESPACE}.svc.cluster.local:8088"
SCRAPE_TARGET_RAG="${AGENT_RELEASE}-declarative-agent-library-rag.${NAMESPACE}.svc.cluster.local:8090"
TMP_VALUES="$(mktemp)"
sed \
  -e "s|@SCRAPE_TARGET_AGENT@|${SCRAPE_TARGET_AGENT}|g" \
  -e "s|@SCRAPE_TARGET_RAG@|${SCRAPE_TARGET_RAG}|g" \
  "${SCRIPT_DIR}/prometheus-kind-o11y-values.yaml" >"${TMP_VALUES}"

echo "==> helm repo (prometheus-community)"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update prometheus-community

echo "==> helm install prometheus (${PROM_RELEASE})"
helm upgrade --install "${PROM_RELEASE}" prometheus-community/prometheus \
  --version "${PROM_CHART_VERSION}" \
  --namespace "${NAMESPACE}" \
  -f "${TMP_VALUES}" \
  --wait \
  --timeout "${HELM_WAIT_TIMEOUT}"

kubectl rollout status deployment/"${PROM_RELEASE}-prometheus-server" -n "${NAMESPACE}" --timeout="${ROLLOUT_TIMEOUT}"

echo "==> port-forward agent + rag + prometheus"
kubectl port-forward -n "${NAMESPACE}" "svc/${AGENT_RELEASE}-declarative-agent-library" 18088:8088 &
PF_AGENT_PID=$!
kubectl port-forward -n "${NAMESPACE}" "svc/${AGENT_RELEASE}-declarative-agent-library-rag" 18189:8090 &
PF_RAG_PID=$!
kubectl port-forward -n "${NAMESPACE}" "svc/${PROM_RELEASE}-prometheus-server" 19090:80 &
PF_PROM_PID=$!

for _ in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:19090/-/ready" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "==> POST /api/v1/trigger x${TRIGGER_COUNT}"
for _ in $(seq 1 "${TRIGGER_COUNT}"); do
  body=$(curl -sf -X POST "http://127.0.0.1:18088/api/v1/trigger")
  echo "    trigger ok: ${body:0:40}..."
done

echo "==> POST RAG /v1/embed + /v1/query (agent_runtime_rag_* traffic)"
curl -sf -X POST "http://127.0.0.1:18189/v1/embed" \
  -H 'content-type: application/json' \
  -d '{"scope":"o11y-it","items":[{"text":"prometheus integration rag corpus","metadata":{"src":"it"}}]}' >/dev/null
curl -sf -X POST "http://127.0.0.1:18189/v1/query" \
  -H 'content-type: application/json' \
  -d '{"scope":"o11y-it","query":"integration corpus","top_k":3}' >/dev/null

echo "==> wait for Prometheus scrape (chart default global interval is 1m)"
sleep 90

QUERY='sum(agent_runtime_http_trigger_requests_total{result="success"})'
echo "==> PromQL: ${QUERY}"
RESP=$(curl -sf -G "http://127.0.0.1:19090/api/v1/query" --data-urlencode "query=${QUERY}")

export RESP
export TRIGGER_COUNT
python3 - <<'PY'
import json
import os
import sys

resp = json.loads(os.environ["RESP"])
if resp.get("status") != "success":
    sys.exit(f"unexpected response: {resp!r}")
results = resp.get("data", {}).get("result", [])
if not results:
    sys.exit("no series for agent_runtime_http_trigger_requests_total — check scrape target and /metrics")
val = float(results[0]["value"][1])
need = float(os.environ.get("TRIGGER_COUNT", "5"))
if val < need:
    sys.exit(f"expected sum(success) >= {need}, got {val}")
print(f"ok: sum(agent_runtime_http_trigger_requests_total{{result=\"success\"}}) = {val}")
PY

QUERY_RAG_EMBED='sum(agent_runtime_rag_embed_requests_total{result="success"})'
echo "==> PromQL: ${QUERY_RAG_EMBED}"
RESP_RE=$(curl -sf -G "http://127.0.0.1:19090/api/v1/query" --data-urlencode "query=${QUERY_RAG_EMBED}")
QUERY_RAG_Q='sum(agent_runtime_rag_query_requests_total{result="success"})'
echo "==> PromQL: ${QUERY_RAG_Q}"
RESP_RQ=$(curl -sf -G "http://127.0.0.1:19090/api/v1/query" --data-urlencode "query=${QUERY_RAG_Q}")

export RESP_RE
export RESP_RQ
python3 - <<'PY'
import json
import os
import sys

def need_sum(name: str, resp_json: str, minimum: float) -> float:
    resp = json.loads(resp_json)
    if resp.get("status") != "success":
        sys.exit(f"{name}: unexpected response: {resp!r}")
    results = resp.get("data", {}).get("result", [])
    if not results:
        sys.exit(f"{name}: no series — check cfha-rag-metrics scrape and RAG /metrics")
    val = float(results[0]["value"][1])
    if val < minimum:
        sys.exit(f"{name}: expected >= {minimum}, got {val}")
    return val

re_v = need_sum("rag_embed", os.environ["RESP_RE"], 1.0)
rq_v = need_sum("rag_query", os.environ["RESP_RQ"], 1.0)
print(f"ok: rag embed success sum = {re_v}, rag query success sum = {rq_v}")
PY

echo "✓ integration_kind_o11y_prometheus.sh passed"
