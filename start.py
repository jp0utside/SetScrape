#!/usr/bin/env python3
"""
Music Player System - Local Development Startup Script
Starts all 4 services: Main API, Search, Download, and Scraping
"""

import os
import sys
import asyncio
import subprocess
import time
import signal
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

def create_directories():
    """Create necessary directories"""
    directories = ["data", "downloads", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

async def init_database():
    """Initialize the SQLite database"""
    try:
        from shared.database import init_db
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

def start_service(name, module, port, description):
    """Start a FastAPI service"""
    cmd = [
        sys.executable, "-m", "uvicorn", 
        f"backend.{module}.main:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--reload",
        "--log-level", "info",
        "--env-file", ".env"
    ]
    
    # Set PYTHONPATH to include the current directory
    env = os.environ.copy()
    env['PYTHONPATH'] = os.getcwd() + os.pathsep + env.get('PYTHONPATH', '')
    
    print(f"🚀 Starting {name} on port {port}...")
    print(f"   Description: {description}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        env=env
    )
    
    return process

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    """Main startup function"""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🎵 Music Player System - Starting 4-Service Architecture")
    print("=" * 60)
    
    # Create directories
    create_directories()
    
    # Initialize database
    print("\n📊 Initializing database...")
    asyncio.run(init_database())
    
    # Note: Background task manager removed for real-time browsing architecture
    print("\n⚙️  Real-time browsing architecture - no background tasks needed")
    
    # Define services
    services = [
    {
        "name": "Main API Service",
        "module": "main_api_service",
        "port": 8000,
        "description": "User management, coordinates browsing and downloading services"
    },
    {
        "name": "Aggregation Service",
        "module": "aggregation_service",
        "port": 8003,
        "description": "Intelligent concert aggregation - groups recordings by concert instances"
    },
    {
        "name": "Download Service",
        "module": "download_service",
        "port": 8002,
        "description": "Downloads music files from Internet Archive"
    },
    {
        "name": "Browse Service",
        "module": "browse_service",
        "port": 8001,
        "description": "Real-time browsing of Internet Archive live music with smart caching"
    }
]
    
    # Start all services
    processes = []
    for service in services:
        process = start_service(**service)
        processes.append((service["name"], process))
        time.sleep(1)  # Small delay between starts
    
    print("\n" + "=" * 60)
    print("🎉 All services started successfully!")
    print("\n📋 Service URLs:")
    print("   🌐 Web Interface:     http://127.0.0.1:8000/")
    print("   📚 API Documentation: http://127.0.0.1:8000/docs")
    print("   🔍 Search Service:    http://127.0.0.1:8003/docs")
    print("   ⬇️  Download Service:  http://127.0.0.1:8002/docs")
    print("   🕷️  Browse Service:    http://127.0.0.1:8001/docs")
    
    print("\n🔧 Development Commands:")
    print("   • Test setup:        python test_setup.py")
    print("   • Test database:     python test_database.py")
    print("   • Demo API calls:    python demo.py")
    
    print("\n📁 Project Structure:")
    print("   • Main API:          backend/main_api_service/")
    print("   • Search Service:    backend/search_service/")
    print("   • Download Service:  backend/download_service/")
    print("   • Browse Service:    backend/browse_service/")
    print("   • Shared Code:       shared/")
    print("   • Database:          data/music_player.db")
    print("   • Downloads:         downloads/")
    
    print("\n🔄 Architecture Flow:")
    print("   1. Browse Service → Real-time Internet Archive browsing with smart caching")
    print("   2. Search Service → Searches user library and playlists")
    print("   3. Download Service → Downloads files from Internet Archive")
    print("   4. Main API → Coordinates all services → User interface")
    
    print("\n⏹️  To stop all services: Press Ctrl+C")
    print("=" * 60)
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check if any process has died
            for name, process in processes:
                if process.poll() is not None:
                    print(f"❌ {name} has stopped unexpectedly")
                    return
                    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        
        # Note: Background tasks removed for real-time architecture
        
        # Terminate all processes gracefully
        for name, process in processes:
            print(f"🛑 Stopping {name}...")
            try:
                process.terminate()
                # Wait for graceful shutdown
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print(f"⚠️  {name} didn't stop gracefully, forcing termination...")
                process.kill()
                process.wait()
            except Exception as e:
                print(f"⚠️  Error stopping {name}: {e}")
        
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
