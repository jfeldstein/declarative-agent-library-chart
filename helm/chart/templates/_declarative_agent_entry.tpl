{{/*
  Parent application charts should use:
    {{- include "declarative-agent.system" . }}
  in templates/agent.yaml. Context `.` is the parent chart root; agent tunables live under .Values.agent.
*/}}
{{- define "declarative-agent.system" -}}
{{- $chart := dict "Name" "declarative-agent-library-chart" "Version" "0.1.0" "AppVersion" "0.1.0" }}
{{- $agentVals := index .Values "agent" | required "Parent chart must set .Values.agent for the Declarative Agent Library" }}
{{- $parentFiles := .Files }}
{{- $dalcFiles := .Files }}
{{- $sub := coalesce (index .Subcharts "agent") (index .Subcharts "declarative-agent-library-chart") }}
{{- if and $sub $sub.Files }}
{{- $dalcFiles = $sub.Files }}
{{- end }}
{{- $ctx := dict "Chart" $chart "Values" $agentVals "Release" .Release "Capabilities" .Capabilities "Template" .Template "Files" $parentFiles "DalcFiles" $dalcFiles }}
{{- include "declarative-agent-library-chart.systemBundled" $ctx }}
{{- end }}
