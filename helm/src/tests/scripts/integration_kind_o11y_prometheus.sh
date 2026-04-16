#!/usr/bin/env bash
# Integration: kind + with-observability chart + prometheus-community/prometheus + PromQL assert.
# Purpose-built for pytest: tests/integration/test_kind_o11y_prometheus.py
# Prerequisites: docker, kind, kubectl, helm, curl, python3 (stdlib json).
#
# Usage (from repository root):
#   ./helm/src/tests/scripts/integration_kind_o11y_prometheus.sh
#
# Env:
#   KIND_CLUSTER_NAME   (default: dalc-o11y-it)
#   SKIP_KIND_CREATE=1  reuse existing cluster if present
#   CLEANUP_KIND=1      delete cluster on exit (success or failure)
#   NAMESPACE           (default: default)
#   PROM_CHART_VERSION  (default: 29.2.0)
#   HELM_WAIT_TIMEOUT   (default: 20m; example chart helm --wait)
#   PROM_ROLLOUT_TIMEOUT (default: 45m; kubectl rollout for prometheus server)
#   PROM_PROGRESS_DEADLINE_SEC (default: 3600; deployment progressDeadlineSeconds; chart default 600s is too low for kind on CI)
#   ROLLOUT_TIMEOUT     (default: 600s)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
cd "$ROOT"

KIND_CLUSTER_NAME="${KIND_CLUSTER_NAME:-dalc-o11y-it}"
NAMESPACE="${NAMESPACE:-default}"
AGENT_RELEASE="${AGENT_RELEASE:-o11y-kind-it}"
PROM_RELEASE="${PROM_RELEASE:-dalc-prom-it}"
PROM_CHART_VERSION="${PROM_CHART_VERSION:-29.2.0}"
TRIGGER_COUNT="${TRIGGER_COUNT:-5}"
HELM_WAIT_TIMEOUT="${HELM_WAIT_TIMEOUT:-20m}"
PROM_ROLLOUT_TIMEOUT="${PROM_ROLLOUT_TIMEOUT:-45m}"
PROM_PROGRESS_DEADLINE_SEC="${PROM_PROGRESS_DEADLINE_SEC:-3600}"
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
# Host-side tar for docker cp → ctr import (cleaned up in cleanup_all).
PROM_PRELOAD_TMP=""

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
  [[ -n "${PROM_PRELOAD_TMP}" ]] && rm -f "${PROM_PRELOAD_TMP}"
  cleanup_kind
}

trap cleanup_all EXIT

if [[ "${SKIP_KIND_CREATE:-}" != "1" ]]; then
  if ! kind get clusters 2>/dev/null | grep -qx "${KIND_CLUSTER_NAME}"; then
    kind create cluster --name "${KIND_CLUSTER_NAME}"
  fi
fi

kubectl config use-context "kind-${KIND_CLUSTER_NAME}"

# Docker container name for the control-plane node (kind versions differ:
# `kind-<cluster>-control-plane` vs `<cluster>-control-plane`).
KIND_CP=""
for cand in "kind-${KIND_CLUSTER_NAME}-control-plane" "${KIND_CLUSTER_NAME}-control-plane"; do
  if docker inspect "${cand}" &>/dev/null; then
    KIND_CP="${cand}"
    break
  fi
done
if [[ -z "${KIND_CP}" ]]; then
  echo "error: could not find kind control-plane container for cluster ${KIND_CLUSTER_NAME}" >&2
  docker ps -a --format '{{.Names}}' >&2 || true
  exit 1
fi

echo "==> helm repo (prometheus-community)"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update prometheus-community

# Load chart images into kind so the node does not pull from quay during helm --wait
# (GitHub runners often exceed Helm deadlines on slow in-cluster pulls). Pins MUST
# match prometheus-community/prometheus for PROM_CHART_VERSION — update when bumping the chart.
echo "==> kind preload images for prometheus-community/prometheus (${PROM_CHART_VERSION})"
PROM_PRELOAD_IMAGES=()
case "${PROM_CHART_VERSION}" in
  29.2.0)
    PROM_PRELOAD_IMAGES=(
      "quay.io/prometheus/prometheus:v2.55.1"
      "quay.io/prometheus-operator/prometheus-config-reloader:v0.90.1"
    )
    ;;
  *)
    echo "warning: no prometheus image preload pins for PROM_CHART_VERSION=${PROM_CHART_VERSION}; helm install may be slow or time out" >&2
    ;;
esac
if [[ ${#PROM_PRELOAD_IMAGES[@]} -gt 0 ]]; then
  for img in "${PROM_PRELOAD_IMAGES[@]}"; do
    docker pull "${img}"
  done
  # File on disk + docker cp avoids stdin import deadlines on large images (GitHub Actions).
  PROM_PRELOAD_TMP="$(mktemp "${TMPDIR:-/tmp}/dalc-prom-preload.XXXXXX")"
  docker save "${PROM_PRELOAD_IMAGES[@]}" -o "${PROM_PRELOAD_TMP}"
  # Use /var, not /tmp: ctr inside kindest/node did not see files copied to /tmp.
  docker cp "${PROM_PRELOAD_TMP}" "${KIND_CP}:/var/dalc-prom-preload.tar"
  docker exec "${KIND_CP}" ctr -n k8s.io images import /var/dalc-prom-preload.tar
  docker exec "${KIND_CP}" rm -f /var/dalc-prom-preload.tar
  rm -f "${PROM_PRELOAD_TMP}"
  PROM_PRELOAD_TMP=""
fi

echo "==> docker build"
docker build -f helm/Dockerfile -t declarative-agent:local .

echo "==> kind load image"
kind load docker-image declarative-agent:local --name "${KIND_CLUSTER_NAME}"

echo "==> helm dependency (with-observability)"
(cd examples/with-observability && helm dependency build --skip-refresh)

echo "==> helm install agent (${AGENT_RELEASE})"
helm upgrade --install "${AGENT_RELEASE}" examples/with-observability \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --set declarative-agent.observability.serviceMonitor.enabled=false \
  --wait \
  --timeout "${HELM_WAIT_TIMEOUT}"

kubectl rollout status deployment/"${AGENT_RELEASE}-declarative-agent" -n "${NAMESPACE}" --timeout="${ROLLOUT_TIMEOUT}"
kubectl rollout status deployment/"${AGENT_RELEASE}-declarative-agent-rag" -n "${NAMESPACE}" --timeout="${ROLLOUT_TIMEOUT}"

SCRAPE_TARGET_AGENT="${AGENT_RELEASE}-declarative-agent.${NAMESPACE}.svc.cluster.local:8088"
SCRAPE_TARGET_RAG="${AGENT_RELEASE}-declarative-agent-rag.${NAMESPACE}.svc.cluster.local:8090"
TMP_VALUES="$(mktemp)"
sed \
  -e "s|@SCRAPE_TARGET_AGENT@|${SCRAPE_TARGET_AGENT}|g" \
  -e "s|@SCRAPE_TARGET_RAG@|${SCRAPE_TARGET_RAG}|g" \
  "${SCRIPT_DIR}/prometheus-kind-o11y-values.yaml" >"${TMP_VALUES}"

echo "==> helm install prometheus (${PROM_RELEASE})"
# Do not use helm --wait here: it tracks many sub-resources and hits multi-hour gRPC
# context deadlines on GitHub Actions. The server Deployment + rollout status suffices.
helm upgrade --install "${PROM_RELEASE}" prometheus-community/prometheus \
  --version "${PROM_CHART_VERSION}" \
  --namespace "${NAMESPACE}" \
  -f "${TMP_VALUES}"

# Chart default progressDeadlineSeconds is 600; slow image pulls / probes on kind CI hit that first.
kubectl patch deployment "${PROM_RELEASE}-prometheus-server" -n "${NAMESPACE}" \
  --type merge -p "{\"spec\":{\"progressDeadlineSeconds\":${PROM_PROGRESS_DEADLINE_SEC}}}"

if ! kubectl rollout status deployment/"${PROM_RELEASE}-prometheus-server" -n "${NAMESPACE}" --timeout="${PROM_ROLLOUT_TIMEOUT}"; then
  echo "error: prometheus server rollout failed; kubectl diagnostics:" >&2
  kubectl get pods -n "${NAMESPACE}" -o wide >&2 || true
  kubectl describe pod -n "${NAMESPACE}" -l "app.kubernetes.io/name=prometheus" >&2 || true
  pod="$(kubectl get pods -n "${NAMESPACE}" -l "app.kubernetes.io/name=prometheus" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  if [[ -n "${pod}" ]]; then
    kubectl logs -n "${NAMESPACE}" "${pod}" -c prometheus-server --tail=80 >&2 || true
  fi
  exit 1
fi

echo "==> port-forward agent + rag + prometheus"
kubectl port-forward -n "${NAMESPACE}" "svc/${AGENT_RELEASE}-declarative-agent" 18088:8088 &
PF_AGENT_PID=$!
kubectl port-forward -n "${NAMESPACE}" "svc/${AGENT_RELEASE}-declarative-agent-rag" 18189:8090 &
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

echo "==> wait for Prometheus scrape (allow ~25s at 3s interval, two jobs)"
sleep 25

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
        sys.exit(f"{name}: no series — check dalc-rag-metrics scrape and RAG /metrics")
    val = float(results[0]["value"][1])
    if val < minimum:
        sys.exit(f"{name}: expected >= {minimum}, got {val}")
    return val

re_v = need_sum("rag_embed", os.environ["RESP_RE"], 1.0)
rq_v = need_sum("rag_query", os.environ["RESP_RQ"], 1.0)
print(f"ok: rag embed success sum = {re_v}, rag query success sum = {rq_v}")
PY

echo "✓ integration_kind_o11y_prometheus.sh passed"
