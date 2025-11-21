#!/usr/bin/env bash

# =============================================================================
# Start the bluesky_nexus_writer service with mounted volumes and configured
# environment variables.
#
# This script launches the NeXus writer container in detached mode as a
# persistent service. It supports two dispatcher modes:
#
#   - ZMQ   : Uses Bluesky ZeroMQ RemoteDispatcher
#   - Kafka : Uses Bluesky Kafka RemoteDispatcher
#
# The mode is selected via the DISPATCHER_MODE variable (default: zmq).
#
# Inside the container, the service starts via:
#
#        python -m bluesky_nexus <mode>
#
# where <mode> is either "zmq" or "kafka".
#
# Environment variables passed into the container:
#
#   _NX_FILE_DIR_PATH
#       Directory inside the container where NeXus files are written.
#
#   _NX_LOG_FILE_DIR_PATH
#       Directory inside the container where writer logs are stored.
#
#   ZMQ MODE:
#       _ZMQ_IP
#       _ZMQ_PORT
#
#   KAFKA MODE:
#       _KAFKA_BROKERS
#       _KAFKA_GROUP       (optional)
#       _KAFKA_TOPIC       (required)
#
#   _OPHYD_CPT_NAME_DELIMITER (optional)
#       Custom ophyd component delimiter. If unset or empty, defaults are used.
#
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
# Common docker run arguments
# =============================================================================
COMMON_RUN_ARGS=(
  --restart unless-stopped
  --network host
  --name "$CONTAINER_NAME"
  --env _NX_FILE_DIR_PATH="$CONTAINER_DATA_DIR"
  --env _NX_LOG_FILE_DIR_PATH="$CONTAINER_LOG_DIR"
  --env _NX_LOG_FILE_NAME="feu_chatterton.log"
  --env _NX_LOG_FILE_MAX_SIZE="5242880"
  --env _NX_BACKUP_COUNT="6"
  --env _NX_CONSOLE_LOG_LEVEL="ERROR"
  --env _NX_FILE_LOG_LEVEL="DEBUG"
  --env _NX_ENABLE_CONSOLE_LOG="true"
  --env _NX_ENABLE_FILE_LOG="true"

  -v "$HOST_DATA_DIR":"$CONTAINER_DATA_DIR"
  -v "$HOST_LOG_DIR":"$CONTAINER_LOG_DIR"
)


# ------------------------- ZMQ MODE ------------------------------------------
if [[ "$DISPATCHER_MODE" == "zmq" ]]; then
    COMMON_RUN_ARGS+=(
      --env _ZMQ_IP="$ZMQ_IP"
      --env _ZMQ_PORT="$ZMQ_PORT"
    )
fi

# ------------------------- KAFKA MODE ----------------------------------------
if [[ "$DISPATCHER_MODE" == "kafka" ]]; then
    COMMON_RUN_ARGS+=(
      --env _KAFKA_BROKERS="$KAFKA_BROKERS"
      --env _KAFKA_GROUP="$KAFKA_GROUP"
      --env _KAFKA_TOPIC="$KAFKA_TOPIC"
    )
fi


# ------------------------- Optional delimiter --------------------------------
if [[ -n "$OPHYD_CPT_NAME_DELIMITER" ]]; then
    echo "Using OPHYD_CPT_NAME_DELIMITER='$OPHYD_CPT_NAME_DELIMITER'"
    COMMON_RUN_ARGS+=( --env _OPHYD_CPT_NAME_DELIMITER="$OPHYD_CPT_NAME_DELIMITER" )
else
    echo "OPHYD_CPT_NAME_DELIMITER empty or unset -> default behavior"
fi


# =============================================================================
# Run container
# =============================================================================
docker run -d \
  "${COMMON_RUN_ARGS[@]}" \
  "$IMAGE_NAME" \
  "$DISPATCHER_MODE"

echo
echo "Container '$CONTAINER_NAME' started in mode: $DISPATCHER_MODE"
echo "Use 'docker logs -f $CONTAINER_NAME' to follow logs."
echo "Use 'docker stop $CONTAINER_NAME' to stop it."
echo "Use 'docker rm -f $CONTAINER_NAME' to remove it."
echo
echo "Done."
