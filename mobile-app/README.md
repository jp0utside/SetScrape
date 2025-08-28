# Internet Archive Music Player - Mobile App

A React Native mobile application for browsing and downloading live music from Internet Archive. This app provides a modern, intuitive interface for discovering and managing live music recordings.

## Features

### 🏠 Home Screen
- View recent concerts from the past week
- Browse aggregated concert data
- Quick access to concert details
- Pull-to-refresh functionality

### 🔍 Search Screen
- Search for individual recordings
- Filter by date range (All Time, Past Week, Month, 3 Months, Year)
- Browse Internet Archive music collection
- Real-time search results

### ⬇️ Downloads Screen
- Track download progress in real-time
- View download queue with status indicators
- Cancel pending downloads
- Download completed files to device
- Detailed download information

### 👤 User Screen
- User profile information
- Download statistics and activity
- System status and statistics
- Settings and preferences
- Logout functionality

## Technical Features

- **Authentication**: JWT-based authentication with session management
- **Real-time Updates**: Live download progress tracking
- **Offline Support**: Download files for offline playback
- **Modern UI**: Clean, responsive design with Material Design principles
- **Cross-platform**: Works on both iOS and Android
- **TypeScript**: Full type safety and better development experience

## Prerequisites

- Node.js (v16 or higher)
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development, macOS only)
- Your backend services running (see backend setup)

## Installation

1. **Clone the repository and navigate to the mobile app directory:**
   ```bash
   cd mobile-app
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **iOS Setup (macOS only):**
   ```bash
   cd ios && pod install && cd ..
   ```

4. **Configure API URL:**
   Edit `src/services/api.ts` and update the `API_BASE_URL`:
   ```typescript
   // For Android emulator
   const API_BASE_URL = 'http://10.0.2.2:8000';
   
   // For iOS simulator
   // const API_BASE_URL = 'http://localhost:8000';
   
   // For physical device (replace with your server IP)
   // const API_BASE_URL = 'http://192.168.1.100:8000';
   ```

## Running the App

### Android
```bash
npm run android
```

### iOS
```bash
npm run ios
```

### Start Metro Bundler
```bash
npm start
```

## Project Structure

```
mobile-app/
├── src/
│   ├── contexts/           # React Context providers
│   │   ├── AuthContext.tsx
│   │   └── DownloadContext.tsx
│   ├── screens/            # App screens
│   │   ├── LoginScreen.tsx
│   │   ├── HomeScreen.tsx
│   │   ├── SearchScreen.tsx
│   │   ├── DownloadsScreen.tsx
│   │   ├── UserScreen.tsx
│   │   ├── ConcertDetailScreen.tsx
│   │   └── RecordingDetailScreen.tsx
│   ├── services/           # API services
│   │   └── api.ts
│   └── types/              # TypeScript type definitions
│       ├── api.ts
│       └── navigation.ts
├── App.tsx                 # Main app component
├── index.js               # App entry point
└── package.json           # Dependencies and scripts
```

## API Integration

The app integrates with your backend services through the following endpoints:

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout

### Music Browsing
- `GET /music/browse` - Browse recordings
- `GET /music/directory/{identifier}` - Get file structure
- `GET /concerts` - Browse concerts

### Downloads
- `POST /downloads` - Start download
- `GET /downloads` - Get download queue
- `DELETE /downloads/{id}` - Cancel download
- `GET /downloads/{id}/file` - Download file

### System
- `GET /stats` - System statistics

## Key Dependencies

- **React Navigation**: Navigation between screens
- **Axios**: HTTP client for API calls
- **AsyncStorage**: Local data persistence
- **React Native Vector Icons**: Material Design icons
- **Date-fns**: Date formatting utilities
- **React Native Progress**: Progress indicators

## Development

### Adding New Features
1. Create new components in `src/screens/`
2. Add navigation routes in `App.tsx`
3. Update TypeScript types in `src/types/`
4. Add API methods in `src/services/api.ts`

### Styling
The app uses a consistent design system with:
- Primary color: `#6200ee` (Purple)
- Background: `#f5f5f5` (Light Gray)
- Cards: `#ffffff` (White)
- Text colors: `#333`, `#666`, `#999`

### State Management
- **AuthContext**: Manages user authentication state
- **DownloadContext**: Manages download queue and progress
- **Local State**: Component-specific state using React hooks

## Troubleshooting

### Common Issues

1. **Metro bundler issues:**
   ```bash
   npx react-native start --reset-cache
   ```

2. **iOS build issues:**
   ```bash
   cd ios && pod install && cd ..
   ```

3. **Android build issues:**
   ```bash
   cd android && ./gradlew clean && cd ..
   ```

4. **API connection issues:**
   - Verify backend services are running
   - Check API_BASE_URL configuration
   - Ensure network connectivity

### Debug Mode
Enable debug mode by shaking the device or pressing `Cmd+D` (iOS) / `Cmd+M` (Android) in the simulator.

## Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for new features
3. Test on both iOS and Android
4. Update documentation for new features

## License

This project is part of the Internet Archive Music Player system. See the main project license for details.
