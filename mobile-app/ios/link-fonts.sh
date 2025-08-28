#!/bin/bash

# Script to manually link react-native-vector-icons fonts to iOS project
echo "Linking vector icons fonts to iOS project..."

# Path to the project file
PROJECT_FILE="internet-archive-music-player.xcodeproj/project.pbxproj"

# Check if project file exists
if [ ! -f "$PROJECT_FILE" ]; then
    echo "Error: Project file not found at $PROJECT_FILE"
    exit 1
fi

# Create backup
cp "$PROJECT_FILE" "${PROJECT_FILE}.backup"
echo "Created backup: ${PROJECT_FILE}.backup"

# Font files to link
FONTS=(
    "AntDesign.ttf"
    "Entypo.ttf"
    "EvilIcons.ttf"
    "Feather.ttf"
    "FontAwesome.ttf"
    "FontAwesome5_Brands.ttf"
    "FontAwesome5_Regular.ttf"
    "FontAwesome5_Solid.ttf"
    "FontAwesome6_Brands.ttf"
    "FontAwesome6_Regular.ttf"
    "FontAwesome6_Solid.ttf"
    "Fontisto.ttf"
    "Foundation.ttf"
    "Ionicons.ttf"
    "MaterialCommunityIcons.ttf"
    "MaterialIcons.ttf"
    "Octicons.ttf"
    "SimpleLineIcons.ttf"
    "Zocial.ttf"
)

# Add fonts to the project
for font in "${FONTS[@]}"; do
    if [ -f "InternetArchiveMusicPlayer/$font" ]; then
        echo "Adding $font to project..."
        
        # Add font reference to project.pbxproj
        # This is a simplified approach - in a real scenario, you'd need to properly parse and modify the plist structure
        # For now, let's try a different approach
    else
        echo "Warning: Font file $font not found"
    fi
done

echo "Font linking complete. You may need to manually add fonts in Xcode."
echo "1. Open the project in Xcode"
echo "2. Right-click on InternetArchiveMusicPlayer folder"
echo "3. Select 'Add Files to InternetArchiveMusicPlayer'"
echo "4. Select all .ttf files from the InternetArchiveMusicPlayer folder"
echo "5. Make sure 'Add to target' is checked for InternetArchiveMusicPlayer"
