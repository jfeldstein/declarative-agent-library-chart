{{- define "declarative-agent-library-chart.manifest.ragDeployment" -}}
{{- if include "declarative-agent-library-chart.ragDeployed" . }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "declarative-agent-library-chart.fullname" . }}-rag
  labels:
    {{- include "declarative-agent-library-chart.labels" . | nindent 4 }}
    app.kubernetes.io/component: rag
spec:
  replicas: {{ .Values.scrapers.ragService.replicaCount }}
  selector:
    matchLabels:
      {{- include "declarative-agent-library-chart.ragSelectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "declarative-agent-library-chart.ragSelectorLabels" . | nindent 8 }}
      {{- if and .Values.observability.prometheusAnnotations.enabled .Values.observability.plugins.prometheus.enabled }}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: {{ .Values.scrapers.ragService.service.port | quote }}
        prometheus.io/path: "/metrics"
      {{- end }}
    spec:
      containers:
        - name: rag
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          args:
            - agent.rag.app:create_app
            - --factory
            - --host
            - "0.0.0.0"
            - --port
            - {{ .Values.scrapers.ragService.service.port | quote }}
          command:
            - uvicorn
          ports:
            - name: http
              containerPort: {{ .Values.scrapers.ragService.service.port }}
              protocol: TCP
          {{- $consumer := .Values.observability.plugins.consumerPlugins | default list }}
          {{- if or (.Values.observability.plugins.prometheus.enabled) (gt (len $consumer) 0) }}
          env:
            {{- if .Values.observability.plugins.prometheus.enabled }}
            - name: HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED
              value: "true"
            {{- end }}
            {{/* [DALC-REQ-CHART-RTV-005] */}}
            {{- include "declarative-agent-library-chart.consumerPluginsEnv" . | nindent 12 }}
          {{- end }}
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 2
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
          {{- with .Values.scrapers.ragService.resources }}
          resources:
            {{- toYaml . | nindent 12 }}
          {{- end }}
{{- end }}
{{- end -}}
