#!/usr/bin/env bash

# =============================================================================
# Start the bluesky_nexus_writer service with mounted volumes and configured
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
#        - Environment variables for runtime configuration (_NX_*, _ZMQ_*, etc.).
#        - Detached (background) execution.
#
# Inside the container, the NeXus writer service is started via:
#
#        python -m bluesky_nexus
#
# Environment variables passed into the container:
#
#   _NX_FILE_DIR_PATH
#       Directory inside the container where NeXus files are written.
#
#   _NX_LOG_FILE_DIR_PATH
#       Directory inside the container where writer logs are stored.
#
#   _ZMQ_IP
#       IP address of the Bluesky ZMQ publisher (data stream source).
#
#   _ZMQ_PORT
#       Port of the Bluesky ZMQ publisher.
#
#   _OPHYD_CPT_NAME_DELIMITER (optional)
#       If defined and non-empty, this value is forwarded into the container
#       and used by bluesky-nexus to override the default Component
#       name delimiter used when expanding Ophyd device component names.
#
#       - If unset or empty: the default behavior is used : "_" (underscore)
#       - If set to a non-empty string: the custom delimiter is applied.
#
#
# Restart policy:
#
#   --restart unless-stopped
#     - Container automatically restarts on crashes, daemon restarts, or host reboot.
#     - Container does NOT restart if manually stopped via `docker stop`.
#
#
# Usage:
#
#   chmod +x start_bluesky_nexus_container.sh
#   ./start_bluesky_nexus_container.sh
#
# =============================================================================


# --- Configuration -----------------------------------------------------------
CONTAINER_NAME="bluesky_nexus_writer"
declare -r IMAGE_NAME="bluesky_nexus_writer"

# Host directories (change if needed)
HOST_DATA_DIR="$HOME/nexus_output"
HOST_LOG_DIR="$HOME/nexus_logs"

# Container directories
CONTAINER_DATA_DIR="/data"
CONTAINER_LOG_DIR="/logs"

# Bluesky ZMQ proxy connection
ZMQ_IP="localhost"
ZMQ_PORT="5578"

# Optional variable:
# - can be commented out          -> Not taken into account
# - can be set to an empty string -> Not taken into account
# - can be set to a valid string  -> Taken into account
OPHYD_CPT_NAME_DELIMITER=""

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


# Arguments common for both following docker run commands
COMMON_RUN_ARGS=(
  --restart unless-stopped
  --network host
  --name "$CONTAINER_NAME"
  --env _NX_FILE_DIR_PATH="$CONTAINER_DATA_DIR"
  --env _NX_LOG_FILE_DIR_PATH="$CONTAINER_LOG_DIR"
  --env _ZMQ_IP="$ZMQ_IP"
  --env _ZMQ_PORT="$ZMQ_PORT"
  -v "$HOST_DATA_DIR":"$CONTAINER_DATA_DIR"
  -v "$HOST_LOG_DIR":"$CONTAINER_LOG_DIR"
)

# ---- Switch ----

# OPHYD_CPT_NAME_DELIMITER exists and is not empty
if [[ -n "$OPHYD_CPT_NAME_DELIMITER" ]]; then
    echo "Using OPHYD_CPT_NAME_DELIMITER='$OPHYD_CPT_NAME_DELIMITER'"
    docker run -d \
      "${COMMON_RUN_ARGS[@]}" \
      --env _OPHYD_CPT_NAME_DELIMITER="$OPHYD_CPT_NAME_DELIMITER" \
      "$IMAGE_NAME"

# OPHYD_CPT_NAME_DELIMITER does not exists or is empty
else
    echo "OPHYD_CPT_NAME_DELIMITER empty or unset -> default mode"
    docker run -d \
      "${COMMON_RUN_ARGS[@]}" \
      "$IMAGE_NAME"
fi

# -----------------------------------------------------------------------------
# End
# -----------------------------------------------------------------------------
