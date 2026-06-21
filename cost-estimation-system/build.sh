#!/bin/bash

# Build script for CI/CD pipeline

set -e

echo "Building Cost Estimation System..."
echo "=================================="

# Backend build
echo ""
echo "Building Backend..."
cd backend

# Install dependencies
pip install -r requirements.txt

# Run tests (if any)
echo "Running backend tests..."
# python -m pytest tests/

echo "✓ Backend build complete"

# Frontend build
echo ""
echo "Building Frontend..."
cd ../frontend

# Install dependencies
npm install

# Build production bundle
npm run build

echo "✓ Frontend build complete"

echo ""
echo "✓ Build successful!"
