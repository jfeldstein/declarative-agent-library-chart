{{- define "declarative-agent-library-chart.manifest.servicemonitorAgent" -}}
{{- if .Values.observability.serviceMonitor.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "declarative-agent-library-chart.fullname" . }}-agent
  labels:
    {{- include "declarative-agent-library-chart.labels" . | nindent 4 }}
    {{- with .Values.observability.serviceMonitor.extraLabels }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
spec:
  selector:
    matchLabels:
      {{- include "declarative-agent-library-chart.agentSelectorLabels" . | nindent 6 }}
  namespaceSelector:
    matchNames:
      - {{ .Release.Namespace }}
  endpoints:
    - port: http
      path: /metrics
      interval: {{ .Values.observability.serviceMonitor.interval | quote }}
      scrapeTimeout: {{ .Values.observability.serviceMonitor.scrapeTimeout | quote }}
{{- end }}
{{- end -}}
