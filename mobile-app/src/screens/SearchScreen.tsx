import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../types/navigation';
import { ArchiveItem } from '../types/api';
import apiService from '../services/api';
import Icon from '../components/Icon';
import { format, parseISO } from 'date-fns';

type SearchScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Main'>;

const SearchScreen: React.FC = () => {
  const [recordings, setRecordings] = useState<ArchiveItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDateRange, setSelectedDateRange] = useState('all');
  const [isSearching, setIsSearching] = useState(false);

  const navigation = useNavigation<SearchScreenNavigationProp>();

  const dateRangeOptions = [
    { label: 'All Time', value: 'all' },
    { label: 'Past Week', value: '7d' },
    { label: 'Past Month', value: '30d' },
    { label: 'Past 3 Months', value: '90d' },
    { label: 'Past Year', value: '1y' },
  ];

  const loadRecordings = async (refresh = false) => {
    try {
      setIsSearching(true);
      const currentPage = refresh ? 1 : page;
      
      const params: any = {
        page: currentPage,
        per_page: 20,
        sort_by: 'relevance',
        sort_order: 'desc', // Relevance order (sort_order ignored for relevance)
      };

      if (searchQuery.trim()) {
        params.query = searchQuery.trim();
      }

      if (selectedDateRange !== 'all') {
        params.date_range = selectedDateRange;
      }

      const response = await apiService.browseMusic(params);

      if (refresh) {
        setRecordings(response.results);
        setPage(1);
      } else {
        setRecordings(prev => [...prev, ...response.results]);
        setPage(currentPage + 1);
      }

      setHasMore(response.page < response.total_pages);
    } catch (error) {
      console.error('Error loading recordings:', error);
      Alert.alert('Error', 'Failed to load recordings');
    } finally {
      setIsSearching(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadRecordings(true);
    setIsRefreshing(false);
  };

  const handleLoadMore = () => {
    if (hasMore && !isLoading && !isSearching) {
      loadRecordings();
    }
  };

  const handleSearch = () => {
    loadRecordings(true);
  };

  const handleRecordingPress = (recording: ArchiveItem) => {
    navigation.navigate('RecordingDetail', {
      identifier: recording.identifier,
      recording,
    });
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const renderRecordingCard = ({ item }: { item: ArchiveItem }) => {
    const recordingDate = item.date ? parseISO(item.date) : null;
    const formattedDate = recordingDate ? format(recordingDate, 'MMM dd, yyyy') : 'Unknown Date';

    return (
      <TouchableOpacity
        style={styles.recordingCard}
        onPress={() => handleRecordingPress(item)}
        activeOpacity={0.7}
      >
        <View style={styles.cardHeader}>
          <View style={styles.titleContainer}>
            <Text style={styles.recordingTitle} numberOfLines={2}>
              {item.title}
            </Text>
            {item.artist && (
              <Text style={styles.artistName} numberOfLines={1}>
                {item.artist}
              </Text>
            )}
          </View>
          <View style={styles.dateContainer}>
            <Icon name="event" size={14} color="#666" />
            <Text style={styles.dateText}>{formattedDate}</Text>
          </View>
        </View>

        <View style={styles.cardContent}>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Icon name="music-note" size={14} color="#6200ee" />
              <Text style={styles.statText}>{item.total_tracks} tracks</Text>
            </View>
            <View style={styles.statItem}>
              <Icon name="storage" size={14} color="#6200ee" />
              <Text style={styles.statText}>{formatFileSize(item.total_size)}</Text>
            </View>
          </View>

          {item.venue && (
            <View style={styles.venueContainer}>
              <Icon name="location-on" size={14} color="#666" />
              <Text style={styles.venueText} numberOfLines={1}>
                {item.venue}
              </Text>
            </View>
          )}

          {item.description && (
            <Text style={styles.description} numberOfLines={2}>
              {item.description}
            </Text>
          )}
        </View>

        <View style={styles.cardFooter}>
          <View style={styles.sourceInfo}>
            {item.taper && (
              <Text style={styles.sourceText}>Taper: {item.taper}</Text>
            )}
            {item.source && (
              <Text style={styles.sourceText}>Source: {item.source}</Text>
            )}
          </View>
                      <Icon name="chevron-right" size={18} color="#ccc" />
        </View>
      </TouchableOpacity>
    );
  };

  const renderDateRangeFilter = () => (
    <View style={styles.filterContainer}>
      <Text style={styles.filterLabel}>Time Period:</Text>
      <View style={styles.filterButtons}>
        {dateRangeOptions.map((option) => (
          <TouchableOpacity
            key={option.value}
            style={[
              styles.filterButton,
              selectedDateRange === option.value && styles.filterButtonActive,
            ]}
            onPress={() => {
              setSelectedDateRange(option.value);
              loadRecordings(true);
            }}
          >
            <Text
              style={[
                styles.filterButtonText,
                selectedDateRange === option.value && styles.filterButtonTextActive,
              ]}
            >
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const renderFooter = () => {
    if (!hasMore && recordings.length > 0) {
      return (
        <View style={styles.footerContainer}>
          <Text style={styles.footerText}>No more recordings to load</Text>
        </View>
      );
    }
    return null;
  };

  useEffect(() => {
    loadRecordings(true);
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.searchContainer}>
        <View style={styles.searchInputContainer}>
          <Icon name="search" size={20} color="#666" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search recordings, artists, venues..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity
              style={styles.clearButton}
              onPress={() => {
                setSearchQuery('');
                loadRecordings(true);
              }}
            >
              <Icon name="clear" size={20} color="#666" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {renderDateRangeFilter()}

      <FlatList
        data={recordings}
        renderItem={renderRecordingCard}
        keyExtractor={(item) => item.identifier}
        contentContainerStyle={styles.listContainer}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            colors={['#6200ee']}
            tintColor="#6200ee"
          />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.1}
        ListFooterComponent={renderFooter}
        showsVerticalScrollIndicator={false}
      />

      {isSearching && (
        <View style={styles.searchingOverlay}>
          <ActivityIndicator size="large" color="#6200ee" />
          <Text style={styles.searchingText}>Searching...</Text>
        </View>
      )}

      {recordings.length === 0 && !isLoading && !isSearching && (
        <View style={styles.emptyContainer}>
          <Icon name="search-off" size={64} color="#ccc" />
          <Text style={styles.emptyTitle}>No Recordings Found</Text>
          <Text style={styles.emptySubtitle}>
            Try adjusting your search terms or date range
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  searchContainer: {
    padding: 20,
    paddingBottom: 10,
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  searchIcon: {
    marginLeft: 12,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    fontSize: 16,
    color: '#333',
  },
  clearButton: {
    padding: 8,
    marginRight: 8,
  },
  filterContainer: {
    paddingHorizontal: 20,
    paddingBottom: 10,
  },
  filterLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  filterButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  filterButtonActive: {
    backgroundColor: '#6200ee',
    borderColor: '#6200ee',
  },
  filterButtonText: {
    fontSize: 12,
    color: '#666',
  },
  filterButtonTextActive: {
    color: '#fff',
  },
  listContainer: {
    padding: 20,
    paddingTop: 10,
  },
  recordingCard: {
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
  titleContainer: {
    flex: 1,
    marginRight: 12,
  },
  recordingTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  artistName: {
    fontSize: 14,
    color: '#666',
  },
  dateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dateText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  cardContent: {
    marginBottom: 12,
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
  venueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  venueText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
    flex: 1,
  },
  description: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  sourceInfo: {
    flex: 1,
  },
  sourceText: {
    fontSize: 10,
    color: '#999',
  },
  footerContainer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#666',
  },
  searchingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
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
});

export default SearchScreen;
