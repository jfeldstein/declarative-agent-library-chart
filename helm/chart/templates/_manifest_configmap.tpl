{{- define "declarative-agent-library-chart.manifest.configmap" -}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "declarative-agent-library-chart.fullname" . }}-config
  labels:
    {{- include "declarative-agent-library-chart.labels" . | nindent 4 }}
data:
  system-prompt: |
{{ .Values.systemPrompt | nindent 4 }}
  subagents.json: {{ .Values.subagents | toJson | quote }}
  skills.json: {{ .Values.skills | toJson | quote }}
  enabled-mcp-tools.json: {{ .Values.mcp.enabledTools | toJson | quote }}
  label-registry.json: {{ .Values.scrapers.slack.feedback.labelRegistry | toJson | quote }}
  slack-emoji-label-map.json: {{ .Values.scrapers.slack.feedback.emojiLabelMap | toJson | quote }}
{{- end -}}
