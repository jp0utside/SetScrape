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
import { useRoute, useNavigation } from '@react-navigation/native';
import { RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../types/navigation';
import { AggregatedConcert, ConcertRecording } from '../types/api';
import { useDownloads } from '../contexts/DownloadContext';
import apiService from '../services/api';
import Icon from '../components/Icon';
import { format, parseISO } from 'date-fns';

type ConcertDetailRouteProp = RouteProp<RootStackParamList, 'ConcertDetail'>;
type ConcertDetailNavigationProp = StackNavigationProp<RootStackParamList, 'ConcertDetail'>;

const ConcertDetailScreen: React.FC = () => {
  const route = useRoute<ConcertDetailRouteProp>();
  const navigation = useNavigation<ConcertDetailNavigationProp>();
  const { concertKey, concert: initialConcert } = route.params;
  
  const [concert, setConcert] = useState<AggregatedConcert | null>(initialConcert);
  const [isLoading, setIsLoading] = useState(!initialConcert);
  const { startDownload } = useDownloads();

  useEffect(() => {
    if (!initialConcert) {
      loadConcertDetails();
    }
  }, [concertKey]);

  const loadConcertDetails = async () => {
    try {
      setIsLoading(true);
      const concertData = await apiService.getConcertDetails(concertKey);
      setConcert(concertData);
    } catch (error) {
      console.error('Error loading concert details:', error);
      Alert.alert('Error', 'Failed to load concert details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRecordingPress = (recording: ConcertRecording) => {
    navigation.navigate('RecordingDetail', {
      identifier: recording.archive_identifier,
      recording,
    });
  };

  const handleDownloadAllAudio = async () => {
    if (!concert) return;

    Alert.alert(
      'Download All Audio Files',
      `This will start downloading all audio files from ${concert.recordings.length} recordings. Continue?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Download All',
          onPress: async () => {
            try {
              let downloadCount = 0;
              
              for (const recording of concert.recordings) {
                if (recording.tracks) {
                  for (const track of recording.tracks) {
                    if (track.file_format && ['flac', 'mp3', 'ogg', 'wav', 'm4a'].includes(track.file_format.toLowerCase())) {
                      await startDownload({
                        archive_identifier: recording.archive_identifier,
                        filename: track.filename,
                        track_title: track.title,
                      });
                      downloadCount++;
                    }
                  }
                }
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

  const renderRecordingItem = ({ item }: { item: ConcertRecording }) => {
    return (
      <TouchableOpacity
        style={styles.recordingCard}
        onPress={() => handleRecordingPress(item)}
        activeOpacity={0.7}
      >
        <View style={styles.recordingHeader}>
          <View style={styles.recordingInfo}>
            <Text style={styles.recordingTitle} numberOfLines={2}>
              {item.title || `Recording ${item.archive_identifier}`}
            </Text>
            <Text style={styles.recordingId}>{item.archive_identifier}</Text>
          </View>
                      <Icon name="chevron-right" size={20} color="#ccc" />
        </View>

        <View style={styles.recordingStats}>
          <View style={styles.statItem}>
            <Icon name="music-note" size={14} color="#6200ee" />
            <Text style={styles.statText}>{item.total_tracks} tracks</Text>
          </View>
          <View style={styles.statItem}>
            <Icon name="storage" size={14} color="#6200ee" />
            <Text style={styles.statText}>{formatFileSize(item.total_size)}</Text>
          </View>
          <View style={styles.statItem}>
            <Icon name="download" size={14} color="#6200ee" />
            <Text style={styles.statText}>{item.downloads} downloads</Text>
          </View>
        </View>

        {item.description && (
          <Text style={styles.recordingDescription} numberOfLines={2}>
            {item.description}
          </Text>
        )}

        {item.taper && (
          <Text style={styles.taperInfo}>Taper: {item.taper}</Text>
        )}
      </TouchableOpacity>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6200ee" />
        <Text style={styles.loadingText}>Loading concert details...</Text>
      </View>
    );
  }

  if (!concert) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="error" size={64} color="#ccc" />
        <Text style={styles.errorTitle}>Concert Not Found</Text>
        <Text style={styles.errorSubtitle}>
          The requested concert could not be loaded
        </Text>
      </View>
    );
  }

  const concertDate = parseISO(concert.date);
  const formattedDate = format(concertDate, 'EEEE, MMMM dd, yyyy');

  return (
    <View style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Concert Header */}
        <View style={styles.header}>
          <Text style={styles.artistName}>{concert.artist}</Text>
          <Text style={styles.concertDate}>{formattedDate}</Text>
          {concert.venue && (
            <View style={styles.venueContainer}>
              <Icon name="location-on" size={16} color="#666" />
              <Text style={styles.venueText}>{concert.venue}</Text>
            </View>
          )}
          {concert.location && (
            <Text style={styles.locationText}>{concert.location}</Text>
          )}
        </View>

        {/* Concert Stats */}
        <View style={styles.statsSection}>
          <View style={styles.statCard}>
            <Icon name="album" size={24} color="#6200ee" />
            <Text style={styles.statNumber}>{concert.total_recordings}</Text>
            <Text style={styles.statLabel}>Recordings</Text>
          </View>
          <View style={styles.statCard}>
            <Icon name="music-note" size={24} color="#6200ee" />
            <Text style={styles.statNumber}>{concert.total_tracks}</Text>
            <Text style={styles.statLabel}>Tracks</Text>
          </View>
          <View style={styles.statCard}>
            <Icon name="storage" size={24} color="#6200ee" />
            <Text style={styles.statNumber}>{formatFileSize(concert.total_size)}</Text>
            <Text style={styles.statLabel}>Total Size</Text>
          </View>
        </View>

        {/* Concert Description */}
        {concert.description && (
          <View style={styles.descriptionSection}>
            <Text style={styles.sectionTitle}>Description</Text>
            <Text style={styles.descriptionText}>{concert.description}</Text>
          </View>
        )}

        {/* Source Information */}
        {(concert.source || concert.taper || concert.lineage) && (
          <View style={styles.sourceSection}>
            <Text style={styles.sectionTitle}>Recording Information</Text>
            {concert.source && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Source:</Text>
                <Text style={styles.infoValue}>{concert.source}</Text>
              </View>
            )}
            {concert.taper && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Taper:</Text>
                <Text style={styles.infoValue}>{concert.taper}</Text>
              </View>
            )}
            {concert.lineage && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Lineage:</Text>
                <Text style={styles.infoValue}>{concert.lineage}</Text>
              </View>
            )}
          </View>
        )}

        {/* Download All Button */}
        <View style={styles.downloadSection}>
          <TouchableOpacity
            style={styles.downloadAllButton}
            onPress={handleDownloadAllAudio}
          >
            <Icon name="download" size={20} color="#fff" />
            <Text style={styles.downloadAllText}>Download All Audio Files</Text>
          </TouchableOpacity>
        </View>

        {/* Recordings List */}
        <View style={styles.recordingsSection}>
          <Text style={styles.sectionTitle}>Recordings ({concert.recordings.length})</Text>
          {concert.recordings.map((recording) => (
            <View key={recording.id || recording.archive_identifier}>
              {renderRecordingItem({ item: recording })}
            </View>
          ))}
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
  artistName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  concertDate: {
    fontSize: 18,
    color: '#666',
    marginBottom: 8,
  },
  venueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  venueText: {
    fontSize: 16,
    color: '#666',
    marginLeft: 4,
  },
  locationText: {
    fontSize: 14,
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
    fontSize: 20,
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
  downloadSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 10,
  },
  downloadAllButton: {
    backgroundColor: '#6200ee',
    borderRadius: 8,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  downloadAllText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  recordingsSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 20,
  },
  recordingCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  recordingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  recordingInfo: {
    flex: 1,
    marginRight: 12,
  },
  recordingTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  recordingId: {
    fontSize: 12,
    color: '#999',
    fontFamily: 'monospace',
  },
  recordingStats: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  statText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  recordingDescription: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
    marginBottom: 8,
  },
  taperInfo: {
    fontSize: 11,
    color: '#999',
    fontStyle: 'italic',
  },
});

export default ConcertDetailScreen;
