import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Modal,
} from 'react-native';
import { useDownloads } from '../contexts/DownloadContext';
import Icon from '../components/Icon';
import { format, parseISO } from 'date-fns';
import ProgressBar from '../components/ProgressBar';

const DownloadsScreen: React.FC = () => {
  const { downloads, isLoading, refreshDownloads, cancelDownload, downloadFile } = useDownloads();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedDownload, setSelectedDownload] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshDownloads();
    setIsRefreshing(false);
  };

  const handleCancelDownload = async (downloadId: string) => {
    Alert.alert(
      'Cancel Download',
      'Are you sure you want to cancel this download?',
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Yes',
          style: 'destructive',
          onPress: async () => {
            try {
              await cancelDownload(downloadId);
            } catch (error) {
              Alert.alert('Error', 'Failed to cancel download');
            }
          },
        },
      ]
    );
  };

  const handleDownloadFile = async (downloadId: string) => {
    try {
      await downloadFile(downloadId);
      // The success message is now handled in the DownloadContext
    } catch (error) {
      Alert.alert('Error', 'Failed to download file');
    }
  };

  const handleShowDetails = (download: any) => {
    setSelectedDownload(download);
    setShowModal(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#4caf50';
      case 'downloading':
        return '#2196f3';
      case 'pending':
        return '#ff9800';
      case 'failed':
        return '#f44336';
      default:
        return '#666';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return 'check-circle';
      case 'downloading':
        return 'download';
      case 'pending':
        return 'schedule';
      case 'failed':
        return 'error';
      default:
        return 'help';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const renderDownloadItem = ({ item }: { item: any }) => {
    const statusColor = getStatusColor(item.status);
    const statusIcon = getStatusIcon(item.status);
    const createdDate = parseISO(item.created_at);
    const formattedDate = format(createdDate, 'MMM dd, HH:mm');

    return (
      <View style={styles.downloadCard}>
        <View style={styles.cardHeader}>
          <View style={styles.fileInfo}>
            <Text style={styles.filename} numberOfLines={1}>
              {item.filename}
            </Text>
            {item.track_title && (
              <Text style={styles.trackTitle} numberOfLines={1}>
                {item.track_title}
              </Text>
            )}
          </View>
          <View style={styles.statusContainer}>
            <Icon name={statusIcon} size={20} color={statusColor} />
            <Text style={[styles.statusText, { color: statusColor }]}>
              {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
            </Text>
          </View>
        </View>

        <View style={styles.cardContent}>
          <View style={styles.progressContainer}>
            <ProgressBar
              progress={item.progress / 100}
              width={null}
              height={6}
              color={statusColor}
              unfilledColor="#e0e0e0"
              borderWidth={0}
            />
            <Text style={styles.progressText}>{Math.round(item.progress)}%</Text>
          </View>

          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Icon name="storage" size={14} color="#666" />
              <Text style={styles.statText}>
                {item.file_size ? formatFileSize(item.file_size) : 'Unknown size'}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Icon name="schedule" size={14} color="#666" />
              <Text style={styles.statText}>{formattedDate}</Text>
            </View>
          </View>

          {item.error_message && (
            <Text style={styles.errorText} numberOfLines={2}>
              Error: {item.error_message}
            </Text>
          )}
        </View>

        <View style={styles.cardActions}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => handleShowDetails(item)}
          >
            <Icon name="info" size={16} color="#666" />
            <Text style={styles.actionText}>Details</Text>
          </TouchableOpacity>

          {item.status === 'completed' && (
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => handleDownloadFile(item.id)}
            >
              <Icon name="file-download" size={16} color="#6200ee" />
              <Text style={[styles.actionText, { color: '#6200ee' }]}>Save</Text>
            </TouchableOpacity>
          )}

          {(item.status === 'pending' || item.status === 'downloading') && (
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => handleCancelDownload(item.id)}
            >
              <Icon name="cancel" size={16} color="#f44336" />
              <Text style={[styles.actionText, { color: '#f44336' }]}>Cancel</Text>
            </TouchableOpacity>
          )}

          {item.status === 'failed' && (
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => handleShowDetails(item)}
            >
              <Icon name="refresh" size={16} color="#ff9800" />
              <Text style={[styles.actionText, { color: '#ff9800' }]}>Retry</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  };

  const renderDownloadDetails = () => (
    <Modal
      visible={showModal}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setShowModal(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Download Details</Text>
            <TouchableOpacity onPress={() => setShowModal(false)}>
              <Icon name="close" size={24} color="#666" />
            </TouchableOpacity>
          </View>

          {selectedDownload && (
            <View style={styles.detailsContent}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Filename:</Text>
                <Text style={styles.detailValue}>{selectedDownload.filename}</Text>
              </View>

              {selectedDownload.track_title && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Track:</Text>
                  <Text style={styles.detailValue}>{selectedDownload.track_title}</Text>
                </View>
              )}

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Status:</Text>
                <Text style={[styles.detailValue, { color: getStatusColor(selectedDownload.status) }]}>
                  {selectedDownload.status.charAt(0).toUpperCase() + selectedDownload.status.slice(1)}
                </Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Progress:</Text>
                <Text style={styles.detailValue}>{Math.round(selectedDownload.progress)}%</Text>
              </View>

              {selectedDownload.file_size && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Size:</Text>
                  <Text style={styles.detailValue}>{formatFileSize(selectedDownload.file_size)}</Text>
                </View>
              )}

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Created:</Text>
                <Text style={styles.detailValue}>
                  {format(parseISO(selectedDownload.created_at), 'MMM dd, yyyy HH:mm')}
                </Text>
              </View>

              {selectedDownload.started_at && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Started:</Text>
                  <Text style={styles.detailValue}>
                    {format(parseISO(selectedDownload.started_at), 'MMM dd, yyyy HH:mm')}
                  </Text>
                </View>
              )}

              {selectedDownload.download_completed_at && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Completed:</Text>
                  <Text style={styles.detailValue}>
                    {format(parseISO(selectedDownload.download_completed_at), 'MMM dd, yyyy HH:mm')}
                  </Text>
                </View>
              )}

              {selectedDownload.error_message && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Error:</Text>
                  <Text style={[styles.detailValue, { color: '#f44336' }]}>
                    {selectedDownload.error_message}
                  </Text>
                </View>
              )}

              {selectedDownload.file_path && selectedDownload.status === 'completed' && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>File Location:</Text>
                  <Text style={styles.detailValue} numberOfLines={3}>
                    {selectedDownload.file_path}
                  </Text>
                </View>
              )}
            </View>
          )}

          <TouchableOpacity
            style={styles.modalButton}
            onPress={() => setShowModal(false)}
          >
            <Text style={styles.modalButtonText}>Close</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  const getStatusCounts = () => {
    const counts = {
      completed: 0,
      downloading: 0,
      pending: 0,
      failed: 0,
    };

    downloads.forEach(download => {
      counts[download.status as keyof typeof counts]++;
    });

    return counts;
  };

  const statusCounts = getStatusCounts();

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Downloads</Text>
        <Text style={styles.headerSubtitle}>Manage your music downloads</Text>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Icon name="check-circle" size={20} color="#4caf50" />
          <Text style={styles.statNumber}>{statusCounts.completed}</Text>
          <Text style={styles.statLabel}>Completed</Text>
        </View>
        <View style={styles.statCard}>
          <Icon name="download" size={20} color="#2196f3" />
          <Text style={styles.statNumber}>{statusCounts.downloading}</Text>
          <Text style={styles.statLabel}>Downloading</Text>
        </View>
        <View style={styles.statCard}>
          <Icon name="schedule" size={20} color="#ff9800" />
          <Text style={styles.statNumber}>{statusCounts.pending}</Text>
          <Text style={styles.statLabel}>Pending</Text>
        </View>
        <View style={styles.statCard}>
          <Icon name="error" size={20} color="#f44336" />
          <Text style={styles.statNumber}>{statusCounts.failed}</Text>
          <Text style={styles.statLabel}>Failed</Text>
        </View>
      </View>

      <FlatList
        data={downloads}
        renderItem={renderDownloadItem}
        keyExtractor={(item) => item.id || `${item.archive_identifier}-${item.filename}`}
        contentContainerStyle={styles.listContainer}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            colors={['#6200ee']}
            tintColor="#6200ee"
          />
        }
        showsVerticalScrollIndicator={false}
      />

      {downloads.length === 0 && !isLoading && (
        <View style={styles.emptyContainer}>
          <Icon name="download-done" size={64} color="#ccc" />
          <Text style={styles.emptyTitle}>No Downloads</Text>
          <Text style={styles.emptySubtitle}>
            Start downloading music from the Search tab
          </Text>
        </View>
      )}

      {renderDownloadDetails()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    paddingBottom: 10,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingBottom: 10,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    marginHorizontal: 4,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  statNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  listContainer: {
    padding: 20,
    paddingTop: 10,
  },
  downloadCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  fileInfo: {
    flex: 1,
    marginRight: 12,
  },
  filename: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  trackTitle: {
    fontSize: 14,
    color: '#666',
  },
  statusContainer: {
    alignItems: 'center',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: 2,
  },
  cardContent: {
    marginBottom: 12,
  },
  progressContainer: {
    marginBottom: 12,
  },
  progressText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 4,
  },
  statsRow: {
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
  errorText: {
    fontSize: 12,
    color: '#f44336',
    fontStyle: 'italic',
  },
  cardActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
  },
  actionText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    margin: 20,
    maxWidth: 400,
    width: '100%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  detailsContent: {
    marginBottom: 20,
  },
  detailRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  detailLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    width: 80,
  },
  detailValue: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  modalButton: {
    backgroundColor: '#6200ee',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  modalButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default DownloadsScreen;
