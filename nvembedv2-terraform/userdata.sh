#!/bin/bash

# Log everything to a file for debugging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "Starting user data script at $(date)"

# Update system
apt-get update -y
apt-get upgrade -y

# Install essential packages
apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    tree \
    vim \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# # Install Docker
# curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
# echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
# apt-get update -y
# apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# # Add ubuntu user to docker group
# usermod -aG docker ubuntu

# # Install NVIDIA Docker (for GPU support)
# distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
#     && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
#     && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
#        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
#        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# apt-get update -y
# apt-get install -y nvidia-container-toolkit
# systemctl restart docker

# # Install Python 3.11 and pip
# add-apt-repository ppa:deadsnakes/ppa -y
# apt-get update -y
# apt-get install -y python3.11 python3.11-pip python3.11-venv python3.11-dev

# # Make python3.11 the default python3
# update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
# update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.11 1

# # Install Node.js and npm
# curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
# apt-get install -y nodejs

# # Install pnpm
# npm install -g pnpm

# # Install AWS CLI
# curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
# unzip awscliv2.zip
# ./aws/install
# rm -rf aws awscliv2.zip

# # Create working directory
# mkdir -p /home/ubuntu/workspace
# chown ubuntu:ubuntu /home/ubuntu/workspace

# # Clone your repository (optional - uncomment and modify as needed)
# # cd /home/ubuntu/workspace
# # sudo -u ubuntu git clone https://github.com/SameerBhat/rag-testing-oncopro.git
# # chown -R ubuntu:ubuntu /home/ubuntu/workspace/

# # Install common Python packages for ML/AI
# sudo -u ubuntu python3 -m pip install --user \
#     torch \
#     transformers \
#     sentence-transformers \
#     numpy \
#     pandas \
#     scikit-learn \
#     matplotlib \
#     jupyter \
#     notebook \
#     pymongo \
#     requests \
#     fastapi \
#     uvicorn

# # Install MongoDB
# wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add -
# echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
# apt-get update -y
# apt-get install -y mongodb-org

# # Configure MongoDB
# systemctl start mongod
# systemctl enable mongod

# # Set up environment variables
# cat >> /home/ubuntu/.bashrc << 'EOF'
# export PATH="/home/ubuntu/.local/bin:$PATH"
# export PYTHONPATH="/home/ubuntu/workspace:$PYTHONPATH"
# EOF

# # Create a setup completion marker
# touch /home/ubuntu/setup-complete.txt
# echo "Setup completed at $(date)" > /home/ubuntu/setup-complete.txt
# chown ubuntu:ubuntu /home/ubuntu/setup-complete.txt

# # Start any services you need
# systemctl enable docker
# systemctl start docker

echo "User data script completed at $(date)"