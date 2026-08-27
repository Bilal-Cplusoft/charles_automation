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
    printf 'Removing existing container %s...\n' "${CONTAINER_NAME}"
    docker container rm --force "${CONTAINER_NAME}" >/dev/null
  fi
}

remove_image() {
  if image_exists; then
    printf 'Removing existing image %s...\n' "${IMAGE_NAME}"
    docker image rm --force "${IMAGE_NAME}" >/dev/null
  fi
}

if ! command -v docker >/dev/null 2>&1; then
  printf 'Error: Docker is not installed or not available on PATH.\n' >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  if [[ -f "${SCRIPT_DIR}/.env.example" ]]; then
    printf "No .env file found. Creating one from .env.example...\n"
    cp "${SCRIPT_DIR}/.env.example" "${ENV_FILE}"
  else
    printf "Warning: No .env or .env.example found. Proceeding with environment defaults.\n"
  fi
fi

cd "${SCRIPT_DIR}"

printf 'Stopping and cleaning up previous container deployment...\n'
remove_container
remove_image

printf 'Building production image %s...\n' "${IMAGE_NAME}"
docker build --tag "${IMAGE_NAME}" .

printf 'Starting container %s in detached mode on port %s...\n' "${CONTAINER_NAME}" "${HOST_PORT}"

docker run --detach \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  --env-file "${ENV_FILE}" \
  --publish "${HOST_PORT}:9000" \
  --volume "${SCRIPT_DIR}:/app" \
  "${IMAGE_NAME}" >/dev/null

printf '\n=======================================================\n'
printf ' Deployment successful!\n'
printf ' Container Name : %s\n' "${CONTAINER_NAME}"
printf ' Access URL     : http://localhost:%s\n' "${HOST_PORT}"
printf ' Status         : Running in background (--restart unless-stopped)\n'
printf '=======================================================\n'
