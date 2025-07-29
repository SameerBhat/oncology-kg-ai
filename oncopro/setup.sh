#!/bin/bash

# OncroPro Embedding System Setup Script for Ubuntu
# This script sets up the complete environment for the OncroPro embedding system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Update system packages
log_info "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install essential build tools and dependencies
log_info "Installing essential build tools and system dependencies..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    unzip \
    zip \
    htop \
    tree

# Install Node.js (using NodeSource repository for latest LTS)
log_info "Installing Node.js..."
if ! command_exists node; then
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
    log_success "Node.js installed successfully"
else
    log_warning "Node.js already installed: $(node --version)"
fi

# Install Python 3.11+ (if not available, use deadsnakes PPA)
log_info "Installing Python 3.11..."
if ! command_exists python3.11; then
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils
    log_success "Python 3.11 installed successfully"
else
    log_warning "Python 3.11 already installed: $(python3.11 --version)"
fi

# Install pip for Python 3.11
log_info "Installing pip for Python 3.11..."
if ! python3.11 -m pip --version >/dev/null 2>&1; then
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
    log_success "pip installed successfully"
else
    log_warning "pip already installed for Python 3.11"
fi

# # Install MongoDB
# log_info "Installing MongoDB..."
# if ! command_exists mongod; then
#     # Import MongoDB public GPG key
#     wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
    
#     # Create MongoDB list file
#     echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
#     # Update package database and install MongoDB
#     sudo apt-get update
#     sudo apt-get install -y mongodb-org
    
#     # Start and enable MongoDB service
#     sudo systemctl start mongod
#     sudo systemctl enable mongod
    
#     log_success "MongoDB installed and started successfully"
# else
#     log_warning "MongoDB already installed"
#     # Ensure MongoDB is running
#     sudo systemctl start mongod || true
# fi

# # Verify MongoDB is running
# if sudo systemctl is-active --quiet mongod; then
#     log_success "MongoDB is running"
# else
#     log_error "MongoDB failed to start"
#     exit 1
# fi

# Set up project directory
PROJECT_DIR="/home/ubuntu/oncopro"
log_info "Setting up project directory at $PROJECT_DIR..."

# Create project directory if it doesn't exist
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# Navigate to project directory
cd $PROJECT_DIR

# Clone or copy the project (assuming the script is run from the project directory)
log_info "Setting up project files..."
if [ -f "/tmp/oncopro-project.tar.gz" ]; then
    # If project is provided as a tar file
    tar -xzf /tmp/oncopro-project.tar.gz -C $PROJECT_DIR --strip-components=1
elif [ -d "/tmp/oncopro" ]; then
    # If project is provided as a directory
    cp -r /tmp/oncopro/* $PROJECT_DIR/
else
    log_warning "Project files not found in /tmp. Please manually copy your project files to $PROJECT_DIR"
fi

# Create Python virtual environment
log_info "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip in virtual environment
log_info "Upgrading pip in virtual environment..."
pip install --upgrade pip setuptools wheel

# Step 1: Install PyTorch first
log_info "Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu120

# Install Python dependencies
log_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    log_success "Python dependencies installed successfully"
else
    log_error "requirements.txt not found. Please ensure it's in the project directory."
fi

# Install Node.js dependencies
log_info "Installing Node.js dependencies..."
if [ -f "package.json" ]; then
    npm install
    log_success "Node.js dependencies installed successfully"
else
    log_error "package.json not found. Please ensure it's in the project directory."
fi

# Set up environment configuration
log_info "Setting up environment configuration..."
if [ -f ".env.example" ]; then
    cp .env.example .env
    log_success "Environment configuration created from .env.example"
    log_info "Please edit .env file to configure your specific settings"
else
    log_warning ".env.example not found. Creating basic .env file..."
    cat > .env << EOF
# Environment variables for embedding configuration

# Choose your embedding model: jina4, qwen3, openai
EMBEDDING_MODEL=jina4

# MongoDB configuration
DATABASE_URI=mongodb://localhost:27017

# Optional configuration
# EMBEDDING_BATCH_SIZE=32
# EMBEDDING_DEVICE=auto
EOF
    log_success "Basic .env file created"
fi

# Create data directory if it doesn't exist
log_info "Creating data directory..."
mkdir -p data
sudo chown $USER:$USER data

# Create logs directory
log_info "Creating logs directory..."
mkdir -p logs
sudo chown $USER:$USER logs

# Set up system service (optional)
log_info "Setting up systemd service..."
sudo tee /etc/systemd/system/oncopro.service > /dev/null << EOF
[Unit]
Description=OncroPro Embedding System
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$PROJECT_DIR/venv/bin/python generate_db_embeddings.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
log_success "Systemd service created (not started automatically)"

# Install useful additional tools
log_info "Installing additional useful tools..."
sudo apt-get install -y htop tree jq curl

# Set up bash aliases for convenience
log_info "Setting up bash aliases..."
cat >> ~/.bashrc << 'EOF'

# OncroPro aliases
alias oncopro-activate='cd /home/ubuntu/oncopro && source venv/bin/activate'
alias oncopro-logs='tail -f /home/ubuntu/oncopro/logs/*.log'
alias oncopro-status='sudo systemctl status oncopro'
alias oncopro-start='sudo systemctl start oncopro'
alias oncopro-stop='sudo systemctl stop oncopro'
alias oncopro-restart='sudo systemctl restart oncopro'
EOF

# Create a convenience script
log_info "Creating convenience management script..."
cat > $PROJECT_DIR/manage.sh << 'EOF'
#!/bin/bash

PROJECT_DIR="/home/ubuntu/oncopro"
cd $PROJECT_DIR

case "$1" in
    start)
        echo "Starting OncroPro embedding generation..."
        source venv/bin/activate
        python generate_db_embeddings.py
        ;;
    convert)
        echo "Converting mindmap to database..."
        npm run convert-mm-db
        ;;
    test)
        echo "Running tests..."
        source venv/bin/activate
        python -m pytest tests/
        ;;
    status)
        echo "Checking MongoDB status..."
        sudo systemctl status mongod --no-pager -l
        echo "Checking project files..."
        ls -la $PROJECT_DIR
        ;;
    logs)
        echo "Showing recent logs..."
        journalctl -u oncopro --no-pager -l -n 50
        ;;
    shell)
        echo "Activating virtual environment..."
        bash --rcfile <(echo '. ~/.bashrc; cd '$PROJECT_DIR'; source venv/bin/activate; echo "OncroPro environment activated"')
        ;;
    *)
        echo "Usage: $0 {start|convert|test|status|logs|shell}"
        echo "  start   - Run embedding generation"
        echo "  convert - Convert mindmap to database"
        echo "  test    - Run test suite"
        echo "  status  - Check system status"
        echo "  logs    - Show recent logs"
        echo "  shell   - Open shell with activated environment"
        exit 1
        ;;
esac
EOF

chmod +x $PROJECT_DIR/manage.sh
sudo ln -sf $PROJECT_DIR/manage.sh /usr/local/bin/oncopro

# Final verification
log_info "Running final verification..."

# Check Python environment
source venv/bin/activate
if python -c "import torch, transformers, sentence_transformers, pymongo; print('All major dependencies imported successfully')" 2>/dev/null; then
    log_success "Python environment verified successfully"
else
    log_error "Python environment verification failed"
fi

# Check Node.js environment
if npm list >/dev/null 2>&1; then
    log_success "Node.js environment verified successfully"
else
    log_warning "Node.js environment verification failed"
fi

# Check MongoDB connection
if mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    log_success "MongoDB connection verified successfully"
else
    log_error "MongoDB connection verification failed"
fi

# Display final information
log_success "OncroPro Embedding System setup completed!"
echo ""
echo -e "${BLUE}📁 Project Directory:${NC} $PROJECT_DIR"
echo -e "${BLUE}🔧 Management Command:${NC} oncopro [start|convert|test|status|logs|shell]"
echo -e "${BLUE}📝 Environment Config:${NC} $PROJECT_DIR/.env"
echo -e "${BLUE}📊 MongoDB URI:${NC} mongodb://localhost:27017"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Copy your mindmap (.mm) and category (.csv) files to $PROJECT_DIR/data/"
echo "2. Edit $PROJECT_DIR/.env to configure your embedding model and settings"
echo "3. Run: oncopro convert    # Convert mindmap to database"
echo "4. Run: oncopro start      # Generate embeddings"
echo "5. Use: oncopro shell      # Open development environment"
echo ""
echo -e "${GREEN}Setup completed successfully! 🎉${NC}"

# Source the new bashrc to make aliases available
source ~/.bashrc
