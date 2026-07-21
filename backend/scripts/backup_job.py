#!/usr/bin/env python3
"""
Automated backup script - run daily via cron or ECS scheduled task
"""
import asyncio
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.backup import run_full_backup

async def main():
    print("🔄 Starting scheduled backup...")
    result = await run_full_backup()
    print(f"✅ Backup completed: {result}")
    
if __name__ == "__main__":
    asyncio.run(main())
