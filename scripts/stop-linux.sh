#!/bin/sh
set -e

docker stop pm-mvp >/dev/null 2>&1 || true
docker rm pm-mvp >/dev/null 2>&1 || true
