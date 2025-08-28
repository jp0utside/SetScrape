import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../types/navigation';
import { useAuth } from '../contexts/AuthContext';
import { useDownloads } from '../contexts/DownloadContext';
import apiService from '../services/api';
import Icon from '../components/Icon';
import { format, parseISO } from 'date-fns';

type UserScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Main'>;

const UserScreen: React.FC = () => {
  const { user, logout } = useAuth();
  const { downloads } = useDownloads();
  const [stats, setStats] = useState<any>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(true);

  const navigation = useNavigation<UserScreenNavigationProp>();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setIsLoadingStats(true);
      const statsData = await apiService.getStats();
      setStats(statsData);
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setIsLoadingStats(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            try {
              await logout();
              navigation.reset({
                index: 0,
                routes: [{ name: 'Login' }],
              });
            } catch (error) {
              Alert.alert('Error', 'Failed to logout');
            }
          },
        },
      ]
    );
  };

  const getDownloadStats = () => {
    const completed = downloads.filter(d => d.status === 'completed').length;
    const downloading = downloads.filter(d => d.status === 'downloading').length;
    const pending = downloads.filter(d => d.status === 'pending').length;
    const failed = downloads.filter(d => d.status === 'failed').length;

    return { completed, downloading, pending, failed };
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const renderProfileSection = () => (
    <View style={styles.section}>
      <View style={styles.profileHeader}>
        <View style={styles.avatarContainer}>
          <Icon name="person" size={40} color="#fff" />
        </View>
        <View style={styles.profileInfo}>
          <Text style={styles.username}>{user?.username}</Text>
          <Text style={styles.email}>{user?.email || 'No email provided'}</Text>
          <Text style={styles.memberSince}>
            Member since {user?.created_at ? format(parseISO(user.created_at), 'MMM yyyy') : 'Unknown'}
          </Text>
        </View>
      </View>
    </View>
  );

  const renderStatsSection = () => {
    const downloadStats = getDownloadStats();
    const totalDownloads = downloadStats.completed + downloadStats.downloading + downloadStats.pending + downloadStats.failed;

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your Activity</Text>
        
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Icon name="download" size={24} color="#6200ee" />
            <Text style={styles.statNumber}>{totalDownloads}</Text>
            <Text style={styles.statLabel}>Total Downloads</Text>
          </View>
          
          <View style={styles.statCard}>
            <Icon name="check-circle" size={24} color="#4caf50" />
            <Text style={styles.statNumber}>{downloadStats.completed}</Text>
            <Text style={styles.statLabel}>Completed</Text>
          </View>
          
          <View style={styles.statCard}>
            <Icon name="schedule" size={24} color="#ff9800" />
            <Text style={styles.statNumber}>{downloadStats.pending}</Text>
            <Text style={styles.statLabel}>Pending</Text>
          </View>
          
          <View style={styles.statCard}>
            <Icon name="error" size={24} color="#f44336" />
            <Text style={styles.statNumber}>{downloadStats.failed}</Text>
            <Text style={styles.statLabel}>Failed</Text>
          </View>
        </View>
      </View>
    );
  };

  const renderSystemStats = () => {
    if (isLoadingStats) {
      return (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>System Status</Text>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#6200ee" />
            <Text style={styles.loadingText}>Loading system stats...</Text>
          </View>
        </View>
      );
    }

    if (!stats) return null;

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>System Status</Text>
        
        <View style={styles.systemStats}>
          <View style={styles.systemStatRow}>
            <Icon name="people" size={20} color="#666" />
            <Text style={styles.systemStatLabel}>Total Users:</Text>
            <Text style={styles.systemStatValue}>{stats.total_users}</Text>
          </View>
          
          <View style={styles.systemStatRow}>
            <Icon name="music-note" size={20} color="#666" />
            <Text style={styles.systemStatLabel}>Total Concerts:</Text>
            <Text style={styles.systemStatValue}>{stats.total_concerts}</Text>
          </View>
          
          <View style={styles.systemStatRow}>
            <Icon name="album" size={20} color="#666" />
            <Text style={styles.systemStatLabel}>Total Recordings:</Text>
            <Text style={styles.systemStatValue}>{stats.total_recordings}</Text>
          </View>
          
          <View style={styles.systemStatRow}>
            <Icon name="download" size={20} color="#666" />
            <Text style={styles.systemStatLabel}>Total Downloads:</Text>
            <Text style={styles.systemStatValue}>{stats.total_downloads}</Text>
          </View>
        </View>
      </View>
    );
  };

  const renderSettingsSection = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Settings</Text>
      
      <TouchableOpacity style={styles.settingItem}>
                    <Icon name="notifications" size={20} color="#666" />
        <Text style={styles.settingText}>Notifications</Text>
        <Icon name="chevron-right" size={20} color="#ccc" />
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.settingItem}>
        <Icon name="storage" size={20} color="#666" />
        <Text style={styles.settingText}>Storage Settings</Text>
        <Icon name="chevron-right" size={20} color="#ccc" />
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.settingItem}>
        <Icon name="help" size={20} color="#666" />
        <Text style={styles.settingText}>Help & Support</Text>
        <Icon name="chevron-right" size={20} color="#ccc" />
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.settingItem}>
        <Icon name="info" size={20} color="#666" />
        <Text style={styles.settingText}>About</Text>
        <Icon name="chevron-right" size={20} color="#ccc" />
      </TouchableOpacity>
    </View>
  );

  const renderLogoutSection = () => (
    <View style={styles.section}>
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Icon name="logout" size={20} color="#f44336" />
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {renderProfileSection()}
      {renderStatsSection()}
      {renderSystemStats()}
      {renderSettingsSection()}
      {renderLogoutSection()}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  section: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#6200ee',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  profileInfo: {
    flex: 1,
  },
  username: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  email: {
    fontSize: 16,
    color: '#666',
    marginBottom: 4,
  },
  memberSince: {
    fontSize: 14,
    color: '#999',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#666',
  },
  systemStats: {
    gap: 12,
  },
  systemStatRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  systemStatLabel: {
    fontSize: 14,
    color: '#666',
    marginLeft: 12,
    flex: 1,
  },
  systemStatValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingText: {
    fontSize: 16,
    color: '#333',
    marginLeft: 12,
    flex: 1,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    backgroundColor: '#fff5f5',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#fecaca',
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#f44336',
    marginLeft: 8,
  },
});

export default UserScreen;
