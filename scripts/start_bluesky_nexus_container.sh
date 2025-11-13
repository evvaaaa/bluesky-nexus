#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Start the bluesky_nexus_container with mounted volumes and environment vars
# -----------------------------------------------------------------------------

# --- Configuration -----------------------------------------------------------
CONTAINER_NAME="bluesky_nexus_writer"
IMAGE_NAME="bluesky_nexus_container"

# Host directories (change if needed)
HOST_DATA_DIR="$HOME/nexus_output"
HOST_LOG_DIR="$HOME/nexus_logs"

# Container directories
CONTAINER_DATA_DIR="/data"
CONTAINER_LOG_DIR="/logs"

# Bluesky ZMQ proxy connection
ZMQ_IP="127.0.0.1"
ZMQ_PORT="5578"

# -----------------------------------------------------------------------------
# Ensure output directories exist on host
# -----------------------------------------------------------------------------
mkdir -p "$HOST_DATA_DIR" "$HOST_LOG_DIR"

# -----------------------------------------------------------------------------
# Run container
# -----------------------------------------------------------------------------
echo "Starting container '$CONTAINER_NAME' from image '$IMAGE_NAME'..."
echo "Mounting:"
echo "  Host data -> $HOST_DATA_DIR"
echo "  Host logs -> $HOST_LOG_DIR"
echo "Connecting to ZMQ at ${ZMQ_IP}:${ZMQ_PORT}"
echo

docker run -it --rm \
  --name $CONTAINER_NAME \
  --env _NX_FILE_DIR_PATH=$CONTAINER_DATA_DIR \
  --env _NX_LOG_FILE_DIR_PATH=$CONTAINER_LOG_DIR \
  --env _ZMQ_IP=$ZMQ_IP \
  --env _ZMQ_PORT=$ZMQ_PORT \
  -v "$HOST_DATA_DIR":$CONTAINER_DATA_DIR \
  -v "$HOST_LOG_DIR":$CONTAINER_LOG_DIR \
  $IMAGE_NAME

# -----------------------------------------------------------------------------
# End
# -----------------------------------------------------------------------------
