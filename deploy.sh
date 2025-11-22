#!/bin/bash

# Deployment script for Diia AI Application on AWS EC2
# This script helps you deploy and update your application

set -e  # Exit on any error

echo "========================================"
echo "Diia AI - Deployment Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    print_warning "backend/.env not found. Please create it before deploying."
    echo "Copy backend/.env.example to backend/.env and fill in your values."
    exit 1
fi

if [ ! -f "frontend/.env" ]; then
    print_warning "frontend/.env not found. Please create it before deploying."
    echo "Copy frontend/.env.example to frontend/.env and fill in your values."
    exit 1
fi

# Main deployment menu
echo "Select deployment action:"
echo "1) Fresh deployment (build and start)"
echo "2) Update deployment (pull latest code and rebuild)"
echo "3) Stop application"
echo "4) View logs"
echo "5) Check application status"
echo "6) Restart application"
echo "7) Clean up (remove containers and images)"
echo ""
read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        print_info "Starting fresh deployment..."
        docker compose -f docker-compose.prod.yaml up -d --build
        print_info "Deployment complete! Your application is now running."
        echo ""
        print_info "Access your application at:"
        echo "  - Frontend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'YOUR_SERVER_IP')"
        echo "  - Backend API: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'YOUR_SERVER_IP'):8000/docs"
        ;;
    2)
        print_info "Updating deployment..."
        if [ -d ".git" ]; then
            print_info "Pulling latest code from git..."
            git pull
        else
            print_warning "Not a git repository. Skipping git pull."
        fi
        print_info "Rebuilding and restarting containers..."
        docker compose -f docker-compose.prod.yaml up -d --build
        print_info "Update complete!"
        ;;
    3)
        print_info "Stopping application..."
        docker compose -f docker-compose.prod.yaml down
        print_info "Application stopped."
        ;;
    4)
        print_info "Showing logs (Ctrl+C to exit)..."
        docker compose -f docker-compose.prod.yaml logs -f
        ;;
    5)
        print_info "Application status:"
        docker compose -f docker-compose.prod.yaml ps
        echo ""
        print_info "Container health:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        ;;
    6)
        print_info "Restarting application..."
        docker compose -f docker-compose.prod.yaml restart
        print_info "Application restarted."
        ;;
    7)
        print_warning "This will remove all containers and images. Are you sure? (y/N)"
        read -p "> " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            print_info "Stopping and removing containers..."
            docker compose -f docker-compose.prod.yaml down
            print_info "Removing unused images..."
            docker image prune -a -f
            print_info "Cleanup complete!"
        else
            print_info "Cleanup cancelled."
        fi
        ;;
    *)
        print_error "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
print_info "Done!"
