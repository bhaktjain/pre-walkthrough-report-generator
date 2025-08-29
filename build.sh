#!/usr/bin/env bash
# Render build script

set -o errexit  # exit on error

echo "Starting build process..."

# Upgrade pip
pip install --upgrade pip

# Install main requirements
echo "Installing main requirements..."
pip install -r render_requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p data
mkdir -p templates

# Copy template file if it exists
if [ -f "pre_walkthrough_generator/Pre-walkthrough_template.docx" ]; then
    echo "Copying template file..."
    cp pre_walkthrough_generator/Pre-walkthrough_template.docx templates/
fi

echo "Build completed successfully!"