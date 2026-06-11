@echo off
echo Starting BookStore Microservices...

SET BASE=d:\This Semester\Analysis and Design\assigments\assignment_5
SET PYTHON=python

start "auth_service :8001" /MIN cmd /k "cd /d "%BASE%\auth_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8001 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "book_service :8002" /MIN cmd /k "cd /d "%BASE%\book_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8002 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "order_service :8003" /MIN cmd /k "cd /d "%BASE%\order_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8003 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "customer_service :8004" /MIN cmd /k "cd /d "%BASE%\customer_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8004 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "staff_service :8005" /MIN cmd /k "cd /d "%BASE%\staff_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8005 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "marketing_service :8006" /MIN cmd /k "cd /d "%BASE%\marketing_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8006 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "inventory_service :8007" /MIN cmd /k "cd /d "%BASE%\inventory_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8007 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "content_service :8008" /MIN cmd /k "cd /d "%BASE%\content_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8008 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "interaction_service :8009" /MIN cmd /k "cd /d "%BASE%\interaction_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8009 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "analytics_service :8010" /MIN cmd /k "cd /d "%BASE%\analytics_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8010 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "notification_service :8011" /MIN cmd /k "cd /d "%BASE%\notification_service" & %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8011 2>&1 & pause"
timeout /t 1 /nobreak > nul
start "frontend :3000" /MIN cmd /k "cd /d "%BASE%\frontend" & %PYTHON% server.py & pause"

echo.
echo All 11 services + frontend launched in separate windows.
echo.
echo Swagger docs (API testing):
echo   Auth:         http://localhost:8001/docs
echo   Book:         http://localhost:8002/docs
echo   Order:        http://localhost:8003/docs
echo   Customer:     http://localhost:8004/docs
echo   Staff:        http://localhost:8005/docs
echo   Marketing:    http://localhost:8006/docs
echo   Inventory:    http://localhost:8007/docs
echo   Content:      http://localhost:8008/docs
echo   Interaction:  http://localhost:8009/docs
echo   Analytics:    http://localhost:8010/docs
echo   Notification: http://localhost:8011/docs
echo.
echo Frontend UI:  http://localhost:3000
echo.
echo Login accounts:
echo   Customer: demo@bookstore.vn / demo123
echo   Staff:    admin / admin123
echo.
pause
