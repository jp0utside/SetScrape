#!/bin/bash

# Internet Archive Music Player - Mobile App Setup Script

echo "🎵 Setting up Internet Archive Music Player Mobile App..."
echo "=================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js v16 or higher."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16 or higher is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed."
    exit 1
fi

echo "✅ npm version: $(npm -v)"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# iOS setup (macOS only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Setting up iOS dependencies..."
    
    # Check if CocoaPods is installed
    if ! command -v pod &> /dev/null; then
        echo "⚠️  CocoaPods is not installed. Installing..."
        sudo gem install cocoapods
    fi
    
    # Install iOS pods
    cd ios && pod install && cd ..
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install iOS pods"
        exit 1
    fi
    
    echo "✅ iOS setup completed"
else
    echo "ℹ️  Skipping iOS setup (not on macOS)"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# API Configuration
API_BASE_URL_ANDROID_EMULATOR=http://10.0.2.2:8000
API_BASE_URL_IOS_SIMULATOR=http://localhost:8000
API_BASE_URL_PHYSICAL_DEVICE=http://192.168.1.100:8000

# App Configuration
APP_NAME=Internet Archive Music Player
APP_VERSION=1.0.0
EOF
    echo "✅ .env file created"
fi

# Check if React Native CLI is installed globally
if ! command -v react-native &> /dev/null; then
    echo "📦 Installing React Native CLI globally..."
    npm install -g @react-native-community/cli
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install React Native CLI"
        exit 1
    fi
fi

echo "✅ React Native CLI installed"

# Create gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    echo "📝 Creating .gitignore file..."
    cat > .gitignore << EOF
# OSX
#
.DS_Store

# Xcode
#
build/
*.pbxuser
!default.pbxuser
*.mode1v3
!default.mode1v3
*.mode2v3
!default.mode2v3
*.perspectivev3
!default.perspectivev3
xcuserdata
*.xccheckout
*.moved-aside
DerivedData
*.hmap
*.ipa
*.xcuserstate
ios/.xcode.env.local

# Android/IntelliJ
#
build/
.idea
.gradle
local.properties
*.iml
*.hprof
.cxx/
*.keystore
!debug.keystore

# node.js
#
node_modules/
npm-debug.log
yarn-error.log

# BUCK
buck-out/
\.buckd/
*.keystore
!debug.keystore

# fastlane
#
# It is recommended to not store the screenshots in the git repo. Instead, use fastlane to re-generate the
# screenshots whenever they are needed.
# For more information about the recommended setup visit:
# https://docs.fastlane.tools/best-practices/source-control/

*/fastlane/report.xml
*/fastlane/Preview.html
*/fastlane/screenshots

# Bundle artifacts
*.jsbundle

# CocoaPods
/ios/Pods/

# Expo
.expo/
web-build/

# Flipper
ios/Pods/Flipper*

# Temporary files created by Metro to check the health of the file watcher
.metro-health-check*

# Testing
/coverage

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
EOF
    echo "✅ .gitignore file created"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Make sure your backend services are running"
echo "2. Update the API_BASE_URL in src/services/api.ts if needed"
echo "3. Run the app:"
echo "   - Android: npm run android"
echo "   - iOS: npm run ios"
echo "   - Metro: npm start"
echo ""
echo "For more information, see README.md"
