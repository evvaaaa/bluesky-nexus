# -----------------------------------------------------------------------------
# Dockerfile for the Bluesky NeXus Writer Service
#
# This container packages and runs the full `bluesky_nexus` CLI application,
# including its ZeroMQ and Kafka RemoteDispatcher backends. The container
# launches the CLI via:
#
#       python -m bluesky_nexus [GLOBAL LOGGING OPTIONS] <zmq|kafka> [...]
#
# The dispatcher backend defaults to **ZeroMQ** unless explicitly overridden.
#
# =============================================================================
# RUNTIME CONFIGURATION (ENVIRONMENT VARIABLES)
# =============================================================================
# The service supports two levels of configuration:
#   1) Top-level logging configuration (shared across all backends)
#   2) Backend-specific configuration (ZMQ or Kafka)
#
# All CLI arguments may be replaced by environment variables.
# CLI arguments ALWAYS override environment variables.
#
# -----------------------------------------------------------------------------
# Top-Level Logging (must be passed BEFORE the backend subcommand)
# -----------------------------------------------------------------------------
# All logging settings are optional. If neither --log-dir nor
# _NX_LOG_FILE_DIR_PATH is defined, file logging is disabled and only console
# logging is used (if enabled).
#
# Environment variables:
#
#   _NX_LOG_FILE_DIR_PATH       (optional)      Directory for log file output.
#   _NX_CONSOLE_LOG_LEVEL       (optional)      Console log level, (default: ERROR)
#                                               [DEBUG|INFO|WARNING|ERROR|CRITICAL]
#   _NX_FILE_LOG_LEVEL          (optional)      File log level (default: DEBUG)
#                                               [DEBUG|INFO|WARNING|ERROR|CRITICAL]
#   _NX_LOG_FILE_NAME           (optional)      Log filename (default: nx_log.log)
#   _NX_LOG_FILE_MAX_SIZE       (optional)      Max size (bytes) before rotation
#                                               (default: 10 MB = 10 * 1024 * 1024)
#   _NX_BACKUP_COUNT            (optional)      Number of rotated log files
#                                               (default: 5)
#   _NX_ENABLE_CONSOLE_LOG      (optional)      Enable console logs [True|False]
#                                               (default: True)
#   _NX_ENABLE_FILE_LOG         (optional)      Enable file logs    [True|False]
#                                               (default: True)
#
# -----------------------------------------------------------------------------
# ZeroMQ Backend (selected with: `python -m bluesky_nexus zmq ...`)
# -----------------------------------------------------------------------------
# Required
#   _ZMQ_IP                   Publisher IP for Bluesky ZMQ stream
#   _ZMQ_PORT                 Publisher port
#   _NX_FILE_DIR_PATH         Directory where NeXus files will be written
#
# Optional:
#   _OPHYD_CPT_NAME_DELIMITER Custom ophyd component name delimiter
#                             (default: '_')
#
# -----------------------------------------------------------------------------
# Kafka Backend (selected with: `python -m bluesky_nexus kafka ...`)
# -----------------------------------------------------------------------------
# Required:
#   _KAFKA_BROKERS            Comma-separated Kafka bootstrap servers
#   _KAFKA_TOPIC              Kafka topic containing Bluesky documents
#   _NX_FILE_DIR_PATH         Directory where NeXus files will be written
#
# Optional:
#   _KAFKA_GROUP              Kafka consumer group (default: "default")
#   _OPHYD_CPT_NAME_DELIMITER Custom ophyd component delimiter
#                             (default: '_')
#
# =============================================================================
# NOTES
# =============================================================================
# • Directories `/data` and `/logs` are created inside the image at build time.
#   To persist NeXus files or logs, mount external directories with `-v`.
#       -v /host/data:/data
#       -v /host/logs:/logs
#
# • ENTRYPOINT launches the CLI directly:
#       ENTRYPOINT ["python", "-m", "bluesky_nexus"]
#   The CMD selects the default backend:
#       CMD ["zmq"]
#
#   Thus:
#       docker run bluesky_nexus_writer
#   runs:
#       python -m bluesky_nexus zmq
#
# • Example: Run Kafka dispatcher
#       docker run bluesky_nexus_writer \
#            --log-dir /logs \
#            kafka \
#            --kafka-brokers "localhost:9092" \
#            --kafka-topic "bluesky.documents"
#
# • Recommended starter script:
#       scripts/start_bluesky_nexus_container.sh
#
# =============================================================================
# Build:
#   docker build --no-cache -t bluesky_nexus_writer:latest .
#
# Run:
#   docker run -v /host/data:/data -v /host/logs:/logs bluesky_nexus_writer
# -----------------------------------------------------------------------------


# ---- Base image ----
FROM python:3.10-slim AS base


# ---- Build arguments ----
ARG REPO_URL="https://codebase.helmholtz.cloud/hzb/bluesky/core/source/bluesky_nexus.git"
ARG REPO_BRANCH="develop"

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
RUN uv pip install --system --no-cache-dir .

# ---- Create default directories ----
RUN mkdir -p /data /logs

# ---- Run NeXus writer dispatcher on when container starts ----
ENTRYPOINT ["python", "-m", "bluesky_nexus"]
CMD ["zmq"]
