{{- define "declarative-agent-library.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "declarative-agent-library.fullname" -}}
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

{{- define "declarative-agent-library.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "declarative-agent-library.labels" -}}
helm.sh/chart: {{ include "declarative-agent-library.chart" . }}
{{ include "declarative-agent-library.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "declarative-agent-library.selectorLabels" -}}
app.kubernetes.io/name: {{ include "declarative-agent-library.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "declarative-agent-library.agentComponentLabel" -}}
app.kubernetes.io/component: agent
{{- end }}

{{- define "declarative-agent-library.agentSelectorLabels" -}}
{{ include "declarative-agent-library.selectorLabels" . }}
{{ include "declarative-agent-library.agentComponentLabel" . }}
{{- end }}

{{- define "declarative-agent-library.ragSelectorLabels" -}}
{{ include "declarative-agent-library.selectorLabels" . }}
app.kubernetes.io/component: rag
{{- end }}

{{/*
True when scrapers.jobs has at least one entry with enabled: true (RAG workload is deployed).
*/}}
{{- define "declarative-agent-library.ragDeployed" -}}
{{- range .Values.scrapers.jobs -}}
{{- if .enabled -}}1{{- end -}}
{{- end -}}
{{- end }}

{{/*
Cluster-internal base URL for the RAG HTTP service (empty when no enabled scraper jobs).
*/}}
{{- define "declarative-agent-library.ragInternalBaseUrl" -}}
{{- if include "declarative-agent-library.ragDeployed" . -}}
http://{{ include "declarative-agent-library.fullname" . }}-rag:{{ .Values.scrapers.ragService.service.port }}
{{- end -}}
{{- end }}
