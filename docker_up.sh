#!/bin/bash
# Run this to start the Docker servers
#   --log    Save output to container_output.log (disables terminal color)

if [[ "$1" == "--log" ]]; then
    docker compose up --build --remove-orphans 2>&1 | tee container_output.log
else
    docker compose up --build --remove-orphans
fi
