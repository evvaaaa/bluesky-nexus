#!/usr/bin/env bash
# =============================================================================
# Start the bluesky_nexus_container service with mounted volumes and configured
# environment variables.
#
# This script launches the NeXus writer container in detached mode as a
# persistent service. It automatically:
#
#   1. Defines container name, image name, and host/container paths.
#   2. Ensures that required host directories (data and logs) exist.
#   3. Removes any existing container with the same name to avoid conflicts.
#   4. Starts a new container with:
#        - Persistent restart policy (restart unless manually stopped).
#        - Mounted host volumes for file output and logging.
#        - Environment variables for runtime configuration (_NX_*, _ZMQ_*).
#        - Detached (background) execution.
#
# Environment variables passed into the container:
#   _NX_FILE_DIR_PATH     → directory inside container where NeXus files are written
#   _NX_LOG_FILE_DIR_PATH → directory inside container where logs are stored
#   _ZMQ_IP               → IP address of the Bluesky ZMQ publisher
#   _ZMQ_PORT             → Port of the Bluesky ZMQ publisher
#
# Restart policy:
#   --restart unless-stopped
#     - Container automatically restarts on crashes, daemon restarts, or host reboot.
#     - Container does NOT restart if manually stopped via `docker stop`.
#
# Usage:
#   Make the script executable:
#       chmod +x start_bluesky_nexus_container.sh
#
#   Run it:
#       ./start_bluesky_nexus_container.sh
#
# Notes:
#   - Existing containers named $CONTAINER_NAME are force-removed before starting.
#   - Host paths can be customized through HOST_DATA_DIR and HOST_LOG_DIR.
# =============================================================================

# --- Configuration -----------------------------------------------------------
CONTAINER_NAME="bluesky_nexus_writer"
declare -r IMAGE_NAME="bluesky_nexus_container"

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

# --- Remove existing container if present ------------------------------------
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo -e "Old container '${CONTAINER_NAME}' exists. Removing it...${RESET}"
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

docker run -d \
  --restart unless-stopped \
  --name "$CONTAINER_NAME" \
  --env _NX_FILE_DIR_PATH="$CONTAINER_DATA_DIR" \
  --env _NX_LOG_FILE_DIR_PATH="$CONTAINER_LOG_DIR" \
  --env _ZMQ_IP="$ZMQ_IP" \
  --env _ZMQ_PORT="$ZMQ_PORT" \
  -v "$HOST_DATA_DIR":"$CONTAINER_DATA_DIR" \
  -v "$HOST_LOG_DIR":"$CONTAINER_LOG_DIR" \
  "$IMAGE_NAME"

# -----------------------------------------------------------------------------
# End
# -----------------------------------------------------------------------------
