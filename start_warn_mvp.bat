@echo off
echo 🚀 Starting W.A.R.N MVP...

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running as Administrator - IP blocking features enabled
) else (
    echo ⚠️ Not running as Administrator - IP blocking features may be limited
    echo Please run as Administrator for full functionality
)

echo.
echo 📦 Installing Python dependencies...
cd server\backend
pip install -r requirements.txt

echo.
echo 🔧 Starting Flask Backend...
start "W.A.R.N Backend" python app.py

echo.
echo 📱 Installing Frontend dependencies...
cd ..\..\frontend
call npm install

echo.
echo 🎨 Starting React Frontend...
start "W.A.R.N Frontend" npm start

echo.
echo ✅ W.A.R.N MVP is starting!
echo 📊 Dashboard: http://localhost:3000
echo 🔌 API: http://localhost:5000
echo 🧪 Demo Login: http://localhost:3000/instagram_login.html
echo.
echo Press any key to exit...
pause