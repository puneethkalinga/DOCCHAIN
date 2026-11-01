#!/bin/bash
# deploy.sh — Custom Kudu deployment script
echo "[DocChain Deploy] Starting custom rsync copy..."
rsync -av --delete --exclude='.git' --exclude='.venv' /tmp/zipdeploy/extracted/ /home/site/wwwroot/
echo "[DocChain Deploy] Copy complete!"
