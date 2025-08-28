# 🎵 Internet Archive Music Player

A **full-stack music player system** with a **4-service microservices backend** and **React Native mobile app** for browsing and downloading live music from Internet Archive. Features real-time browsing, intelligent concert aggregation, and offline-first functionality.

## 🏗️ Architecture

### Backend Services (Microservices)
- **🎵 Main API Service** (Port 8000): User management, authentication, service coordination
- **🔍 Aggregation Service** (Port 8003): Intelligent concert aggregation - groups recordings by concert instances
- **⬇️ Download Service** (Port 8002): Downloads music files from Internet Archive with real-time progress
- **🌐 Browse Service** (Port 8001): Real-time browsing of Internet Archive live music with smart caching

### Mobile App
- **📱 React Native App**: Cross-platform mobile application for iOS and Android
- **🔐 JWT Authentication**: Secure user authentication and session management
- **📊 Real-time Updates**: Live download progress tracking via WebSockets
- **📱 Offline Support**: Download files for offline playback

## 🚀 Quick Start

### Backend Setup

```bash
# Clone and setup
git clone <repository-url>
cd set-scrape

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start all backend services
python start.py
```

### Mobile App Setup

```bash
# Navigate to mobile app directory
cd mobile-app

# Install dependencies
npm install

# iOS Setup (macOS only)
cd ios && pod install && cd ..

# Configure API URL in src/services/api.ts
# For Android emulator: http://10.0.2.2:8000
# For iOS simulator: http://localhost:8000
# For physical device: http://YOUR_SERVER_IP:8000

# Run the app
npx react-native run-android  # or npx react-native run-ios --scheme InternetArchiveMusicPlayer
```

## 📋 Service URLs

### Backend Services
- **🌐 Web Interface**: http://127.0.0.1:8000/
- **📚 API Documentation**: http://127.0.0.1:8000/docs
- **🔍 Aggregation Service**: http://127.0.0.1:8003/docs
- **⬇️ Download Service**: http://127.0.0.1:8002/docs
- **🌐 Browse Service**: http://127.0.0.1:8001/docs

## 🎯 Key Features

### Backend
- **Real-time Browsing**: Direct Internet Archive API calls with smart caching
- **Intelligent Aggregation**: Groups recordings by concert instances automatically
- **User Management**: Authentication and user profiles
- **Real-time Downloads**: WebSocket progress tracking

### Mobile App
- **🏠 Home Screen**: Recent concerts from the past week
- **🔍 Search Screen**: Search Internet Archive uploads directly
- **⬇️ Downloads Screen**: Real-time download progress tracking
- **👤 User Screen**: Profile, statistics, and settings
- **📱 Cross-platform**: Works on both iOS and Android
- **🔐 Secure**: JWT-based authentication

## 📁 Project Structure

```
├── backend/
│   ├── main_api_service/     # Main API Service (Port 8000)
│   ├── aggregation_service/  # Aggregation Service (Port 8003)
│   ├── download_service/     # Download Service (Port 8002)
│   └── browse_service/       # Browse Service (Port 8001)
├── mobile-app/               # React Native mobile application
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── screens/          # App screens
│   │   ├── services/         # API services
│   │   ├── contexts/         # React contexts
│   │   └── types/           # TypeScript type definitions
│   ├── android/             # Android-specific files
│   └── ios/                 # iOS-specific files
├── shared/                   # Shared utilities and models
├── data/                    # SQLite database
├── downloads/               # Downloaded music files
├── start.py                 # Service startup script
└── requirements.txt         # Python dependencies
```

## 🛠️ Development

### Backend Development
This system is designed for local development with:
- **SQLite** database for simplicity
- **Real-time API calls** to Internet Archive with smart caching
- **Local file storage** for downloads
- **Hot reload** for all services

### Mobile Development
- **TypeScript** for type safety
- **React Native** for cross-platform development
- **Material Design** principles for UI
- **Hot reloading** for development

## 📖 Documentation

For detailed architecture documentation, see [README-ARCHITECTURE.md](README-ARCHITECTURE.md).

## 🔧 Development Commands

```bash
# Backend
python start.py                    # Start all services
python test_setup.py              # Test setup
python test_database.py           # Test database
python demo.py                    # Demo API calls

# Mobile App
npm start                         # Start Metro bundler
npm run android                   # Run on Android
npx react-native run-ios --scheme InternetArchiveMusicPlayer  # Run on iOS
```

## 🔮 Future Enhancements

- Containerization with Docker
- PostgreSQL for production
- Cloud storage integration
- Streaming and media player integration
- Social features (sharing, following)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
