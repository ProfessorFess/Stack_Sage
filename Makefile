.PHONY: install dev clean backend frontend test help

help:
	@echo "Stack Sage - Development Commands"
	@echo ""
	@echo "make install   - Install all dependencies (backend + frontend)"
	@echo "make dev       - Run both backend and frontend in parallel"
	@echo "make backend   - Run only the backend server"
	@echo "make frontend  - Run only the frontend dev server"
	@echo "make clean     - Remove cache files and build artifacts"
	@echo "make test      - Run tests (when available)"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Installation complete!"

dev:
	@echo "Starting Stack Sage in development mode..."
	@./dev.sh

backend:
	@echo "Starting backend server..."
	@if [ -d "backend/venv" ]; then \
		. backend/venv/bin/activate && python3 -m uvicorn backend.api.server:app --reload --port 8000; \
	else \
		python3 -m uvicorn backend.api.server:app --reload --port 8000; \
	fi

frontend:
	@echo "Starting frontend dev server..."
	cd frontend && npm run dev

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

test:
	@echo "Running tests..."
	cd backend && python -m pytest tests/ -v

