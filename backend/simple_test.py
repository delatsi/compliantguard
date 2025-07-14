#!/usr/bin/env python3
"""
Ultra-simple test to check if FastAPI works at all
"""

try:
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
    
    app = FastAPI()
    
    @app.get("/")
    def root():
        return {"message": "Simple test works"}
    
    @app.get("/test")
    def test():
        return {"status": "working"}
    
    print("✅ FastAPI app created successfully")
    
    import uvicorn
    print("✅ Uvicorn imported successfully")
    print("🚀 Starting simple test server on port 9000...")
    
    uvicorn.run(app, host="127.0.0.1", port=9000, reload=False)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()