#!/bin/bash
# Moves the logs to the archive folder so they will no longer be read by the analysis

cd -- "$(dirname -- "${BASH_SOURCE[0]}")" # Current folder
mv -v ./2026-*.eval ../archived_logs/
