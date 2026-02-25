#!/bin/bash
# Run this to start the Docker servers
> container_output.log # Clear log file
docker compose up --build --remove-orphans # 2>&1 | tee container_output.log
