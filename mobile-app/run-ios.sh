#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Start Metro in the background
echo "Starting Metro bundler..."
npx metro start --reset-cache &

# Wait a moment for Metro to start
sleep 3

# Run the iOS app
echo "Building and running iOS app..."
npx react-native run-ios --scheme InternetArchiveMusicPlayer

# Clean up background process
pkill -f "metro start"
