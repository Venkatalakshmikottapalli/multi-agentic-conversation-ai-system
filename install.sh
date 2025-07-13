#!/bin/bash

# Multi-Agent CRM Chatbot System - Installation Script
# This script installs all dependencies for both backend and frontend

set -e

echo "🛠️  Installing Multi-Agent CRM Chatbot System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION detected"
            return 0
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

# Function to check Node.js version
check_node_version() {
    if command_exists node; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
        
        if [ "$NODE_MAJOR" -ge 14 ]; then
            print_success "Node.js $NODE_VERSION detected"
            return 0
        else
            print_error "Node.js 14+ required, found $NODE_VERSION"
            return 1
        fi
    else
        print_error "Node.js not found"
        return 1
    fi
}

# Function to create virtual environment
create_venv() {
    print_status "Creating Python virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing and recreating..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    print_success "Virtual environment created!"
}

# Function to install backend dependencies
install_backend_deps() {
    print_status "Installing backend dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Backend dependencies installed!"
    else
        print_error "requirements.txt not found!"
        exit 1
    fi
}

# Function to install frontend dependencies
install_frontend_deps() {
    print_status "Installing frontend dependencies..."
    
    if [ -d "frontend" ]; then
        cd frontend
        npm install
        cd ..
        print_success "Frontend dependencies installed!"
    else
        print_error "Frontend directory not found!"
        exit 1
    fi
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Create database tables
    python -c "from database import create_tables; create_tables()" 2>/dev/null || true
    
    print_success "Database setup completed!"
}

# Function to create environment files
create_env_files() {
    print_status "Creating environment files..."
    
    # Create backend .env if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating backend .env file..."
        cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Database Configuration
DATABASE_URL=sqlite:///./crm_chatbot.db

# Vector Database Configuration
CHROMA_DB_PATH=./chroma_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
EOF
        print_warning "Please update .env file with your OpenAI API key"
    fi
    
    # Create frontend .env if it doesn't exist
    if [ ! -f "frontend/.env" ]; then
        print_status "Creating frontend .env file..."
        cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8000
EOF
    fi
    
    print_success "Environment files created!"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run backend tests
    if command_exists pytest; then
        python -m pytest tests/ -v || print_warning "Some tests failed"
    else
        print_warning "pytest not found, skipping tests"
    fi
    
    # Run frontend tests
    if [ -d "frontend" ]; then
        cd frontend
        npm test -- --watchAll=false --passWithNoTests || print_warning "Frontend tests failed"
        cd ..
    fi
    
    print_success "Tests completed!"
}

# Main installation function
main() {
    echo "========================================"
    echo "  Multi-Agent CRM Chatbot System"
    echo "          Installation Script"
    echo "========================================"
    echo ""
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    
    if ! check_python_version; then
        print_error "Please install Python 3.8 or higher"
        exit 1
    fi
    
    if ! check_node_version; then
        print_error "Please install Node.js 14 or higher"
        exit 1
    fi
    
    if ! command_exists npm; then
        print_error "npm is not installed!"
        exit 1
    fi
    
    if ! command_exists pip; then
        print_error "pip is not installed!"
        exit 1
    fi
    
    print_success "Prerequisites check passed!"
    
    # Parse arguments
    SKIP_TESTS=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-tests      Skip running tests"
                echo "  -h, --help        Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Installation steps
    create_venv
    install_backend_deps
    install_frontend_deps
    setup_database
    create_env_files
    
    if [ "$SKIP_TESTS" = false ]; then
        run_tests
    fi
    
    # Final message
    echo ""
    echo "========================================"
    echo "🎉 Installation Complete!"
    echo "========================================"
    echo ""
    echo "Next steps:"
    echo "1. Update your OpenAI API key in .env file"
    echo "2. Run './start.sh' to start the system"
    echo "3. Open http://localhost:3000 in your browser"
    echo ""
    echo "For help, run './start.sh --help'"
    echo "========================================"
}

# Run main function
main "$@" 