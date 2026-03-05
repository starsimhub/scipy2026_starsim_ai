#!/bin/bash
# Run this to start the Docker servers
docker compose up --build --remove-orphans 2>&1 | tee container_output.log
