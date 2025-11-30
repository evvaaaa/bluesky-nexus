#!/usr/bin/env bash

# =============================================================================
# Start the Bluesky NeXus Writer service as a persistent Docker container.
#
# This script launches the `bluesky_nexus_writer` container with mounted
# host directories and fully configured environment variables. It supports
# both available dispatcher backends:
#
#   - ZMQ   : Bluesky ZeroMQ RemoteDispatcher
#   - Kafka : Bluesky Kafka RemoteDispatcher
#
# The backend is selected using DISPATCHER_MODE (default: "zmq").
#
# Inside the container, the service runs via:
#
#       python -m bluesky_nexus <zmq|kafka>
#
# =====================================================================
# Logging Configuration (applies to all backends)
# =====================================================================
# Logging MUST be configured before the backend subcommand. This script
# sets the following environment variables for the container:
#
#   _NX_LOG_FILE_DIR_PATH   Directory for log file output (mounted to /logs)
#   _NX_LOG_FILE_NAME       Log filename      (default here: bluesky_nexus_writer.log)
#   _NX_LOG_FILE_MAX_SIZE   Log rotation size (default here: 5 MB)
#   _NX_BACKUP_COUNT        Number of rotated logs (default here: 6)
#   _NX_CONSOLE_LOG_LEVEL   Console level (default: ERROR)
#   _NX_FILE_LOG_LEVEL      File level    (default: DEBUG)
#   _NX_ENABLE_CONSOLE_LOG  Enable console logging [True|False] (default: True)
#
# These override the defaults defined in the Python code.
#
# =====================================================================
# Backend Configuration
# =====================================================================
# ZMQ Mode:
#   _ZMQ_IP                   ZeroMQ publisher IP
#   _ZMQ_PORT                 ZeroMQ publisher port
#   _NX_FILE_DIR_PATH         Directory where NeXus files are written
#
# Kafka Mode:
#   _KAFKA_BROKERS            Kafka bootstrap servers (required)
#   _KAFKA_TOPIC              Kafka topic for Bluesky documents (required)
#   _KAFKA_GROUP              Kafka consumer group (optional, default: "default")
#   _NX_FILE_DIR_PATH         Directory where NeXus files are written
#
# Optional:
#   _OPHYD_CPT_NAME_DELIMITER Component delimiter for ophyd names
#                             If unset or empty → default behaviour is used.
#
# =====================================================================
# Volumes
# =====================================================================
# Host directories are mounted:
#   $HOST_DATA_DIR → /data : NeXus file output
#   $HOST_LOG_DIR  → /logs : Writer log output
#
# =====================================================================
# Additional Notes
# =====================================================================
# • Container is started with '--restart unless-stopped'.
# • Uses host networking (--network host).
# • Any existing container with the same name is removed first.
# =============================================================================


# ------------------------- Mode selection ------------------------------------
# Available values: "zmq" or "kafka"
DISPATCHER_MODE="zmq"

# ------------------------- Configuration -------------------------------------
CONTAINER_NAME="bluesky_nexus_writer"
declare -r IMAGE_NAME="bluesky_nexus_writer"

# Host directories (change if needed)
HOST_DATA_DIR="$HOME/nexus_output"
HOST_LOG_DIR="$HOME/nexus_logs"

# Container directories
CONTAINER_DATA_DIR="/data"
CONTAINER_LOG_DIR="/logs"

# ------------------------- ZMQ Configuration ---------------------------------
ZMQ_IP="localhost"
ZMQ_PORT="5578"

# ------------------------- Kafka Configuration -------------------------------
KAFKA_BROKERS="localhost:9092"  # e.g. "localhost:9092"
KAFKA_GROUP="Nexus-Writer"      # optional
KAFKA_TOPIC="bluesky.documents" # required for Kafka mode

# ------------------------- Optional ophyd delimiter ---------------------------
OPHYD_CPT_NAME_DELIMITER=""


# =============================================================================
# Validate mode-specific requirements
# =============================================================================
if [[ "$DISPATCHER_MODE" == "kafka" ]]; then
    if [[ -z "$KAFKA_TOPIC" ]]; then
        echo "ERROR: Kafka mode requires KAFKA_TOPIC to be set."
        exit 1
    fi
    if [[ -z "$KAFKA_BROKERS" ]]; then
        echo "ERROR: Kafka mode requires KAFKA_BROKERS to be set."
        exit 1
    fi
fi

# =============================================================================
# Ensure output directories exist on host
# =============================================================================
mkdir -p "$HOST_DATA_DIR" "$HOST_LOG_DIR"

echo "Starting NeXus Writer container in '$DISPATCHER_MODE' mode..."
echo "Container name : $CONTAINER_NAME"
echo "Image name     : $IMAGE_NAME"
echo "Host data dir  : $HOST_DATA_DIR"
echo "Host log dir   : $HOST_LOG_DIR"
echo


# =============================================================================
# Verify that the image exists before continuing
# =============================================================================
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "ERROR: Docker image '$IMAGE_NAME' not found."
    exit 1
fi


# =============================================================================
# Remove existing container
# =============================================================================
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Old container '${CONTAINER_NAME}' exists. Removing it..."
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi


# =============================================================================
# Base env vars for logging (override defaults)
# =============================================================================
ENV_VARS=(
  --env _NX_FILE_DIR_PATH="$CONTAINER_DATA_DIR"
  --env _NX_LOG_FILE_DIR_PATH="$CONTAINER_LOG_DIR"
  --env _NX_LOG_FILE_NAME="bluesky_nexus_writer.log"
  --env _NX_LOG_FILE_MAX_SIZE="5242880"
  --env _NX_BACKUP_COUNT="6"
  --env _NX_CONSOLE_LOG_LEVEL="ERROR"
  --env _NX_FILE_LOG_LEVEL="DEBUG"
  --env _NX_ENABLE_CONSOLE_LOG="True"
)


# ------------------------- ZMQ MODE ------------------------------------------
if [[ "$DISPATCHER_MODE" == "zmq" ]]; then
    ENV_VARS+=(
      --env _ZMQ_IP="$ZMQ_IP"
      --env _ZMQ_PORT="$ZMQ_PORT"
    )
fi

# ------------------------- KAFKA MODE ----------------------------------------
if [[ "$DISPATCHER_MODE" == "kafka" ]]; then
    ENV_VARS+=(
      --env _KAFKA_BROKERS="$KAFKA_BROKERS"
      --env _KAFKA_GROUP="$KAFKA_GROUP"
      --env _KAFKA_TOPIC="$KAFKA_TOPIC"
    )
fi


# ------------------------- Optional delimiter --------------------------------
if [[ -n "$OPHYD_CPT_NAME_DELIMITER" ]]; then
    echo "Using OPHYD_CPT_NAME_DELIMITER='$OPHYD_CPT_NAME_DELIMITER'"
    ENV_VARS+=( --env _OPHYD_CPT_NAME_DELIMITER="$OPHYD_CPT_NAME_DELIMITER" )
else
    echo "OPHYD_CPT_NAME_DELIMITER empty or unset -> default behavior"
fi


# =============================================================================
# Run container
# =============================================================================
docker run -d \
  --restart unless-stopped \
  --network host \
  --user "$(id -u)":"$(id -g)" \
  --name "$CONTAINER_NAME" \
  -v "$HOST_DATA_DIR":"$CONTAINER_DATA_DIR" \
  -v "$HOST_LOG_DIR":"$CONTAINER_LOG_DIR" \
  "${ENV_VARS[@]}" \
  "$IMAGE_NAME" \
  "$DISPATCHER_MODE"

echo
echo "Container '$CONTAINER_NAME' started in mode: $DISPATCHER_MODE"
echo "Use 'docker logs -f $CONTAINER_NAME' to follow logs."
echo "Use 'docker stop $CONTAINER_NAME' to stop it."
echo "Use 'docker rm -f $CONTAINER_NAME' to remove it."
echo
echo "Done."
