import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { useRoute } from '@react-navigation/native';
import { RouteProp } from '@react-navigation/native';
import { ArchiveItem, DirectoryFile } from '../types/api';
import { useDownloads } from '../contexts/DownloadContext';
import apiService from '../services/api';
import Icon from '../components/Icon';
import { format, parseISO } from 'date-fns';

type RecordingDetailRouteProp = RouteProp<RootStackParamList, 'RecordingDetail'>;

const RecordingDetailScreen: React.FC = () => {
  const route = useRoute<RecordingDetailRouteProp>();
  const { identifier, recording: initialRecording } = route.params;
  
  const [recording, setRecording] = useState<ArchiveItem | null>(initialRecording);
  const [directory, setDirectory] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(!initialRecording);
  const [isLoadingDirectory, setIsLoadingDirectory] = useState(false);
  const { startDownload } = useDownloads();

  useEffect(() => {
    if (!initialRecording) {
      loadRecordingDetails();
    }
    loadDirectoryStructure();
  }, [identifier]);

  const loadRecordingDetails = async () => {
    try {
      setIsLoading(true);
      const recordingData = await apiService.getItemDetails(identifier);
      setRecording(recordingData);
    } catch (error) {
      console.error('Error loading recording details:', error);
      Alert.alert('Error', 'Failed to load recording details');
    } finally {
      setIsLoading(false);
    }
  };

  const loadDirectoryStructure = async () => {
    try {
      setIsLoadingDirectory(true);
      const directoryData = await apiService.getDirectoryStructure(identifier);
      setDirectory(directoryData);
    } catch (error) {
      console.error('Error loading directory structure:', error);
      Alert.alert('Error', 'Failed to load file structure');
    } finally {
      setIsLoadingDirectory(false);
    }
  };

  const handleDownloadFile = async (file: DirectoryFile) => {
    try {
      await startDownload({
        archive_identifier: identifier,
        filename: file.name,
        track_title: file.name,
      });
      Alert.alert('Success', `Started downloading ${file.name}`);
    } catch (error) {
      Alert.alert('Error', 'Failed to start download');
    }
  };

  const handleDownloadAllAudio = async () => {
    if (!directory) return;

    Alert.alert(
      'Download All Audio Files',
      `This will start downloading all ${directory.audio_files.length} audio files. Continue?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Download All',
          onPress: async () => {
            try {
              let downloadCount = 0;
              
              for (const file of directory.audio_files) {
                await startDownload({
                  archive_identifier: identifier,
                  filename: file.name,
                  track_title: file.name,
                });
                downloadCount++;
              }
              
              Alert.alert('Success', `Started downloading ${downloadCount} audio files`);
            } catch (error) {
              Alert.alert('Error', 'Failed to start downloads');
            }
          },
        },
      ]
    );
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'audio':
        return 'audiotrack';
      case 'image':
        return 'image';
      case 'metadata':
        return 'description';
      default:
        return 'insert-drive-file';
    }
  };

  const getFileColor = (fileType: string) => {
    switch (fileType) {
      case 'audio':
        return '#6200ee';
      case 'image':
        return '#4caf50';
      case 'metadata':
        return '#ff9800';
      default:
        return '#666';
    }
  };

  const renderFileItem = ({ item }: { item: DirectoryFile }) => {
    const fileIcon = getFileIcon(item.type);
    const fileColor = getFileColor(item.type);

    return (
      <View style={styles.fileCard}>
        <View style={styles.fileHeader}>
          <View style={styles.fileInfo}>
            <Icon name={fileIcon} size={20} color={fileColor} />
            <View style={styles.fileDetails}>
              <Text style={styles.fileName} numberOfLines={1}>
                {item.name}
              </Text>
              <Text style={styles.fileSize}>{formatFileSize(item.size)}</Text>
            </View>
          </View>
          {item.type === 'audio' && (
            <TouchableOpacity
              style={styles.downloadButton}
              onPress={() => handleDownloadFile(item)}
            >
              <Icon name="download" size={16} color="#6200ee" />
            </TouchableOpacity>
          )}
        </View>
        {item.format && (
          <Text style={styles.fileFormat}>{item.format.toUpperCase()}</Text>
        )}
      </View>
    );
  };

  const renderFileSection = (title: string, files: DirectoryFile[], type: string) => {
    if (!files || files.length === 0) return null;

    return (
      <View style={styles.fileSection}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>{title} ({files.length})</Text>
          {type === 'audio' && files.length > 0 && (
            <TouchableOpacity
              style={styles.downloadAllButton}
              onPress={handleDownloadAllAudio}
            >
              <Icon name="download" size={16} color="#6200ee" />
              <Text style={styles.downloadAllText}>All</Text>
            </TouchableOpacity>
          )}
        </View>
        {files.map((file, index) => (
          <View key={`${file.name}-${index}`}>
            {renderFileItem({ item: file })}
          </View>
        ))}
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6200ee" />
        <Text style={styles.loadingText}>Loading recording details...</Text>
      </View>
    );
  }

  if (!recording) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="error" size={64} color="#ccc" />
        <Text style={styles.errorTitle}>Recording Not Found</Text>
        <Text style={styles.errorSubtitle}>
          The requested recording could not be loaded
        </Text>
      </View>
    );
  }

  const recordingDate = recording.date ? parseISO(recording.date) : null;
  const formattedDate = recordingDate ? format(recordingDate, 'EEEE, MMMM dd, yyyy') : 'Unknown Date';

  return (
    <View style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Recording Header */}
        <View style={styles.header}>
          <Text style={styles.recordingTitle}>{recording.title}</Text>
          {recording.artist && (
            <Text style={styles.artistName}>{recording.artist}</Text>
          )}
          <Text style={styles.recordingDate}>{formattedDate}</Text>
          {recording.venue && (
            <View style={styles.venueContainer}>
              <Icon name="location-on" size={16} color="#666" />
              <Text style={styles.venueText}>{recording.venue}</Text>
            </View>
          )}
          {recording.location && (
            <Text style={styles.locationText}>{recording.location}</Text>
          )}
        </View>

        {/* Recording Stats */}
        <View style={styles.statsSection}>
          <View style={styles.statCard}>
            <Icon name="music-note" size={24} color="#6200ee" />
            <Text style={styles.statNumber}>{recording.total_tracks}</Text>
            <Text style={styles.statLabel}>Tracks</Text>
          </View>
          <View style={styles.statCard}>
            <Icon name="storage" size={24} color="#6200ee" />
            <Text style={styles.statNumber}>{formatFileSize(recording.total_size)}</Text>
            <Text style={styles.statLabel}>Total Size</Text>
          </View>
          <View style={styles.statCard}>
            <Icon name="folder" size={24} color="#6200ee" />
            <Text style={styles.statNumber}>{directory?.total_files || 0}</Text>
            <Text style={styles.statLabel}>Files</Text>
          </View>
          <View style={styles.statCard}>
            <Icon name="download" size={24} color="#6200ee" />
            <Text style={styles.statNumber}>{recording.downloads}</Text>
            <Text style={styles.statLabel}>Downloads</Text>
          </View>
        </View>

        {/* Recording Description */}
        {recording.description && (
          <View style={styles.descriptionSection}>
            <Text style={styles.sectionTitle}>Description</Text>
            <Text style={styles.descriptionText}>{recording.description}</Text>
          </View>
        )}

        {/* Source Information */}
        {(recording.source || recording.taper || recording.lineage) && (
          <View style={styles.sourceSection}>
            <Text style={styles.sectionTitle}>Recording Information</Text>
            {recording.source && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Source:</Text>
                <Text style={styles.infoValue}>{recording.source}</Text>
              </View>
            )}
            {recording.taper && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Taper:</Text>
                <Text style={styles.infoValue}>{recording.taper}</Text>
              </View>
            )}
            {recording.lineage && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Lineage:</Text>
                <Text style={styles.infoValue}>{recording.lineage}</Text>
              </View>
            )}
          </View>
        )}

        {/* Files Section */}
        <View style={styles.filesSection}>
          <Text style={styles.sectionTitle}>Files</Text>
          
          {isLoadingDirectory ? (
            <View style={styles.loadingFilesContainer}>
              <ActivityIndicator size="small" color="#6200ee" />
              <Text style={styles.loadingFilesText}>Loading files...</Text>
            </View>
          ) : directory ? (
            <>
              {renderFileSection('Audio Files', directory.audio_files, 'audio')}
              {renderFileSection('Images', directory.image_files, 'image')}
              {renderFileSection('Metadata', directory.metadata_files, 'metadata')}
              {renderFileSection('Other Files', directory.other_files, 'other')}
            </>
          ) : (
            <View style={styles.noFilesContainer}>
              <Icon name="folder-open" size={48} color="#ccc" />
              <Text style={styles.noFilesText}>No files available</Text>
            </View>
          )}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 40,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  errorSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
  },
  header: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 10,
  },
  recordingTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  artistName: {
    fontSize: 18,
    color: '#666',
    marginBottom: 8,
  },
  recordingDate: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  venueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  venueText: {
    fontSize: 14,
    color: '#666',
    marginLeft: 4,
  },
  locationText: {
    fontSize: 12,
    color: '#999',
  },
  statsSection: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 10,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 18,
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
  descriptionSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  descriptionText: {
    fontSize: 16,
    color: '#666',
    lineHeight: 24,
  },
  sourceSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 10,
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  infoLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    width: 80,
  },
  infoValue: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  filesSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 20,
  },
  loadingFilesContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  loadingFilesText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#666',
  },
  noFilesContainer: {
    alignItems: 'center',
    padding: 40,
  },
  noFilesText: {
    fontSize: 16,
    color: '#666',
    marginTop: 8,
  },
  fileSection: {
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  downloadAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    backgroundColor: '#f0f0f0',
  },
  downloadAllText: {
    fontSize: 12,
    color: '#6200ee',
    marginLeft: 4,
    fontWeight: '600',
  },
  fileCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  fileHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  fileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  fileDetails: {
    marginLeft: 12,
    flex: 1,
  },
  fileName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  fileSize: {
    fontSize: 12,
    color: '#666',
  },
  downloadButton: {
    padding: 8,
  },
  fileFormat: {
    fontSize: 10,
    color: '#999',
    marginTop: 4,
    fontFamily: 'monospace',
  },
});

export default RecordingDetailScreen;
