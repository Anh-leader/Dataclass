FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend

COPY web-02/backend/requirements.txt /tmp/web02-requirements.txt
COPY web-02/backend/graph-requirements.txt /tmp/graph-requirements.txt
RUN pip install --no-cache-dir -r /tmp/web02-requirements.txt -r /tmp/graph-requirements.txt

COPY web-02/backend /app/backend
COPY DA-Agent-drive/graph /opt/DA-Agent-drive/graph
RUN useradd --uid 10001 --create-home appuser && mkdir -p /data && chown -R appuser:appuser /data
ENV PYTHONPATH=/opt/DA-Agent-drive:/app/backend DA_AGENT_DIR=/opt/DA-Agent-drive WEB02_DATA_DIR=/data
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
