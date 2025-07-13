# 🚀 Quick Start Guide

## ✅ Fixed TailwindCSS Issue

The PostCSS configuration has been updated to work with the latest TailwindCSS version.

## 🏃‍♂️ Start Development Environment

### Option 1: Automatic Setup (Recommended)
```bash
# From project root
./scripts/start-dev.sh
```

### Option 2: Manual Setup

**1. Backend Setup:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python dev.py
```

**2. Frontend Setup (in new terminal):**
```bash
cd frontend
npm install
npm run dev
```

## 🌐 Access URLs

- **Frontend**: http://localhost:5174 (may vary if port is taken)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🧪 Test the Application

1. **Backend Health Check:**
```bash
curl http://localhost:8000/health
```

2. **Frontend:**
   - Visit the frontend URL shown in terminal
   - Try login with any email/password (mock auth)
   - Explore the dashboard with sample data

## 🔧 Development Features

- ✅ **Hot Reload**: Both frontend and backend auto-reload on changes
- ✅ **Mock Data**: Sample compliance scans and violations
- ✅ **CORS Enabled**: Frontend can call backend APIs
- ✅ **API Documentation**: Interactive docs at `/docs`

## 🚨 Common Issues & Fixes

### TailwindCSS PostCSS Error (FIXED)
The error was: `It looks like you're trying to use 'tailwindcss' directly as a PostCSS plugin`

**Fix Applied:**
- Installed `@tailwindcss/postcss`
- Updated `postcss.config.js` to use the correct plugin

### Port Conflicts
If ports are in use:
- Frontend will automatically use next available port (5174, 5175, etc.)
- Backend can be changed by editing `dev.py` (line with `port=8000`)

### Python Dependencies
Make sure you're in the virtual environment:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Node Dependencies
```bash
cd frontend
npm install
```

## 📝 What's Working Now

✅ **Frontend**: React + Vite + TailwindCSS  
✅ **Backend**: FastAPI with mock endpoints  
✅ **Authentication**: Mock login/register  
✅ **Dashboard**: Sample compliance data  
✅ **Scanning**: Mock scan interface  
✅ **API Documentation**: Auto-generated docs  

## 🎯 Ready for Development

The application is now fully set up for local development. You can:

1. **Modify the UI**: Edit files in `frontend/src/`
2. **Add API endpoints**: Edit `backend/dev.py` or `backend/main.py`
3. **Test features**: Use the mock data to develop new functionality
4. **Deploy later**: Use SAM CLI for AWS deployment

Happy coding! 🎉