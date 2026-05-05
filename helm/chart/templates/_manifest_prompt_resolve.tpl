{{/*
  [DALC-REQ-CHART-RTV-006]
  Resolve supervisor and subagent prompts; parent chart files via .Files.Get.
  Mutually exclusive: non-empty inline text vs file path per scope (orchestrator, each subagent).
  See values.schema.json for contract.
*/}}
{{- define "declarative-agent-library-chart.resolvedSystemPrompt" -}}
{{- $sp := trim (toString (default "" .Values.systemPrompt)) -}}
{{- $sf := trim (toString (default "" .Values.systemPromptFile)) -}}
{{- if and $sp $sf -}}
{{- fail "dalc chart: systemPrompt and systemPromptFile are mutually exclusive (both non-empty after trim)" -}}
{{- end -}}
{{- if $sf -}}
{{- .Files.Get $sf -}}
{{- else -}}
{{- .Values.systemPrompt -}}
{{- end -}}
{{- end -}}

{{- define "declarative-agent-library-chart.resolvedSubagentsJson" -}}
{{- $out := list -}}
{{- $rows := .Values.subagents | default list -}}
{{- range $i, $row := $rows -}}
  {{- if not (kindIs "map" $row) -}}
  {{- fail (printf "dalc chart: subagents[%d] must be an object" $i) -}}
  {{- end -}}
  {{- $name := trim (toString (default "" (index $row "name"))) -}}
  {{- $label := $name -}}
  {{- if not $label -}}{{- $label = printf "index %d" $i -}}{{- end -}}
  {{- $f1 := trim (toString (default "" (index $row "systemPromptFile"))) -}}
  {{- $f2 := trim (toString (default "" (index $row "system_prompt_file"))) -}}
  {{- if and $f1 $f2 -}}
  {{- fail (printf "dalc chart: subagent %q uses both systemPromptFile and system_prompt_file (mutually exclusive)" $label) -}}
  {{- end -}}
  {{- $filePath := "" -}}
  {{- if $f1 -}}{{- $filePath = $f1 -}}{{- else if $f2 -}}{{- $filePath = $f2 -}}{{- end -}}
  {{- $inlineSp := toString (default "" (index $row "systemPrompt")) -}}
  {{- $inlineSn := toString (default "" (index $row "system_prompt")) -}}
  {{- $spTrim := trim $inlineSp -}}
  {{- $snTrim := trim $inlineSn -}}
  {{- $inlinePresent := or (ne $spTrim "") (ne $snTrim "") -}}
  {{- if and $inlinePresent $filePath -}}
  {{- fail (printf "dalc chart: subagent %q has both inline prompt and systemPromptFile/system_prompt_file (mutually exclusive)" $label) -}}
  {{- end -}}
  {{- $resolved := "" -}}
  {{- if $filePath -}}
  {{- $resolved = $.Files.Get $filePath -}}
  {{- else if $spTrim -}}
  {{- $resolved = $inlineSp -}}
  {{- else -}}
  {{- $resolved = $inlineSn -}}
  {{- end -}}
  {{- $clean := omit $row "system_prompt" "systemPromptFile" "system_prompt_file" -}}
  {{- if $filePath -}}
  {{- $clean = set $clean "systemPrompt" $resolved -}}
  {{- else if $inlinePresent -}}
  {{- $clean = set $clean "systemPrompt" $resolved -}}
  {{- else -}}
  {{- $clean = omit $clean "systemPrompt" -}}
  {{- end -}}
  {{- $out = append $out $clean -}}
{{- end -}}
{{- $out | toJson -}}
{{- end -}}
