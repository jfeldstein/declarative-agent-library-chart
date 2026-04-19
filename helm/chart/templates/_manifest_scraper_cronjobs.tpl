{{- define "declarative-agent-library-chart.manifest.scraperCronjobs" -}}
{{/* One CronJob per enabled scraper job; secrets via env (Secret refs), config via mounted ConfigMap. Traceability: [DALC-REQ-RAG-SCRAPERS-002] [DALC-REQ-RAG-SCRAPERS-005] [DALC-REQ-SCRAPER-CURSOR-003] [DALC-REQ-SCRAPER-CURSOR-004] */}}
{{- $root := . }}
{{- $cursorBackend := default "file" $root.Values.scrapers.cursorStore.backend }}
{{- $cursorStoreSecretName := default "" $root.Values.scrapers.cursorStore.postgresUrlSecretName }}
{{- $cursorStoreSecretKey := default "url" $root.Values.scrapers.cursorStore.postgresUrlSecretKey }}
{{- $hasScraperJobs := or (and $root.Values.scrapers.jira.enabled $root.Values.scrapers.jira.jobs) (and $root.Values.scrapers.slack.enabled $root.Values.scrapers.slack.jobs) }}
{{- if and (eq $cursorBackend "postgres") $hasScraperJobs (not $cursorStoreSecretName) (not $root.Values.checkpoints.postgresUrl) }}
{{- fail "scrapers.cursorStore.backend=postgres requires scrapers.cursorStore.postgresUrlSecretName or checkpoints.postgresUrl (shared DSN for HOSTED_AGENT_POSTGRES_URL)" }}
{{- end }}
{{- if and $root.Values.scrapers.jira.enabled $root.Values.scrapers.jira.jobs }}
{{- range $ji, $job := $root.Values.scrapers.jira.jobs }}
{{- if or (not (hasKey $job "enabled")) $job.enabled }}
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {{ include "declarative-agent-library-chart.fullname" $root }}-scraper-jira-{{ $ji }}
  labels:
    {{- include "declarative-agent-library-chart.labels" $root | nindent 4 }}
    app.kubernetes.io/component: scraper
    scraper.agentic.dalc/source: jira
    scraper.agentic.dalc/index: {{ $ji | quote }}
spec:
  schedule: {{ $job.schedule | quote }}
  concurrencyPolicy: {{ default "Forbid" $job.concurrencyPolicy | quote }}
  successfulJobsHistoryLimit: 1
  failedJobsHistoryLimit: 2
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        metadata:
          {{- if $root.Values.observability.prometheusAnnotations.enabled }}
          annotations:
            prometheus.io/scrape: "true"
            prometheus.io/port: "9091"
            prometheus.io/path: "/metrics"
          {{- end }}
          labels:
            {{- include "declarative-agent-library-chart.selectorLabels" $root | nindent 12 }}
            app.kubernetes.io/component: scraper
            scraper.agentic.dalc/source: jira
            scraper.agentic.dalc/index: {{ $ji | quote }}
        spec:
          restartPolicy: OnFailure
          volumes:
            - name: scraper-job-config
              configMap:
                name: {{ include "declarative-agent-library-chart.fullname" $root }}-scraper-job-jira-{{ $ji }}
          containers:
            - name: scraper
              image: "{{ $root.Values.image.repository }}:{{ $root.Values.image.tag }}"
              imagePullPolicy: {{ $root.Values.image.pullPolicy }}
              command:
                - python
                - -m
                - agent.scrapers.jira_job
              ports:
                - name: metrics
                  containerPort: 9091
                  protocol: TCP
              volumeMounts:
                - name: scraper-job-config
                  mountPath: /config
                  readOnly: true
              env:
                - name: RAG_SERVICE_URL
                  value: {{ include "declarative-agent-library-chart.ragInternalBaseUrl" $root | quote }}
                - name: SCRAPER_JOB_CONFIG
                  value: /config/job.json
                - name: SCRAPER_NAME
                  value: {{ printf "jira-%d" $ji | quote }}
                - name: SCRAPER_SCOPE
                  value: {{ default (printf "%s-jira-%d" $root.Release.Name $ji) $job.scope | quote }}
                - name: SCRAPER_INTEGRATION
                  value: "jira"
                - name: SCRAPER_METRICS_ADDR
                  value: "0.0.0.0:9091"
                - name: SCRAPER_METRICS_GRACE_SECONDS
                  value: "35"
                {{- $siteUrl := default $root.Values.scrapers.jira.siteUrl $job.siteUrl }}
                {{- if $siteUrl }}
                - name: JIRA_SITE_URL
                  value: {{ $siteUrl | quote }}
                {{- end }}
                {{- $wmDir := default $root.Values.scrapers.jira.watermarkDir $job.watermarkDir }}
                {{- if $wmDir }}
                - name: JIRA_WATERMARK_DIR
                  value: {{ $wmDir | quote }}
                {{- end }}
                {{- with $root.Values.scrapers.jira.auth }}
                {{- if .emailSecretName }}
                - name: JIRA_EMAIL
                  valueFrom:
                    secretKeyRef:
                      name: {{ .emailSecretName | quote }}
                      key: {{ .emailSecretKey | quote }}
                {{- end }}
                {{- if .tokenSecretName }}
                - name: JIRA_API_TOKEN
                  valueFrom:
                    secretKeyRef:
                      name: {{ .tokenSecretName | quote }}
                      key: {{ .tokenSecretKey | quote }}
                {{- end }}
                {{- end }}
                {{- if eq $cursorBackend "postgres" }}
                - name: SCRAPER_CURSOR_BACKEND
                  value: postgres
                {{- if $cursorStoreSecretName }}
                - name: SCRAPER_POSTGRES_URL
                  valueFrom:
                    secretKeyRef:
                      name: {{ $cursorStoreSecretName | quote }}
                      key: {{ $cursorStoreSecretKey | quote }}
                {{- else if $root.Values.checkpoints.postgresUrl }}
                - name: HOSTED_AGENT_POSTGRES_URL
                  value: {{ $root.Values.checkpoints.postgresUrl | quote }}
                {{- end }}
                {{- end }}
              {{- with $root.Values.scrapers.resources }}
              resources:
                {{- toYaml . | nindent 16 }}
              {{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- if and $root.Values.scrapers.slack.enabled $root.Values.scrapers.slack.jobs }}
{{- range $si, $job := $root.Values.scrapers.slack.jobs }}
{{- if or (not (hasKey $job "enabled")) $job.enabled }}
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {{ include "declarative-agent-library-chart.fullname" $root }}-scraper-slack-{{ $si }}
  labels:
    {{- include "declarative-agent-library-chart.labels" $root | nindent 4 }}
    app.kubernetes.io/component: scraper
    scraper.agentic.dalc/source: slack
    scraper.agentic.dalc/index: {{ $si | quote }}
spec:
  schedule: {{ $job.schedule | quote }}
  concurrencyPolicy: {{ default "Forbid" $job.concurrencyPolicy | quote }}
  successfulJobsHistoryLimit: 1
  failedJobsHistoryLimit: 2
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        metadata:
          {{- if $root.Values.observability.prometheusAnnotations.enabled }}
          annotations:
            prometheus.io/scrape: "true"
            prometheus.io/port: "9091"
            prometheus.io/path: "/metrics"
          {{- end }}
          labels:
            {{- include "declarative-agent-library-chart.selectorLabels" $root | nindent 12 }}
            app.kubernetes.io/component: scraper
            scraper.agentic.dalc/source: slack
            scraper.agentic.dalc/index: {{ $si | quote }}
        spec:
          restartPolicy: OnFailure
          volumes:
            - name: scraper-job-config
              configMap:
                name: {{ include "declarative-agent-library-chart.fullname" $root }}-scraper-job-slack-{{ $si }}
          containers:
            - name: scraper
              image: "{{ $root.Values.image.repository }}:{{ $root.Values.image.tag }}"
              imagePullPolicy: {{ $root.Values.image.pullPolicy }}
              command:
                - python
                - -m
                - agent.scrapers.slack_job
              ports:
                - name: metrics
                  containerPort: 9091
                  protocol: TCP
              volumeMounts:
                - name: scraper-job-config
                  mountPath: /config
                  readOnly: true
              env:
                - name: RAG_SERVICE_URL
                  value: {{ include "declarative-agent-library-chart.ragInternalBaseUrl" $root | quote }}
                - name: SCRAPER_JOB_CONFIG
                  value: /config/job.json
                - name: SCRAPER_NAME
                  value: {{ printf "slack-%d" $si | quote }}
                - name: SCRAPER_SCOPE
                  value: {{ default (printf "%s-slack-%d" $root.Release.Name $si) $job.scope | quote }}
                - name: SCRAPER_INTEGRATION
                  value: "slack"
                - name: SCRAPER_METRICS_ADDR
                  value: "0.0.0.0:9091"
                - name: SCRAPER_METRICS_GRACE_SECONDS
                  value: "35"
                {{- with $root.Values.scrapers.slack.stateDir }}
                - name: SLACK_STATE_DIR
                  value: {{ . | quote }}
                {{- end }}
                {{- with $root.Values.scrapers.slack.auth }}
                {{- if .botTokenSecretName }}
                - name: SLACK_BOT_TOKEN
                  valueFrom:
                    secretKeyRef:
                      name: {{ .botTokenSecretName | quote }}
                      key: {{ .botTokenSecretKey | quote }}
                {{- end }}
                {{- if .userTokenSecretName }}
                - name: SLACK_USER_TOKEN
                  valueFrom:
                    secretKeyRef:
                      name: {{ .userTokenSecretName | quote }}
                      key: {{ .userTokenSecretKey | quote }}
                {{- end }}
                {{- end }}
                {{- if eq $cursorBackend "postgres" }}
                - name: SCRAPER_CURSOR_BACKEND
                  value: postgres
                {{- if $cursorStoreSecretName }}
                - name: SCRAPER_POSTGRES_URL
                  valueFrom:
                    secretKeyRef:
                      name: {{ $cursorStoreSecretName | quote }}
                      key: {{ $cursorStoreSecretKey | quote }}
                {{- else if $root.Values.checkpoints.postgresUrl }}
                - name: HOSTED_AGENT_POSTGRES_URL
                  value: {{ $root.Values.checkpoints.postgresUrl | quote }}
                {{- end }}
                {{- end }}
              {{- with $root.Values.scrapers.resources }}
              resources:
                {{- toYaml . | nindent 16 }}
              {{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end -}}
