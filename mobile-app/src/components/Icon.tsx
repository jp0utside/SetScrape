import React from 'react';
import { Text, StyleSheet } from 'react-native';

interface IconProps {
  name: string;
  size?: number;
  color?: string;
  style?: any;
}

const Icon: React.FC<IconProps> = ({ name, size = 24, color = '#000', style }) => {
  // Comprehensive icon mapping for all icons used in the app
  const iconMap: { [key: string]: string } = {
    // Tab bar icons
    'home': '🏠',
    'search': '🔍',
    'download': '⬇️',
    'person': '👤',
    
    // Music and media icons
    'music-note': '🎵',
    'play-arrow': '▶️',
    'pause': '⏸️',
    'stop': '⏹️',
    'skip-next': '⏭️',
    'skip-previous': '⏮️',
    'volume-up': '🔊',
    'volume-down': '🔉',
    'volume-off': '🔇',
    'music-off': '🔇',
    'album': '💿',
    
    // File and storage icons
    'storage': '💾',
    'folder': '📁',
    'file-download': '📥',
    'file-upload': '📤',
    'description': '📄',
    'insert-drive-file': '📄',
    'folder-open': '📂',
    
    // Location and navigation
    'location-on': '📍',
    'place': '📍',
    'directions': '🧭',
    'navigation': '🧭',
    
    // Time and schedule
    'schedule': '⏰',
    'access-time': '⏰',
    'event': '📅',
    'today': '📅',
    
    // Information and help
    'info': 'ℹ️',
    'help': '❓',
    'help-outline': '❓',
    'question-mark': '❓',
    'lock': '🔒',
    'visibility': '👁️',
    'visibility-off': '👁️‍🗨️',
    
    // Actions and controls
    'cancel': '❌',
    'close': '❌',
    'clear': '❌',
    'refresh': '🔄',
    'replay': '🔄',
    'settings': '⚙️',
    'edit': '✏️',
    'delete': '🗑️',
    'add': '➕',
    'remove': '➖',
    'chevron-right': '▶️',
    'logout': '🚪',
    'notifications': '🔔',
    
    // Status and feedback
    'error': '❌',
    'warning': '⚠️',
    'check-circle': '✅',
    'check': '✅',
    'done': '✅',
    'success': '✅',
    
    // Communication
    'email': '📧',
    'phone': '📞',
    'message': '💬',
    'chat': '💬',
    
    // Social and user
    'account-circle': '👤',
    'person-outline': '👤',
    'group': '👥',
    'people': '👥',
    
    // Search and filter
    'filter-list': '🔍',
    'sort': '↕️',
    'tune': '🎛️',
    'search-off': '🔍',
    'download-done': '✅',
    
    // Default fallback
    'default': '❓',
  };

  const icon = iconMap[name] || iconMap['default'] || '❓';

  return (
    <Text style={[styles.icon, { fontSize: size, color }, style]}>
      {icon}
    </Text>
  );
};

const styles = StyleSheet.create({
  icon: {
    textAlign: 'center',
  },
});

export default Icon;
