#!/bin/bash
cd /home/site/wwwroot
python -m gunicorn app:app -k uvicorn.workers.UvicornWorker --bind=0.0.0.0 --timeout 600 