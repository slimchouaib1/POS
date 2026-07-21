# start_backend.ps1
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "     Starting POS Intelligent Backend    " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Check if Docker is running
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Start PostgreSQL container
Write-Host "[INFO] Starting PostgreSQL database container..." -ForegroundColor Yellow
docker-compose -f "$PSScriptRoot\..\docker-compose.yml" up -d db
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to start PostgreSQL container." -ForegroundColor Red
    exit 1
}
Write-Host "[INFO] PostgreSQL container is running." -ForegroundColor Green

# The database is automatically created and seeded by app.main's lifespan function.
Write-Host "[INFO] The PostgreSQL database will be automatically seeded upon startup if it does not exist." -ForegroundColor Yellow

# Check for requirements.txt to ensure we are in the right directory
if (-not (Test-Path "requirements.txt")) {
    Write-Host "Warning: requirements.txt not found. Are you in the backend directory?" -ForegroundColor Yellow
}

# Start the FastAPI server using Uvicorn
Write-Host "[INFO] Starting Uvicorn server on http://localhost:8000" -ForegroundColor Green
Write-Host "[INFO] Press Ctrl+C to stop the server." -ForegroundColor Gray
Write-Host "-----------------------------------------" -ForegroundColor Cyan

python -m uvicorn app.main:app --reload --port 8000
