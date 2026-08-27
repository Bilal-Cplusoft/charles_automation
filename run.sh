#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly IMAGE_NAME="sports-squares-ui:latest"
readonly CONTAINER_NAME="sports-squares-ui"

readonly ENV_FILE="${SCRIPT_DIR}/.env"
readonly HOST_PORT="${APP_PORT:-9000}"

container_exists() {
  docker container inspect "${CONTAINER_NAME}" >/dev/null 2>&1
}

image_exists() {
  docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1
}

remove_container() {
  if container_exists; then
    printf 'Removing container %s...\n' "${CONTAINER_NAME}"
    docker container rm --force "${CONTAINER_NAME}" >/dev/null
  fi
}

remove_image() {
  if image_exists; then
    printf 'Removing image %s...\n' "${IMAGE_NAME}"
    docker image rm --force "${IMAGE_NAME}" >/dev/null
  fi
}

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM
  printf '\nCleaning up Docker resources...\n'
  remove_container || true
  remove_image || true
  exit "${exit_code}"
}

if ! command -v docker >/dev/null 2>&1; then
  printf 'Docker is not installed or is not available on PATH.\n' >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  printf "No .env file found. Creating one from .env.example...\n"
  cp "${SCRIPT_DIR}/.env.example" "${ENV_FILE}"
fi

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

cd "${SCRIPT_DIR}"

printf 'Removing previous Docker resources, if present...\n'
remove_container
remove_image

printf 'Building %s...\n' "${IMAGE_NAME}"
docker build --tag "${IMAGE_NAME}" .

printf 'Starting %s on port %s...\n' "${CONTAINER_NAME}" "${HOST_PORT}"

# Map the container volume with current dir so Python can pick up the GCP Key locally
docker run --detach \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  --env-file "${ENV_FILE}" \
  --publish "${HOST_PORT}:9000" \
  --volume "${SCRIPT_DIR}:/app" \
  "${IMAGE_NAME}" >/dev/null

printf 'Following logs. Press Ctrl+C to stop and remove the container and image.\n'
docker logs --follow "${CONTAINER_NAME}"
