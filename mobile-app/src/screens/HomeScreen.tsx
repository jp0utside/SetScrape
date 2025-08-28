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
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../types/navigation';
import { AggregatedConcert } from '../types/api';
import apiService from '../services/api';
import Icon from '../components/Icon';
import { format, parseISO } from 'date-fns';

type HomeScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Main'>;

const HomeScreen: React.FC = () => {
  const [concerts, setConcerts] = useState<AggregatedConcert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);

  const navigation = useNavigation<HomeScreenNavigationProp>();

  const loadConcerts = async (refresh = false) => {
    try {
      const currentPage = refresh ? 1 : page;
      const response = await apiService.browseConcerts({
        date_range: '7d', // Past week
        page: currentPage,
        per_page: 20,
        sort_by: 'date',
        sort_order: 'desc', // Most recent first
        filter_by_concert_date: true, // Filter by actual concert date, not upload date
      });

      if (refresh) {
        setConcerts(response.results);
        setPage(1);
      } else {
        setConcerts(prev => [...prev, ...response.results]);
        setPage(currentPage + 1);
      }

      setHasMore(response.page < response.total_pages);
    } catch (error) {
      console.error('Error loading concerts:', error);
      Alert.alert('Error', 'Failed to load recent concerts');
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadConcerts(true);
    setIsRefreshing(false);
  };

  const handleLoadMore = () => {
    if (hasMore && !isLoading) {
      loadConcerts();
    }
  };

  const handleConcertPress = (concert: AggregatedConcert) => {
    navigation.navigate('ConcertDetail', {
      concertKey: concert.concert_key,
      concert,
    });
  };

  const renderConcertCard = ({ item }: { item: AggregatedConcert }) => {
    const concertDate = parseISO(item.date);
    const formattedDate = format(concertDate, 'MMM dd, yyyy');

    // Parse the title which is now in format "ARTIST-VENUE-LOCATION" (venue may be omitted)
    const titleParts = item.title?.split('-') || [];
    const displayArtist = titleParts[0] || item.artist;
    
    // Handle different title formats:
    // - "ARTIST" (no venue/location)
    // - "ARTIST-VENUE" (venue only)
    // - "ARTIST-LOCATION" (location only, no venue)
    // - "ARTIST-VENUE-LOCATION" (both venue and location)
    let displayVenue = '';
    if (titleParts.length === 2) {
      // Could be "ARTIST-VENUE" or "ARTIST-LOCATION"
      // Use the venue from the data if available, otherwise show the second part
      displayVenue = item.venue && item.venue !== 'Unknown Venue' ? item.venue : titleParts[1];
    } else if (titleParts.length >= 3) {
      // "ARTIST-VENUE-LOCATION" format
      displayVenue = titleParts[1]; // Second part is venue
    }
    
    // Fallback to venue from data if title parsing didn't work
    if (!displayVenue || displayVenue === 'Unknown Venue') {
      displayVenue = item.venue && item.venue !== 'Unknown Venue' ? item.venue : '';
    }

    return (
      <TouchableOpacity
        style={styles.concertCard}
        onPress={() => handleConcertPress(item)}
        activeOpacity={0.7}
      >
        <View style={styles.cardHeader}>
          <View style={styles.artistInfo}>
            <Text style={styles.artistName} numberOfLines={1}>
              {displayArtist}
            </Text>
            <Text style={styles.venueName} numberOfLines={1}>
              {displayVenue}
            </Text>
          </View>
          <View style={styles.dateContainer}>
            <Icon name="event" size={16} color="#666" />
            <Text style={styles.dateText}>{formattedDate}</Text>
          </View>
        </View>

        <View style={styles.cardContent}>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Icon name="album" size={16} color="#6200ee" />
              <Text style={styles.statText}>{item.total_recordings} recordings</Text>
            </View>
            <View style={styles.statItem}>
              <Icon name="music-note" size={16} color="#6200ee" />
              <Text style={styles.statText}>{item.total_tracks} tracks</Text>
            </View>
            <View style={styles.statItem}>
              <Icon name="download" size={16} color="#6200ee" />
              <Text style={styles.statText}>{item.total_downloads} downloads</Text>
            </View>
          </View>

          {item.description && (
            <Text style={styles.description} numberOfLines={2}>
              {item.description}
            </Text>
          )}
        </View>

        <View style={styles.cardFooter}>
          <View style={styles.sourceInfo}>
            <Text style={styles.sourceText}>
              {item.total_recordings} distinct uploads available
            </Text>
          </View>
          <Icon name="chevron-right" size={20} color="#ccc" />
        </View>
      </TouchableOpacity>
    );
  };

  const renderFooter = () => {
    if (!hasMore) {
      return (
        <View style={styles.footerContainer}>
          <Text style={styles.footerText}>No more concerts to load</Text>
        </View>
      );
    }
    return null;
  };

  useEffect(() => {
    loadConcerts(true).finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6200ee" />
        <Text style={styles.loadingText}>Loading recent concerts...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Recent Concerts</Text>
        <Text style={styles.headerSubtitle}>Live music from the past week</Text>
      </View>

      <FlatList
        data={concerts}
        renderItem={renderConcertCard}
        keyExtractor={(item) => item.id || item.concert_key || `${item.artist}-${item.date}`}
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

      {concerts.length === 0 && !isLoading && (
        <View style={styles.emptyContainer}>
          <Icon name="music-off" size={64} color="#ccc" />
          <Text style={styles.emptyTitle}>No Recent Concerts</Text>
          <Text style={styles.emptySubtitle}>
            Check back later for new live music recordings
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
  listContainer: {
    padding: 20,
    paddingTop: 10,
  },
  concertCard: {
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
  artistInfo: {
    flex: 1,
    marginRight: 12,
  },
  artistName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  venueName: {
    fontSize: 14,
    color: '#666',
  },
  dateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dateText: {
    fontSize: 14,
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
    marginRight: 20,
  },
  statText: {
    fontSize: 14,
    color: '#666',
    marginLeft: 4,
  },
  description: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
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
    fontSize: 12,
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

export default HomeScreen;
