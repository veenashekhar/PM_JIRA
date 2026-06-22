#!/bin/sh
set -e

if [ -f .env ]; then
	set -a
	. ./.env
	set +a
fi

docker rm -f pm-mvp >/dev/null 2>&1 || true

docker build -t pm-mvp .
docker run --name pm-mvp -p 8000:8000 -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" -d pm-mvp
