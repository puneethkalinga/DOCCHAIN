#!/bin/bash
# startup.sh — DocChain Custom App Service Bootstrapper
echo "[DocChain Startup] Initializing environment..."

# 1. Install requirements to /tmp/packages (fast SSD storage)
echo "[DocChain Startup] Installing dependencies into local overlay storage..."
pip install --target=/tmp/packages -r requirements.txt --no-cache-dir

# 2. Add /tmp/packages to PYTHONPATH so python can load them
export PYTHONPATH="/tmp/packages:$PYTHONPATH"
export PYTHONPATH="/home/site/wwwroot:$PYTHONPATH"

# 3. Launch Gunicorn server
echo "[DocChain Startup] Launching backend server..."
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 backend.main:app
