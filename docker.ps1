# RAG Q&A Chatbot - Docker Management Script (PowerShell)

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    [Parameter(Position=1)]
    [string]$Service = ""
)

function Write-ColorMessage {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-ColorMessage "======================================" "Blue"
    Write-ColorMessage $Message "Blue"
    Write-ColorMessage "======================================" "Blue"
    Write-Host ""
}

function Test-Docker {
    try {
        docker info > $null 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-ColorMessage "Error: Docker is not running. Please start Docker Desktop and try again." "Red"
            exit 1
        }
    } catch {
        Write-ColorMessage "Error: Docker is not running. Please start Docker Desktop and try again." "Red"
        exit 1
    }
}

function Build-Containers {
    Write-Header "Building Docker Containers"
    Test-Docker
    docker-compose build
    if ($LASTEXITCODE -eq 0) {
        Write-ColorMessage "Build completed successfully!" "Green"
    }
}

function Start-Services {
    Write-Header "Starting Services"
    Test-Docker
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-ColorMessage "Services started successfully!" "Green"
        Write-Host ""
        Write-ColorMessage "Backend API: http://localhost:8000" "Blue"
        Write-ColorMessage "Frontend UI: http://localhost:3000" "Blue"
        Write-ColorMessage "API Docs: http://localhost:8000/docs" "Blue"
        Write-Host ""
    }
}

function Stop-Services {
    Write-Header "Stopping Services"
    Test-Docker
    docker-compose down
    if ($LASTEXITCODE -eq 0) {
        Write-ColorMessage "Services stopped successfully!" "Green"
    }
}

function Start-Ingestion {
    Write-Header "Running Document Ingestion"
    Test-Docker
    
    if (-not (Test-Path "./provided document")) {
        Write-ColorMessage "Warning: ./provided document directory not found." "Yellow"
        exit 1
    }
    
    Write-ColorMessage "Starting ingestion process..." "Blue"
    docker-compose run --rm backend python ingest.py
    if ($LASTEXITCODE -eq 0) {
        Write-ColorMessage "Ingestion completed successfully!" "Green"
    }
}

function Show-Logs {
    param([string]$ServiceName)
    Write-Header "Service Logs"
    Test-Docker
    if ([string]::IsNullOrEmpty($ServiceName)) {
        docker-compose logs -f
    } else {
        docker-compose logs -f $ServiceName
    }
}

function Show-Status {
    Write-Header "Service Status"
    Test-Docker
    docker-compose ps
}

function Clean-All {
    Write-Header "Cleaning Up"
    Test-Docker
    Write-ColorMessage "This will remove all containers, volumes, and the vector store. Are you sure? (y/N)" "Yellow"
    $response = Read-Host
    if ($response -match "^[yY](es)?$") {
        docker-compose down -v
        if ($LASTEXITCODE -eq 0) {
            Write-ColorMessage "Cleanup completed!" "Green"
        }
    } else {
        Write-ColorMessage "Cleanup cancelled." "Yellow"
    }
}

function Restart-Services {
    Write-Header "Restarting Services"
    Stop-Services
    Start-Services
}

function Show-Help {
    Write-Header "RAG Q&A Chatbot - Docker Management"
    Write-Host "Usage: .\docker.ps1 [command]"
    Write-Host ""
    Write-Host "Available commands:"
    Write-Host "  build       - Build Docker containers"
    Write-Host "  up          - Start all services"
    Write-Host "  down        - Stop all services"
    Write-Host "  restart     - Restart all services"
    Write-Host "  ingest      - Run document ingestion"
    Write-Host "  logs        - View service logs (optionally specify service: backend/frontend)"
    Write-Host "  status      - Show service status"
    Write-Host "  clean       - Remove all containers and volumes"
    Write-Host "  help        - Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\docker.ps1 build"
    Write-Host "  .\docker.ps1 up"
    Write-Host "  .\docker.ps1 ingest"
    Write-Host "  .\docker.ps1 logs backend"
    Write-Host ""
}

# Main script logic
switch ($Command.ToLower()) {
    "build" { Build-Containers }
    "up" { Start-Services }
    "down" { Stop-Services }
    "restart" { Restart-Services }
    "ingest" { Start-Ingestion }
    "logs" { Show-Logs -ServiceName $Service }
    "status" { Show-Status }
    "clean" { Clean-All }
    "help" { Show-Help }
    default {
        Write-ColorMessage "Unknown command: $Command" "Red"
        Write-Host ""
        Show-Help
        exit 1
    }
}
