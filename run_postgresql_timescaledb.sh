#!/bin/zsh
docker compose -f docker/docker-compose.yml down -v

sleep 3
docker compose -f docker/docker-compose.yml up  --build timescaledb &
