#!/bin/bash
set -e

echo "Cleaning up previous package..."
rm -rf lambda_package
rm -rf python

echo "Creating package directory..."
mkdir -p lambda_package

echo "Creating virtual environment for Lambda-compatible dependencies..."
python3 -m venv venv_lambda
source venv_lambda/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install --platform manylinux2014_x86_64 --implementation cp --python-version 3.9 --only-binary=:all: -r requirements.txt -t lambda_package/

echo "Copying source code..."
cp chapter_generator.py lambda_package/
cp summary_generator.py lambda_package/
cp gemini_client.py lambda_package/
cp supabase_client.py lambda_package/

echo "Deactivating virtual environment..."
deactivate
rm -rf venv_lambda

echo "Listing package contents:"
ls -la lambda_package/

echo "Package creation completed."

# Clean up unnecessary files to reduce package size
cd lambda_package
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name "*.dist-info" -exec rm -rf {} +
find . -type d -name "*.egg-info" -exec rm -rf {} +
cd .. 