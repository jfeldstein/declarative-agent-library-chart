{{/*
Traceability: [DALC-REQ-CHART-RTV-005]
Consumer plugins: observability.plugins.consumerPlugins is a list of entry-point names.
Non-empty list enables HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS (comma-separated).
*/}}
{{- define "declarative-agent-library-chart.consumerPluginsEnv" -}}
{{- $names := .Values.observability.plugins.consumerPlugins | default list }}
{{- if gt (len $names) 0 }}
- name: HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS
  value: {{ join "," $names | quote }}
{{- end }}
{{- end }}
