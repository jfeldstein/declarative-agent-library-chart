{{/*
Inject consumer observability plugin env when observability.plugins.consumerPlugins.enabled is true.
Traceability: [DALC-REQ-CHART-RTV-005]
*/}}
{{- define "declarative-agent-library-chart.consumerPluginsEnv" -}}
{{- $cp := .Values.observability.plugins.consumerPlugins | default dict }}
{{- if $cp.enabled | default false }}
- name: HOSTED_AGENT_OBSERVABILITY_PLUGINS_CONSUMER_ENABLED
  value: "true"
{{- if $cp.strict | default false }}
- name: HOSTED_AGENT_OBSERVABILITY_PLUGINS_STRICT
  value: "true"
{{- end }}
{{- $eps := $cp.entryPoints | default list }}
{{- if $eps }}
- name: HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS
  value: {{ join "," $eps | quote }}
{{- end }}
{{- $sec := $cp.configJsonSecret | default dict }}
{{- $secName := $sec.secretName | default "" | trim }}
{{- $secKey := $sec.secretKey | default "config.json" | trim }}
{{- if and $secName $secKey }}
- name: HOSTED_AGENT_OBSERVABILITY_PLUGINS_CONSUMER_CONFIG_JSON
  valueFrom:
    secretKeyRef:
      name: {{ $secName | quote }}
      key: {{ $secKey | quote }}
{{- else }}
{{- $inline := $cp.configJson | default "" | trim }}
{{- if $inline }}
- name: HOSTED_AGENT_OBSERVABILITY_PLUGINS_CONSUMER_CONFIG_JSON
  value: {{ $inline | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
