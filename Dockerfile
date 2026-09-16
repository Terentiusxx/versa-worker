FROM ghcr.io/ggml-org/llama.cpp:server-cuda13

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        ca-certificates \
        curl && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv

COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app

COPY app.py /app/app.py
COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 8000

ENTRYPOINT []
CMD ["/app/start.sh"]
