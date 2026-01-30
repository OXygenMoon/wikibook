#!/bin/bash

PIDFILE="/tmp/wikibook.pid"
CDIR="/root/projects/wikibook"
PORT=5009

cd $CDIR

# Activate virtual environment
source venv/bin/activate

# Stop the service if running
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p $PID > /dev/null; then
        echo "Stopping existing instance (PID: $PID)..."
        kill $PID
        sleep 2
    else
        rm "$PIDFILE"
    fi
fi

echo "Starting Wikibook service on port $PORT..."
gunicorn -c gunicorn.conf.py app:app

if [ $? -eq 0 ]; then
    sleep 2
    if [ -f "$PIDFILE" ]; then
        NEW_PID=$(cat "$PIDFILE")
        if ps -p $NEW_PID > /dev/null; then
            echo "Service started successfully! PID: $NEW_PID"
            echo "Listening on port $PORT"
        else
            echo "Service started but process died. Check logs."
        fi
    else
        echo "Service failed to start."
    fi
else
    echo "Failed to start gunicorn."
fi