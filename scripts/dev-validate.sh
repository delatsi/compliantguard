#!/bin/bash
# Development validation script with ruff formatting
# Run this before committing changes

echo "🔍 Running development validation..."
echo ""

# Check if we're in the project root
if [ ! -f "template.yaml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

echo "🐍 Running backend validation..."
echo "  🔧 Using backend virtual environment..."

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Backend virtual environment not found. Please run 'python -m venv venv' in the backend directory"
    cd ..
    exit 1
fi

# Activate virtual environment and run ruff
source venv/bin/activate

echo "  🚀 Running ruff check (linting)..."
if ! ruff check .; then
    echo "❌ Backend linting failed"
    cd ..
    exit 1
fi

echo "  🎨 Running ruff format (formatting)..."
if ! ruff format .; then
    echo "❌ Backend formatting failed"
    cd ..
    exit 1
fi

echo "✅ Backend validation completed"
cd ..

echo ""
echo "⚛️  Running frontend validation..."

# Run frontend validation
if ! npm run validate; then
    echo "❌ Frontend validation failed"
    exit 1
fi

echo ""
echo "✅ All validation passed! Ready to commit 🎉"