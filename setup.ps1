# Quick setup script for Windows (PowerShell)
# Clinical FHIR Extractor Setup

Write-Host "🏥 Clinical FHIR Extractor - Setup Script" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.10 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green

# Check for uv
Write-Host "`nChecking for uv package manager..." -ForegroundColor Yellow
$uvInstalled = Get-Command uv -ErrorAction SilentlyContinue
if ($uvInstalled) {
    Write-Host "✓ uv is installed" -ForegroundColor Green
    $useUv = Read-Host "`nUse uv for installation? (Y/n)"
    if ($useUv -eq "" -or $useUv -eq "Y" -or $useUv -eq "y") {
        Write-Host "`nInstalling dependencies with uv..." -ForegroundColor Yellow
        uv sync
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
            exit 1
        }
    } else {
        $useUv = $false
    }
} else {
    Write-Host "⚠ uv not found. Using pip instead." -ForegroundColor Yellow
    $useUv = $false
}

if (-not $useUv) {
    # Create virtual environment
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    if (-not (Test-Path "venv")) {
        python -m venv venv
        Write-Host "✓ Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "⚠ Virtual environment already exists" -ForegroundColor Yellow
    }

    # Activate and install
    Write-Host "`nInstalling dependencies with pip..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install -e .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Check for .env file
Write-Host "`nChecking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠ .env file not found" -ForegroundColor Yellow
    $createEnv = Read-Host "Create .env file from template? (Y/n)"
    if ($createEnv -eq "" -or $createEnv -eq "Y" -or $createEnv -eq "y") {
        Copy-Item .env.example .env
        Write-Host "✓ Created .env file" -ForegroundColor Green
        Write-Host "`n⚠ IMPORTANT: Edit .env and add your OPENAI_API_KEY" -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ .env file exists" -ForegroundColor Green
}

# Success message
Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Set your OPENAI_API_KEY in .env file" -ForegroundColor White
Write-Host "2. Run the application:" -ForegroundColor White
if ($useUv) {
    Write-Host "   uv run python main.py" -ForegroundColor Yellow
} else {
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "   python main.py" -ForegroundColor Yellow
}
Write-Host "3. Visit http://localhost:8000/docs for API documentation" -ForegroundColor White
Write-Host "`n🏥 Happy FHIR extraction!" -ForegroundColor Cyan

