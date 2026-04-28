# Start both backend and frontend servers

# Start Backend
Write-Host "Starting backend server on port 8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python main.py"

# Wait a moment for backend to start
Start-Sleep -Seconds 2

# Start Frontend
Write-Host "Starting frontend server on port 5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`n✓ Both servers starting!`nFrontend: http://localhost:5173`nBackend: http://localhost:8000" -ForegroundColor Cyan
