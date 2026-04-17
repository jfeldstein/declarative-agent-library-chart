{{- define "declarative-agent-library-chart.appendDoc" -}}
{{- $prev := .prev }}
{{- $next := .next | trim }}
{{- if $next }}
{{- if $prev }}
{{- printf "%s\n---\n%s" $prev $next }}
{{- else }}
{{- $next }}
{{- end }}
{{- else }}
{{- $prev }}
{{- end }}
{{- end }}

{{- define "declarative-agent-library-chart.systemBundled" -}}
{{- $acc := "" }}
{{- $d := include "declarative-agent-library-chart.manifest.observabilityMigration" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $d = include "declarative-agent-library-chart.manifest.configmap" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $d = include "declarative-agent-library-chart.manifest.deployment" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $d = include "declarative-agent-library-chart.manifest.service" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $d = include "declarative-agent-library-chart.manifest.servicemonitorAgent" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $d = include "declarative-agent-library-chart.manifest.scraperJobConfigmaps" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $d = include "declarative-agent-library-chart.manifest.scraperCronjobs" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $d = include "declarative-agent-library-chart.manifest.ragDeployment" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $d = include "declarative-agent-library-chart.manifest.ragService" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $d = include "declarative-agent-library-chart.manifest.ragServiceMonitor" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $d = include "declarative-agent-library-chart.manifest.testTrigger" . | trim }}
{{- $acc = include "declarative-agent-library-chart.appendDoc" (dict "prev" $acc "next" $d) }}
{{- $acc }}
{{- end }}
