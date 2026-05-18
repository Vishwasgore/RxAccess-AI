#!/bin/bash

# RxAccess AI - Automated Setup Script
# This script sets up the entire RxAccess AI system

set -e  # Exit on error

echo "🚀 RxAccess AI - Automated Setup"
echo "=================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if Python 3.10+
required_version="3.10"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "   ❌ Error: Python 3.10 or higher required"
    exit 1
fi
echo "   ✅ Python version OK"

# Check Tesseract
echo ""
echo "📋 Checking Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n1)
    echo "   Found: $tesseract_version"
    echo "   ✅ Tesseract OK"
else
    echo "   ⚠️  Tesseract not found"
    echo "   Please install Tesseract OCR:"
    echo "   - macOS: brew install tesseract"
    echo "   - Linux: sudo apt-get install tesseract-ocr"
    echo "   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists"
else
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "   ✅ Pip upgraded"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt > /dev/null 2>&1
echo "   ✅ Dependencies installed"

# Create .env file
echo ""
echo "⚙️  Setting up environment..."
if [ -f ".env" ]; then
    echo "   .env file already exists"
else
    cp .env.example .env
    echo "   ✅ Created .env file"
fi

# Initialize system
echo ""
echo "🔧 Initializing system..."
python scripts/init_system.py
echo "   ✅ System initialized"

# Train model
echo ""
echo "🤖 Training adherence model..."
python scripts/train_adherence_model.py
echo "   ✅ Model trained"

# Generate synthetic data
echo ""
echo "📄 Generating synthetic prescriptions..."
python scripts/generate_synthetic_data.py
echo "   ✅ Synthetic data generated"

# Final message
echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "🎉 RxAccess AI is ready to use!"
echo ""
echo "To start the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: streamlit run streamlit_app/app.py"
echo "  3. Open browser at: http://localhost:8501"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
echo ""
echo "📚 Documentation:"
echo "  - README.md - Full documentation"
echo "  - QUICKSTART.md - Quick start guide"
echo "  - PROJECT_SUMMARY.md - Project overview"
echo ""
echo "⚠️  Remember: This is a prototype for demonstration only!"
echo ""
