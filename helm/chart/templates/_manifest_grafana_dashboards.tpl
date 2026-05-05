{{- define "declarative-agent-library-chart.manifest.grafanaDashboards" -}}
{{- if .Values.observability.plugins.grafana.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "declarative-agent-library-chart.fullname" . }}-grafana-dashboards
  labels:
    {{- include "declarative-agent-library-chart.labels" . | nindent 4 }}
    dalc.agent.grafana.dashboards: "true"
data:
  dalc-overview.json: |-
{{ .DalcFiles.Get "files/grafana/dalc-overview.json" | nindent 4 }}
  cfha-token-metrics.json: |-
{{ .DalcFiles.Get "files/grafana/cfha-token-metrics.json" | nindent 4 }}
{{- end }}
{{- end }}
