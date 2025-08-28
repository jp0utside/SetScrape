#!/bin/bash

# Mobile Music Player System - Development Setup

echo "🎵 Setting up Mobile Music Player for Development"
echo "================================================="

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.11 or higher is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p downloads logs data

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database Configuration (SQLite)
DATABASE_URL=sqlite+aiosqlite:///./data/music_player.db

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Internet Archive API (optional)
INTERNET_ARCHIVE_API_KEY=your-ia-api-key

# Service URLs
SCRAPING_SERVICE_URL=http://127.0.0.1:8001
DOWNLOAD_SERVICE_URL=http://127.0.0.1:8002

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
EOF
    echo "✅ Created .env file with development settings"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Development setup complete!"
echo ""
echo "Next steps:"
echo "1. Start all services: python start.py"
echo "2. Open API docs: http://127.0.0.1:8000/docs"
echo "3. Start mobile app: cd mobile-app && npm install && npx expo start"
echo ""
echo "To activate the virtual environment in the future:"
echo "source venv/bin/activate"
echo ""
echo "To start development:"
echo "python start.py"
