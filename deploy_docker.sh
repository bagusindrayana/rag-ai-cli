#!/bin/bash
set -e

APP_NAME="contextapi"
WORKDIR=$(pwd)

print() { echo -e "[${APP_NAME}] $1"; }

check_requirements() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "docker is required. Install Docker and try again." >&2
    exit 1
  fi

  # Detect docker compose command: either `docker-compose` or `docker compose`
  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  else
    echo "docker compose is required. Install docker-compose (v1) or Docker Compose v2 and try again." >&2
    exit 1
  fi
  echo "Using compose command: $COMPOSE_CMD"
}

ensure_env() {
  if [ ! -f .env.prod ]; then
    read -p "Enter Google API Key: " GOOGLE_API_KEY
    cat > .env.prod <<EOF
GOOGLE_API_KEY=$GOOGLE_API_KEY
FAISS_INDEX_PATH=/app/faiss_db
FAISS_INDEX_PATH_MISTRAL=/app/faiss_db_mistral
API_HOST=0.0.0.0
API_PORT=8000
FLASK_ENV=production
EOF
    print "Created .env.prod"
  else
    print ".env.prod found, using existing file"
  fi
}

build_and_start() {
  print "Building Docker image..."
  $COMPOSE_CMD build --no-cache
  print "Starting containers..."
  $COMPOSE_CMD up -d
}

show_status() {
  print "Containers status:"
  docker-compose ps
  echo
  print "To see logs: docker-compose logs -f"
}

main() {
  check_requirements
  ensure_env
  build_and_start
  show_status
}

main
