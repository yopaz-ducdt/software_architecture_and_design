#!/bin/bash

# Trap Ctrl+C to kill all background processes automatically on exit
trap "echo -e '\nStopping all services...'; kill 0" EXIT

echo "=================================================="
echo "   Starting LearnMart Microservices Locally...   "
echo "=================================================="

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
else
    echo "Warning: venv directory not found. Using system Python."
fi

# Run database setup and migrations
echo "Running migration script..."
python setup_and_migrate.py
if [ $? -ne 0 ]; then
    echo "Migration failed. Please make sure MySQL is running."
    exit 1
fi

echo "Starting Backend Services..."

# Run each service in the background
python -m uvicorn auth_service.main:app --host 0.0.0.0 --port 8001 > /dev/null 2>&1 &
python -m uvicorn product_service.app:app --host 0.0.0.0 --port 8002 > /dev/null 2>&1 &
python -m uvicorn order_service.main:app --host 0.0.0.0 --port 8003 > /dev/null 2>&1 &
python -m uvicorn customer_service.main:app --host 0.0.0.0 --port 8004 > /dev/null 2>&1 &
python -m uvicorn staff_service.main:app --host 0.0.0.0 --port 8005 > /dev/null 2>&1 &
python -m uvicorn marketing_service.main:app --host 0.0.0.0 --port 8006 > /dev/null 2>&1 &
python -m uvicorn inventory_service.main:app --host 0.0.0.0 --port 8007 > /dev/null 2>&1 &
python -m uvicorn content_service.main:app --host 0.0.0.0 --port 8008 > /dev/null 2>&1 &
python -m uvicorn interaction_service.main:app --host 0.0.0.0 --port 8009 > /dev/null 2>&1 &
python -m uvicorn analytics_service.main:app --host 0.0.0.0 --port 8010 > /dev/null 2>&1 &
python -m uvicorn notification_service.main:app --host 0.0.0.0 --port 8011 > /dev/null 2>&1 &
python -m uvicorn ai_chat_service.main:app --host 0.0.0.0 --port 8012 > /dev/null 2>&1 &
python -m uvicorn behavior_service.main:app --host 0.0.0.0 --port 8013 > /dev/null 2>&1 &

# Wait a brief moment before starting Gateway & Frontend
sleep 2
echo "Starting API Gateway and Frontend Client..."
python -m uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
python frontend/server.py &

echo "=================================================="
echo "All services started successfully!"
echo "- Frontend Web: http://localhost:4000"
echo "- API Gateway:  http://localhost:8000"
echo "=================================================="
echo "Press Ctrl+C to stop all services."

# Wait for all background jobs to finish (keeps script running)
wait
