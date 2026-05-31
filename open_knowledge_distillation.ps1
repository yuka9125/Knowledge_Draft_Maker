$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$python = "python"
$port = if ($env:KNOWLEDGE_DISTILLATION_PORT) { $env:KNOWLEDGE_DISTILLATION_PORT } else { "8501" }
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "Starting Knowledge Distillation UI..."
Write-Host "URL: http://localhost:$port"
Write-Host ""
Write-Host "Demo import CSV:"
Write-Host "  benchmark\demo\knowledge_distillation_start_inquiries.csv"
Write-Host "Comparison source:"
Write-Host "  data\approved_knowledge.json"
Write-Host ""
Write-Host "If Azure OpenAI variables are missing, copy .env.example to .env and set real values."
Write-Host ""

Start-Process "http://localhost:$port"
& $python -m streamlit run knowledge_distillation/app.py --server.port $port --server.headless true
