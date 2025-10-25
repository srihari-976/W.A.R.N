@echo off
echo 🚀 Starting W.A.R.N Integrated MVP (Backend + Frontend)...

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running as Administrator - Full security features enabled
) else (
    echo ⚠️ Not running as Administrator - Some security features may be limited
)

echo.
echo 📦 Installing Backend Dependencies...
cd server\backend
pip install -r requirements.txt

echo.
echo 🔧 Starting Flask Backend...
start "W.A.R.N Backend" cmd /k "python app.py"

echo.
echo ⏳ Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo.
echo 📱 Installing Frontend Dependencies...
cd ..\..\frontend
call npm install

echo.
echo 🎨 Starting React Frontend...
start "W.A.R.N Frontend" cmd /k "npm start"

echo.
echo ⏳ Waiting for frontend to start...
timeout /t 10 /nobreak > nul

echo.
echo 🧪 Running Integration Test...
cd ..
python integration_test.py

echo.
echo ✅ W.A.R.N Integrated MVP is running!
echo.
echo 📊 Frontend Dashboard: http://localhost:3000
echo 🔌 Backend API: http://localhost:5000
echo 🧪 Instagram Demo: http://localhost:3000/instagram_login.html
echo 🛡️ Security Dashboard: http://localhost:3000/security
echo.
echo 🔑 Login Credentials:
echo   Username: any username
echo   Password: demo123
echo.
echo Press any key to exit...
pause