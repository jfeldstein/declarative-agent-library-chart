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
      {{- if and .Values.observability.prometheusAnnotations.enabled .Values.observability.plugins.prometheus.enabled }}
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
            {{- if .Values.observability.plugins.prometheus.enabled }}
            - name: HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED
              value: "true"
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
            {{- $wbPlug := .Values.observability.plugins.wandb | default dict }}
            {{- if $wbPlug.enabled }}
            - name: HOSTED_AGENT_WANDB_ENABLED
              value: "true"
            {{- if $wbPlug.project }}
            - name: WANDB_PROJECT
              value: {{ $wbPlug.project | quote }}
            {{- end }}
            {{- if $wbPlug.entity }}
            - name: WANDB_ENTITY
              value: {{ $wbPlug.entity | quote }}
            {{- end }}
            {{- end }}
            {{- $lf := .Values.observability.plugins.langfuse | default dict }}
            {{- if $lf.enabled | default false }}
            - name: HOSTED_AGENT_LANGFUSE_ENABLED
              value: "true"
            {{- $lfHost := $lf.host | default "" | trim }}
            {{- if $lfHost }}
            - name: HOSTED_AGENT_LANGFUSE_HOST
              value: {{ $lfHost | quote }}
            {{- end }}
            {{- $lfFlush := $lf.flushIntervalSeconds }}
            {{- if $lfFlush }}
            - name: HOSTED_AGENT_LANGFUSE_FLUSH_INTERVAL_SECONDS
              value: {{ $lfFlush | toString | quote }}
            {{- end }}
            {{- $lfPk := $lf.publicKeySecret | default dict }}
            {{- $lfPkName := $lfPk.secretName | default "" | trim }}
            {{- $lfPkKey := $lfPk.secretKey | default "public-key" | trim }}
            {{- if and $lfPkName $lfPkKey }}
            - name: HOSTED_AGENT_LANGFUSE_PUBLIC_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ $lfPkName | quote }}
                  key: {{ $lfPkKey | quote }}
            {{- end }}
            {{- $lfSk := $lf.secretKeySecret | default dict }}
            {{- $lfSkName := $lfSk.secretName | default "" | trim }}
            {{- $lfSkKey := $lfSk.secretKey | default "secret-key" | trim }}
            {{- if and $lfSkName $lfSkKey }}
            - name: HOSTED_AGENT_LANGFUSE_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ $lfSkName | quote }}
                  key: {{ $lfSkKey | quote }}
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
            {{- $jt := .Values.jiraTools | default dict }}
            {{- if $jt.enabled }}
            - name: HOSTED_AGENT_JIRA_TOOLS_ENABLED
              value: "true"
            - name: HOSTED_AGENT_JIRA_TOOLS_SIMULATED
              value: {{ $jt.simulated | default true | quote }}
            {{- $jtu := $jt.siteUrl | default "" | trim }}
            {{- if $jtu }}
            - name: HOSTED_AGENT_JIRA_TOOLS_SITE_URL
              value: {{ $jtu | quote }}
            {{- end }}
            - name: HOSTED_AGENT_JIRA_TOOLS_TIMEOUT_SECONDS
              value: {{ $jt.timeoutSeconds | default 30 | toString | quote }}
            - name: HOSTED_AGENT_JIRA_TOOLS_SCOPES_JSON
              value: {{ ($jt.scopes | default dict) | toJson | quote }}
            - name: HOSTED_AGENT_JIRA_TOOLS_ALLOWED_PROJECT_KEYS_JSON
              value: {{ ($jt.allowedProjectKeys | default list) | toJson | quote }}
            - name: HOSTED_AGENT_JIRA_TOOLS_MAX_SEARCH_RESULTS
              value: {{ $jt.maxSearchResults | default 50 | toString | quote }}
            - name: HOSTED_AGENT_JIRA_TOOLS_MAX_JQL_LENGTH
              value: {{ $jt.maxJqlLength | default 4000 | toString | quote }}
            {{- $jauth := $jt.auth | default dict }}
            {{- $jem := $jauth.emailSecretName | default "" | trim }}
            {{- $jek := $jauth.emailSecretKey | default "" | trim }}
            {{- if and $jem $jek }}
            - name: HOSTED_AGENT_JIRA_TOOLS_EMAIL
              valueFrom:
                secretKeyRef:
                  name: {{ $jem }}
                  key: {{ $jek | quote }}
            {{- end }}
            {{- $jtm := $jauth.tokenSecretName | default "" | trim }}
            {{- $jtk := $jauth.tokenSecretKey | default "" | trim }}
            {{- if and $jtm $jtk }}
            - name: HOSTED_AGENT_JIRA_TOOLS_API_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ $jtm }}
                  key: {{ $jtk | quote }}
            {{- end }}
            {{- end }}
            {{- $slackTrig := .Values.slackTrigger | default dict }}
            {{- if $slackTrig.enabled | default false }}
            - name: HOSTED_AGENT_SLACK_TRIGGER_ENABLED
              value: "true"
            {{- if $slackTrig.socketMode | default false }}
            - name: HOSTED_AGENT_SLACK_TRIGGER_SOCKET_MODE
              value: "true"
            {{- end }}
            {{- if $slackTrig.eventDedupe | default false }}
            - name: HOSTED_AGENT_SLACK_TRIGGER_EVENT_DEDUPE
              value: "true"
            {{- end }}
            {{- $trSign := $slackTrig.signingSecretSecretName | default "" | trim }}
            {{- $trSignKey := $slackTrig.signingSecretSecretKey | default "signing-secret" | trim }}
            {{- if and $trSign $trSignKey }}
            - name: HOSTED_AGENT_SLACK_TRIGGER_SIGNING_SECRET
              valueFrom:
                secretKeyRef:
                  name: {{ $trSign | quote }}
                  key: {{ $trSignKey | quote }}
            {{- end }}
            {{- $trApp := $slackTrig.appTokenSecretName | default "" | trim }}
            {{- $trAppKey := $slackTrig.appTokenSecretKey | default "app-token" | trim }}
            {{- if and $trApp $trAppKey }}
            - name: HOSTED_AGENT_SLACK_TRIGGER_APP_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ $trApp | quote }}
                  key: {{ $trAppKey | quote }}
            {{- end }}
            {{- $trBot := $slackTrig.botTokenSecretName | default "" | trim }}
            {{- $trBotKey := $slackTrig.botTokenSecretKey | default "token" | trim }}
            {{- if and $trBot $trBotKey }}
            - name: HOSTED_AGENT_SLACK_TRIGGER_BOT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ $trBot | quote }}
                  key: {{ $trBotKey | quote }}
            {{- end }}
            {{- end }}
            {{- $jiraTrig := .Values.jiraTrigger | default dict }}
            {{- if $jiraTrig.enabled | default false }}
            - name: HOSTED_AGENT_JIRA_TRIGGER_ENABLED
              value: "true"
            {{- if $jiraTrig.eventDedupe | default false }}
            - name: HOSTED_AGENT_JIRA_TRIGGER_EVENT_DEDUPE
              value: "true"
            {{- end }}
            {{- $jhp := $jiraTrig.httpPath | default "" | trim }}
            {{- if $jhp }}
            - name: HOSTED_AGENT_JIRA_TRIGGER_HTTP_PATH
              value: {{ $jhp | quote }}
            {{- end }}
            {{- $jwsec := $jiraTrig.webhookSecretSecretName | default "" | trim }}
            {{- $jwkey := $jiraTrig.webhookSecretSecretKey | default "webhook-secret" | trim }}
            {{- if and $jwsec $jwkey }}
            - name: HOSTED_AGENT_JIRA_TRIGGER_WEBHOOK_SECRET
              valueFrom:
                secretKeyRef:
                  name: {{ $jwsec | quote }}
                  key: {{ $jwkey | quote }}
            {{- end }}
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
