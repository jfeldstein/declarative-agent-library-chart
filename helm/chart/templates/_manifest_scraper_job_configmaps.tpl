{{- define "declarative-agent-library-chart.manifest.scraperJobConfigmaps" -}}
{{/* One ConfigMap per enabled scraper job (non-secret JSON at job.json). Traceability: [DALC-REQ-RAG-SCRAPERS-002] [DALC-REQ-RAG-SCRAPERS-005] */}}
{{- $root := . }}
{{- if and $root.Values.scrapers.jira.enabled $root.Values.scrapers.jira.jobs }}
{{- range $ji, $job := $root.Values.scrapers.jira.jobs }}
{{- if or (not (hasKey $job "enabled")) $job.enabled }}
{{- $clean := dict }}
{{- range $k, $v := $job }}
{{- if and (ne $k "enabled") (ne $k "schedule") (ne $k "siteUrl") (ne $k "watermarkDir") (ne $k "concurrencyPolicy") }}
{{- $_ := set $clean $k $v }}
{{- end }}
{{- end }}
{{- $defaults := default dict $root.Values.scrapers.jira.defaults }}
{{- $cfg := mergeOverwrite (deepCopy $defaults) $clean }}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "declarative-agent-library-chart.fullname" $root }}-scraper-job-jira-{{ $ji }}
  labels:
    {{- include "declarative-agent-library-chart.labels" $root | nindent 4 }}
    app.kubernetes.io/component: scraper
    scraper.agentic.dalc/source: jira
    scraper.agentic.dalc/index: {{ $ji | quote }}
data:
  job.json: |
{{ toJson $cfg | nindent 4 }}
{{- end }}
{{- end }}
{{- end }}
{{- if and $root.Values.scrapers.slack.enabled $root.Values.scrapers.slack.jobs }}
{{- range $si, $job := $root.Values.scrapers.slack.jobs }}
{{- if or (not (hasKey $job "enabled")) $job.enabled }}
{{- $clean := dict }}
{{- range $k, $v := $job }}
{{- if and (ne $k "enabled") (ne $k "schedule") (ne $k "concurrencyPolicy") }}
{{- $_ := set $clean $k $v }}
{{- end }}
{{- end }}
{{- $defaults := default dict $root.Values.scrapers.slack.defaults }}
{{- $cfg := mergeOverwrite (deepCopy $defaults) $clean }}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "declarative-agent-library-chart.fullname" $root }}-scraper-job-slack-{{ $si }}
  labels:
    {{- include "declarative-agent-library-chart.labels" $root | nindent 4 }}
    app.kubernetes.io/component: scraper
    scraper.agentic.dalc/source: slack
    scraper.agentic.dalc/index: {{ $si | quote }}
data:
  job.json: |
{{ toJson $cfg | nindent 4 }}
{{- end }}
{{- end }}
{{- end }}
{{- end -}}
