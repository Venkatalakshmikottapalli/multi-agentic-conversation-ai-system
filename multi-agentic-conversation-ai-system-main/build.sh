#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

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