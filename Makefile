.PHONY: help up down restart logs clean neo4j app

# Default target - show available commands
help:
	@echo "Knowledge Graph Generator - Available Commands:"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up       - Start all services (Neo4j + Streamlit)"
	@echo "  make down     - Stop all services"
	@echo "  make restart  - Restart all services"
	@echo "  make logs     - Show service logs"
	@echo "  make clean    - Remove containers and images"
	@echo ""
	@echo "Quick Access:"
	@echo "  make neo4j    - Open Neo4j browser"
	@echo "  make app      - Open Streamlit app"
	@echo ""

# Start infrastructure
up:
	@echo "🚀 Starting Knowledge Graph Generator infrastructure..."
	docker-compose up --build -d
	@echo "✅ Services started in background. Use 'make logs' to view logs."
	@echo "🌐 Streamlit app: http://localhost:8501"
	@echo "🌐 Neo4j browser: http://localhost:7474"

# Stop infrastructure
down:
	@echo "🛑 Stopping Knowledge Graph Generator infrastructure..."
	docker-compose down

# Restart infrastructure
restart: down up

# Show logs
logs:
	@echo "📋 Showing service logs..."
	docker-compose logs -f

# Clean up containers and images
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down --rmi all --volumes --remove-orphans

# Quick links (open in default browser)
neo4j:
	@echo "🌐 Opening Neo4j Browser..."
	@open http://localhost:7474 || xdg-open http://localhost:7474 || echo "Please open http://localhost:7474 manually"

app:
	@echo "🌐 Opening Streamlit App..."
	@open http://localhost:8501 || xdg-open http://localhost:8501 || echo "Please open http://localhost:8501 manually"