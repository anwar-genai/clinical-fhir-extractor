#!/bin/bash
# Quick setup script for macOS/Linux
# Clinical FHIR Extractor Setup

echo "🏥 Clinical FHIR Extractor - Setup Script"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10 or higher."
    exit 1
fi
python_version=$(python3 --version)
echo "✓ Found: $python_version"

# Check for uv
echo ""
echo "Checking for uv package manager..."
if command -v uv &> /dev/null; then
    echo "✓ uv is installed"
    read -p "Use uv for installation? (Y/n): " use_uv
    use_uv=${use_uv:-Y}
    if [[ $use_uv =~ ^[Yy]$ ]]; then
        echo ""
        echo "Installing dependencies with uv..."
        uv sync
        if [ $? -eq 0 ]; then
            echo "✓ Dependencies installed successfully"
        else
            echo "❌ Failed to install dependencies"
            exit 1
        fi
    else
        use_uv="n"
    fi
else
    echo "⚠ uv not found. Using pip instead."
    use_uv="n"
fi

if [[ ! $use_uv =~ ^[Yy]$ ]]; then
    # Create virtual environment
    echo ""
    echo "Creating virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✓ Virtual environment created"
    else
        echo "⚠ Virtual environment already exists"
    fi

    # Activate and install
    echo ""
    echo "Installing dependencies with pip..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -e .
    if [ $? -eq 0 ]; then
        echo "✓ Dependencies installed successfully"
    else
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check for .env file
echo ""
echo "Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠ .env file not found"
    read -p "Create .env file from template? (Y/n): " create_env
    create_env=${create_env:-Y}
    if [[ $create_env =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "✓ Created .env file"
        echo ""
        echo "⚠ IMPORTANT: Edit .env and add your OPENAI_API_KEY"
    fi
else
    echo "✓ .env file exists"
fi

# Success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set your OPENAI_API_KEY in .env file"
echo "2. Run the application:"
if [[ $use_uv =~ ^[Yy]$ ]]; then
    echo "   uv run python main.py"
else
    echo "   source venv/bin/activate"
    echo "   python main.py"
fi
echo "3. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "🏥 Happy FHIR extraction!"

