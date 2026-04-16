{{- define "declarative-agent-library-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "declarative-agent-library-chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "declarative-agent-library-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "declarative-agent-library-chart.labels" -}}
helm.sh/chart: {{ include "declarative-agent-library-chart.chart" . }}
{{ include "declarative-agent-library-chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "declarative-agent-library-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "declarative-agent-library-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "declarative-agent-library-chart.agentComponentLabel" -}}
app.kubernetes.io/component: agent
{{- end }}

{{- define "declarative-agent-library-chart.agentSelectorLabels" -}}
{{ include "declarative-agent-library-chart.selectorLabels" . }}
{{ include "declarative-agent-library-chart.agentComponentLabel" . }}
{{- end }}

{{- define "declarative-agent-library-chart.ragSelectorLabels" -}}
{{ include "declarative-agent-library-chart.selectorLabels" . }}
app.kubernetes.io/component: rag
{{- end }}

{{/*
True when scrapers.jira or scrapers.slack has at least one enabled job (RAG workload is deployed).
*/}}
{{- define "declarative-agent-library-chart.ragDeployed" -}}
{{- if and $.Values.scrapers.jira.enabled $.Values.scrapers.jira.jobs }}
{{- range $.Values.scrapers.jira.jobs }}
{{- if or (not (hasKey . "enabled")) .enabled }}1{{- end }}
{{- end }}
{{- end }}
{{- if and $.Values.scrapers.slack.enabled $.Values.scrapers.slack.jobs }}
{{- range $.Values.scrapers.slack.jobs }}
{{- if or (not (hasKey . "enabled")) .enabled }}1{{- end }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Cluster-internal base URL for the RAG HTTP service (empty when no enabled scraper jobs).
*/}}
{{- define "declarative-agent-library-chart.ragInternalBaseUrl" -}}
{{- if include "declarative-agent-library-chart.ragDeployed" . -}}
http://{{ include "declarative-agent-library-chart.fullname" . }}-rag:{{ .Values.scrapers.ragService.service.port }}
{{- end -}}
{{- end }}
