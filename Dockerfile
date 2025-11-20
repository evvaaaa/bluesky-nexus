# -----------------------------------------------------------------------------
# Dockerfile for Bluesky NeXus Writer Dispatcher
#
# This container runs the Bluesky NeXus writer using either ZeroMQ or Kafka as
# document transport sources.
#
# Environment variables required at runtime:
#   - _NX_FILE_DIR_PATH         : required: Directory where NeXus files are
#                                 written.
#   - _NX_LOG_FILE_DIR_PATH     : required: Directory for log file output.
#   - _ZMQ_IP                   : required: IP address of the Bluesky ZeroMQ
#                                 proxy.
#   - _ZMQ_PORT                 : required: Port of the Bluesky ZeroMQ proxy.
#   - _OPHYD_CPT_NAME_DELIMITER : optional: Component name delimiter in
#                                 documents.
#   - _KAFKA_BROKERS            : optional: Kafka bootstrap servers.
#   - _KAFKA_GROUP              : optional: Kafka consumer group.
#   - _KAFKA_TOPIC              : required for Kafka mode.
#
# Notes:
#   - The directories `/data` and `/logs` are created during image build. When
#     not mounted, they exist only inside the container.
#   - To persist output and logs, mount host directories using `-v` bindings.
#
# How to build the image:
#   docker build --no-cache -t bluesky_nexus_writer:latest .
#
# How to run the container:
#
#   1) Default mode (ZeroMQ):
#      docker run bluesky_nexus_writer
#      expands to:
#      python -m bluesky_nexus zmq
#
#   2) Override the dispatcher mode (Kafka example):
#      docker run bluesky_nexus_writer kafka --kafka-topic xyz \
#                 --kafka-brokers localhost:9092
#      expands to:
#      python -m bluesky_nexus kafka --kafka-topic xyz \
#             --kafka-brokers localhost:9092
#
# How to start the container using the provided script:
#   Execute: scripts/start_bluesky_nexus_container.sh
#
# -----------------------------------------------------------------------------


# ---- Base image ----
FROM python:3.10-slim AS base


# ---- Build arguments ----
ARG REPO_URL="https://codebase.helmholtz.cloud/hzb/bluesky/core/source/bluesky_nexus.git"
ARG REPO_BRANCH="5652_feature"

# ---- System deps ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# ----  Define working directory ----
WORKDIR /app

# ---- Clone 'bluesky_nexus' repo using build args ----
RUN git clone --branch ${REPO_BRANCH} ${REPO_URL} .

# ---- Install uv ----
RUN pip install -U uv

# ---- Install package and dependencies ----
RUN uv pip install --system --no-cache-dir . \
    && uv pip install --system --no-cache-dir pyzmq \
    && uv pip install --system --no-cache-dir bluesky-kafka


# ---- Create default directories ----
RUN mkdir -p /data /logs

# ---- Run NeXus writer dispatcher on when container starts ----
ENTRYPOINT ["python", "-m", "bluesky_nexus"]
CMD ["zmq"]
