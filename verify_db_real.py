import asyncio
import sys
import os

# Add backend to path so we can import src
sys.path.append(os.path.abspath("backend"))

from src.database.database import AsyncSessionLocal, engine
from sqlalchemy import text

async def verify_db_connection():
    print("1. Testing Database Connection...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"   ✅ Connection successful! Result: {result.scalar()}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return

    print("\n2. Testing Session Creation...")
    try:
        async with AsyncSessionLocal() as session:
            print(f"   ✅ Session created successfully: {session}")
            # Try a simple query within session
            result = await session.execute(text("SELECT 1"))
            print(f"   ✅ Session query result: {result.scalar()}")
    except Exception as e:
        print(f"   ❌ Session creation failed: {e}")
        return

    print("\n✅ VERIFICATION COMPLETE: The database module is real and working.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_db_connection())
