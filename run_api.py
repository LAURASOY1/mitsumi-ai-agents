#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    print(" Starting Mitsumi AI Platform API...")
    print("http://localhost:8000")
    print(" Health: http://localhost:8000/health")
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
