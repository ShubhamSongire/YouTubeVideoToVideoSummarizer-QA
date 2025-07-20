#!/bin/bash

# YouTube Video QA - Development Environment Manager
# Usage: ./dev.sh [start|stop|restart|logs|build|clean]

set -e

COMPOSE_FILE="docker-compose.dev.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} YouTube Video QA - Development Setup${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_error ".env file not found!"
        print_warning "Please create a .env file with your API keys."
        print_warning "You can copy from .env.example if available."
        exit 1
    fi
}

# Check which docker compose command is available
get_docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        print_error "Neither 'docker-compose' nor 'docker compose' is available!"
        print_error "Please install Docker and Docker Compose first."
        print_warning "See DOCKER_SETUP.md for installation instructions."
        exit 1
    fi
}

# Function to start development environment
start_dev() {
    print_header
    print_status "Starting YouTube Video QA development environment..."
    
    check_env_file
    
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    print_status "Using: $DOCKER_COMPOSE_CMD"
    
    # Build and start containers
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up --build -d
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if services are running
    if $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE ps | grep -q "Up"; then
        print_status "✅ Services are running!"
        echo ""
        print_status "🚀 Application URLs:"
        echo "   • Backend API: http://localhost:8000"
        echo "   • API Documentation: http://localhost:8000/docs"
        echo "   • Frontend (Streamlit): http://localhost:8502"
        echo ""
        print_status "📝 To view logs: ./dev.sh logs"
        print_status "🛑 To stop: ./dev.sh stop"
    else
        print_error "❌ Failed to start services"
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs
    fi
}

# Function to stop development environment
stop_dev() {
    print_status "Stopping development environment..."
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down
    print_status "✅ Environment stopped"
}

# Function to restart development environment
restart_dev() {
    print_status "Restarting development environment..."
    stop_dev
    start_dev
}

# Function to show logs
show_logs() {
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    if [ "$2" = "backend" ]; then
        print_status "Showing backend logs (Ctrl+C to exit)..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs -f backend
    elif [ "$2" = "frontend" ]; then
        print_status "Showing frontend logs (Ctrl+C to exit)..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs -f frontend
    else
        print_status "Showing all logs (Ctrl+C to exit)..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs -f
    fi
}

# Function to rebuild containers
rebuild_dev() {
    print_status "Rebuilding development environment..."
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE build --no-cache
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d
    print_status "✅ Environment rebuilt and started"
}

# Function to clean up
clean_dev() {
    print_warning "This will remove all containers, images, and volumes"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up development environment..."
        DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down -v --rmi all
        docker system prune -f
        print_status "✅ Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to show help
show_help() {
    print_header
    echo "Usage: ./dev.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the development environment"
    echo "  stop      Stop the development environment"
    echo "  restart   Restart the development environment"
    echo "  logs      Show logs (optional: backend/frontend)"
    echo "  build     Rebuild containers"
    echo "  clean     Clean up everything (containers, images, volumes)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./dev.sh start"
    echo "  ./dev.sh logs backend"
    echo "  ./dev.sh restart"
}

# Main command handler
case "${1:-help}" in
    start)
        start_dev
        ;;
    stop)
        stop_dev
        ;;
    restart)
        restart_dev
        ;;
    logs)
        show_logs "$@"
        ;;
    build)
        rebuild_dev
        ;;
    clean)
        clean_dev
        ;;
    help|*)
        show_help
        ;;
esac
