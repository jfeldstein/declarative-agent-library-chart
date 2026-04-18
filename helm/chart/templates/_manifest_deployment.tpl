{{- define "declarative-agent-library-chart.manifest.deployment" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "declarative-agent-library-chart.fullname" . }}
  labels:
    {{- include "declarative-agent-library-chart.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "declarative-agent-library-chart.agentSelectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "declarative-agent-library-chart.agentSelectorLabels" . | nindent 8 }}
      {{- if .Values.observability.prometheusAnnotations.enabled }}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: {{ .Values.service.port | quote }}
        prometheus.io/path: "/metrics"
      {{- end }}
    spec:
      containers:
        - name: agent
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8088
              protocol: TCP
          env:
            {{/* HOSTED_AGENT_POSTGRES_URL: plaintext = checkpoints.postgresUrl else observability URL fields; else secretKeyRef from observability postgresUrlSecret / postgres.urlSecret. */}}
            {{- $obsPg := .Values.observability.postgres | default dict }}
            {{- $pgUrlSec := $obsPg.urlSecret | default dict }}
            {{- $topPgUrlSec := .Values.observability.postgresUrlSecret | default dict }}
            {{- $pgUrl := or .Values.observability.postgresUrl $obsPg.url "" }}
            {{- $checkpointPostgresUrl := .Values.checkpoints.postgresUrl | default "" | trim }}
            {{- $postgresUrlPlain := or $checkpointPostgresUrl $pgUrl "" }}
            {{- $pgSecName := or $topPgUrlSec.name $pgUrlSec.name "" }}
            {{- $pgSecKey := or $topPgUrlSec.key $pgUrlSec.key "DATABASE_URL" }}
            - name: HOSTED_AGENT_SYSTEM_PROMPT
              valueFrom:
                configMapKeyRef:
                  name: {{ include "declarative-agent-library-chart.fullname" . }}-config
                  key: system-prompt
            {{- if .Values.chatModel }}
            - name: HOSTED_AGENT_CHAT_MODEL
              value: {{ .Values.chatModel | quote }}
            {{- end }}
            - name: HOSTED_AGENT_RAG_BASE_URL
              value: {{ include "declarative-agent-library-chart.ragInternalBaseUrl" . | quote }}
            - name: HOSTED_AGENT_SUBAGENTS_JSON
              valueFrom:
                configMapKeyRef:
                  name: {{ include "declarative-agent-library-chart.fullname" . }}-config
                  key: subagents.json
            - name: HOSTED_AGENT_SKILLS_JSON
              valueFrom:
                configMapKeyRef:
                  name: {{ include "declarative-agent-library-chart.fullname" . }}-config
                  key: skills.json
            - name: HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON
              valueFrom:
                configMapKeyRef:
                  name: {{ include "declarative-agent-library-chart.fullname" . }}-config
                  key: enabled-mcp-tools.json
            {{- $st := .Values.slackTools | default dict }}
            {{- if $st.botTokenSecretName }}
            - name: HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ $st.botTokenSecretName | quote }}
                  key: {{ default "token" $st.botTokenSecretKey | quote }}
            {{- end }}
            - name: HOSTED_AGENT_SLACK_TOOLS_HISTORY_LIMIT
              value: {{ default 50 $st.historyLimit | toString | quote }}
            - name: HOSTED_AGENT_SLACK_TOOLS_TIMEOUT_SECONDS
              value: {{ default 30 $st.timeoutSeconds | toString | quote }}
            {{- if .Values.observability.structuredLogs.json }}
            - name: HOSTED_AGENT_LOG_FORMAT
              value: "json"
            {{- end }}
            - name: HOSTED_AGENT_OBSERVABILITY_STORE
              value: {{ .Values.observability.store | default "memory" | quote }}
            - name: HOSTED_AGENT_POSTGRES_POOL_MAX
              value: {{ $obsPg.poolMax | default 5 | toString | quote }}
            {{- if $postgresUrlPlain }}
            - name: HOSTED_AGENT_POSTGRES_URL
              value: {{ $postgresUrlPlain | quote }}
            {{- else if $pgSecName }}
            - name: HOSTED_AGENT_POSTGRES_URL
              valueFrom:
                secretKeyRef:
                  name: {{ $pgSecName }}
                  key: {{ $pgSecKey }}
            {{- end }}
            {{- if .Values.checkpoints.enabled }}
            - name: HOSTED_AGENT_CHECKPOINTS_ENABLED
              value: "true"
            - name: HOSTED_AGENT_CHECKPOINT_BACKEND
              value: {{ .Values.checkpoints.backend | quote }}
            {{- end }}
            {{- if .Values.wandb.enabled }}
            - name: HOSTED_AGENT_WANDB_ENABLED
              value: "true"
            {{- if .Values.wandb.project }}
            - name: WANDB_PROJECT
              value: {{ .Values.wandb.project | quote }}
            {{- end }}
            {{- if .Values.wandb.entity }}
            - name: WANDB_ENTITY
              value: {{ .Values.wandb.entity | quote }}
            {{- end }}
            {{- end }}
            {{- if .Values.scrapers.slack.feedback.enabled }}
            - name: HOSTED_AGENT_SLACK_FEEDBACK_ENABLED
              value: "true"
            - name: HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON
              valueFrom:
                configMapKeyRef:
                  name: {{ include "declarative-agent-library-chart.fullname" . }}-config
                  key: slack-emoji-label-map.json
            {{- end }}
            {{- if .Values.scrapers.slack.feedback.labelRegistry }}
            - name: HOSTED_AGENT_LABEL_REGISTRY_JSON
              valueFrom:
                configMapKeyRef:
                  name: {{ include "declarative-agent-library-chart.fullname" . }}-config
                  key: label-registry.json
            {{- end }}
            {{- $presence := .Values.presence | default dict }}
            {{- $slackPU := $presence.slack | default dict }}
            {{- $slackBot := $slackPU.botUserId | default dict }}
            {{- $slackSecName := $slackBot.secretName | default "" | trim }}
            {{- $slackSecKey := $slackBot.secretKey | default "" | trim }}
            {{- if and $slackSecName $slackSecKey }}
            - name: HOSTED_AGENT_SLACK_BOT_USER_ID
              valueFrom:
                secretKeyRef:
                  name: {{ $slackSecName }}
                  key: {{ $slackSecKey | quote }}
            {{- end }}
            {{- $jiraPU := $presence.jira | default dict }}
            {{- $jiraAcct := $jiraPU.botAccountId | default dict }}
            {{- $jiraSecName := $jiraAcct.secretName | default "" | trim }}
            {{- $jiraSecKey := $jiraAcct.secretKey | default "" | trim }}
            {{- if and $jiraSecName $jiraSecKey }}
            - name: HOSTED_AGENT_JIRA_BOT_ACCOUNT_ID
              valueFrom:
                secretKeyRef:
                  name: {{ $jiraSecName }}
                  key: {{ $jiraSecKey | quote }}
            {{- end }}
            {{- range .Values.extraEnv }}
            - name: {{ .name }}
              value: {{ .value | quote }}
            {{- end }}
          {{- with .Values.resources }}
          resources:
            {{- toYaml . | nindent 12 }}
          {{- end }}
{{- end -}}
