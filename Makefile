.PHONY: help install run test clean docker-build docker-run

help:
	@echo "Office Assist API - Available Commands"
	@echo "======================================"
	@echo "make install      - Install dependencies"
	@echo "make run          - Start the development server"
	@echo "make test         - Run API tests"
	@echo "make clean        - Clean up cache files"
	@echo "make docker-build - Build Docker image"
	@echo "make docker-run   - Run with Docker Compose"
	@echo "make docker-stop  - Stop Docker containers"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

run:
	@echo "Starting FastAPI server..."
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "Running API tests..."
	python test_api.py

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

docker-build:
	@echo "Building Docker image..."
	docker build -t office-assist-api .

docker-run:
	@echo "Starting with Docker Compose..."
	docker-compose up

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down

dev:
	@echo "Starting development server with auto-reload..."
	uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
