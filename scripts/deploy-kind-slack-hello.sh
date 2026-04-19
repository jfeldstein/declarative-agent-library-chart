#!/usr/bin/env bash
# Deploy hello-world to a local kind cluster with Slack Socket Mode trigger + hello reply.
#
# Prerequisites:
#   - Docker daemon running (Docker Desktop, Rancher Desktop, etc.)
#   - kind + kubectl + helm
# Slack app (api.slack.com/apps): enable Socket Mode; create app-level token (connections:write).
# Subscribe to bot event app_mention; OAuth scopes include app_mentions:read and chat:write.
#
# Usage:
#   export SLACK_BOT_TOKEN=xoxb-...
#   export SLACK_APP_TOKEN=xapp-...
#   ./scripts/deploy-kind-slack-hello.sh
#
# Optional env:
#   KIND_CLUSTER_NAME (default: dalc)
#   K8S_NAMESPACE (default: declarative-agent)
#   HELM_RELEASE (default: hello-world)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLUSTER="${KIND_CLUSTER_NAME:-dalc}"
NS="${K8S_NAMESPACE:-declarative-agent}"
RELEASE="${HELM_RELEASE:-hello-world}"

if [[ -z "${SLACK_BOT_TOKEN:-}" || -z "${SLACK_APP_TOKEN:-}" ]]; then
  echo "error: set SLACK_BOT_TOKEN (xoxb-…) and SLACK_APP_TOKEN (xapp-…) for Socket Mode." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "error: Docker daemon not reachable; start Docker Desktop (or your container runtime) and retry." >&2
  exit 1
fi

if ! kind get clusters 2>/dev/null | grep -qx "${CLUSTER}"; then
  echo "==> Creating kind cluster ${CLUSTER}"
  kind create cluster --name "${CLUSTER}"
fi

kubectl config use-context "kind-${CLUSTER}"

echo "==> Building agent image"
docker build -t declarative-agent-library-chart:local -f "${ROOT}/helm/Dockerfile" "${ROOT}"

echo "==> Loading image into kind"
kind load docker-image declarative-agent-library-chart:local --name "${CLUSTER}"

echo "==> Helm dependency build"
(cd "${ROOT}/examples/hello-world" && helm dependency build --skip-refresh)

kubectl create namespace "${NS}" 2>/dev/null || true

kubectl -n "${NS}" create secret generic slack-trigger-secrets \
  --from-literal=token="${SLACK_BOT_TOKEN}" \
  --from-literal=app-token="${SLACK_APP_TOKEN}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Installing Helm release ${RELEASE}"
helm upgrade --install "${RELEASE}" "${ROOT}/examples/hello-world" \
  --namespace "${NS}" \
  --wait \
  --timeout 5m \
  -f "${ROOT}/examples/hello-world/values.yaml" \
  --set agent.slackTrigger.enabled=true \
  --set agent.slackTrigger.socketMode=true \
  --set agent.slackTrigger.appTokenSecretName=slack-trigger-secrets \
  --set agent.slackTrigger.botTokenSecretName=slack-trigger-secrets

echo ""
echo "Done. Invite the Slack app to a channel, then @-mention the bot."
echo "It should reply with the configured hello (see agent.systemPrompt in examples/hello-world/values.yaml)."
echo ""
kubectl -n "${NS}" rollout status "deployment/${RELEASE}-declarative-agent-library-chart" --timeout 120s
