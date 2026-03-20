#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/..")

echo "Starting frontend..."
cd "$PROJECT_ROOT/frontend" || exit
npm install
npm run dev