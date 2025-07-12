#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting build process..."

# Set environment variables to avoid Rust compilation
export CARGO_NET_OFFLINE=true
export PIP_ONLY_BINARY=:all:
export DISABLE_AUTOBREW=1

# Upgrade pip and install build tools first
echo "🔧 Upgrading pip and installing build tools..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies with flags to avoid compilation
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt --only-binary=all --no-compile

# Install Node.js dependencies and build frontend
echo "🔧 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Create static directory for serving frontend
echo "📁 Setting up static files..."
mkdir -p static
cp -r frontend/build/* static/

# Create necessary directories for databases
echo "🗄️ Creating database directories..."
mkdir -p chroma_db
mkdir -p data

# Set permissions
echo "🔐 Setting permissions..."
chmod +x start.sh

echo "✅ Build completed successfully!" 