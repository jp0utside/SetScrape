import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { DownloadResponse, DownloadCreate } from '../types/api';
import apiService from '../services/api';
import { useAuth } from './AuthContext';
import RNFS from 'react-native-fs';
import { Alert, Platform } from 'react-native';

interface DownloadContextType {
  downloads: DownloadResponse[];
  isLoading: boolean;
  startDownload: (downloadData: DownloadCreate) => Promise<void>;
  cancelDownload: (downloadId: string) => Promise<void>;
  refreshDownloads: () => Promise<void>;
  downloadFile: (downloadId: string) => Promise<void>;
}

const DownloadContext = createContext<DownloadContextType | undefined>(undefined);

export const useDownloads = () => {
  const context = useContext(DownloadContext);
  if (context === undefined) {
    throw new Error('useDownloads must be used within a DownloadProvider');
  }
  return context;
};

interface DownloadProviderProps {
  children: ReactNode;
}

export const DownloadProvider: React.FC<DownloadProviderProps> = ({ children }) => {
  const [downloads, setDownloads] = useState<DownloadResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { isAuthenticated } = useAuth();

  const refreshDownloads = async () => {
    if (!isAuthenticated) return;
    
    try {
      setIsLoading(true);
      const downloadList = await apiService.getDownloads();
      setDownloads(downloadList);
    } catch (error: any) {
      console.error('Error refreshing downloads:', error);
      // Don't show error alerts for auth errors - they're handled by the auth context
      if (error.message && !error.message.includes('token has expired')) {
        // Only show non-auth related errors
        console.log('Non-auth error refreshing downloads:', error.message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const startDownload = async (downloadData: DownloadCreate) => {
    if (!isAuthenticated) {
      throw new Error('User must be authenticated to start downloads');
    }

    try {
      const newDownload = await apiService.startDownload(downloadData);
      setDownloads(prev => [...prev, newDownload]);
    } catch (error) {
      console.error('Error starting download:', error);
      throw error;
    }
  };

  const cancelDownload = async (downloadId: string) => {
    try {
      await apiService.cancelDownload(downloadId);
      setDownloads(prev => 
        prev.map(download => 
          download.id === downloadId 
            ? { ...download, status: 'failed' as const }
            : download
        )
      );
    } catch (error) {
      console.error('Error cancelling download:', error);
      throw error;
    }
  };

  const downloadFile = async (downloadId: string) => {
    try {
      // Get the download details first
      const download = downloads.find(d => d.id === downloadId);
      if (!download) {
        throw new Error('Download not found');
      }

      // Get the file blob from the server
      const blob = await apiService.downloadFile(downloadId);
      
      // Determine the appropriate directory based on platform
      let baseDir = '';
      if (Platform.OS === 'ios') {
        baseDir = RNFS.DocumentDirectoryPath;
      } else {
        baseDir = RNFS.ExternalDirectoryPath;
      }
      
      // Create a Music subdirectory
      const musicDir = `${baseDir}/Music`;
      await RNFS.mkdir(musicDir).catch(() => {}); // Ignore if directory already exists
      
      // Create a subdirectory for the artist/concert
      const artistDir = `${musicDir}/${download.archive_identifier}`;
      await RNFS.mkdir(artistDir).catch(() => {}); // Ignore if directory already exists
      
      // Set the file path
      const filePath = `${artistDir}/${download.filename}`;
      
      // Convert blob to base64 and save the file
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const base64Data = (reader.result as string).split(',')[1]; // Remove data URL prefix
          await RNFS.writeFile(filePath, base64Data, 'base64');
          
          // Update the download status
          setDownloads(prev => 
            prev.map(d => 
              d.id === downloadId 
                ? { ...d, status: 'completed' as const, file_path: filePath }
                : d
            )
          );
          
          Alert.alert(
            'Download Complete',
            `File saved to: ${filePath}`,
            [
              { text: 'OK', style: 'default' },
              { text: 'Open Folder', onPress: () => {
                // On iOS, we can't open folders, but we can show the path
                Alert.alert('File Location', `File saved to:\n${filePath}`);
              }}
            ]
          );
        } catch (error) {
          console.error('Error saving file:', error);
          Alert.alert('Error', 'Failed to save file to device');
        }
      };
      
      reader.readAsDataURL(blob);
      
    } catch (error) {
      console.error('Error downloading file:', error);
      throw error;
    }
  };

  // Auto-refresh downloads when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      refreshDownloads();
      
      // Set up periodic refresh for active downloads
      const interval = setInterval(() => {
        const hasActiveDownloads = downloads.some(
          download => download.status === 'pending' || download.status === 'downloading'
        );
        if (hasActiveDownloads) {
          refreshDownloads();
        }
      }, 3000); // Refresh every 3 seconds if there are active downloads

      return () => clearInterval(interval);
    }
  }, [isAuthenticated, downloads.length]); // Re-trigger when downloads array length changes

  const value: DownloadContextType = {
    downloads,
    isLoading,
    startDownload,
    cancelDownload,
    refreshDownloads,
    downloadFile,
  };

  return (
    <DownloadContext.Provider value={value}>
      {children}
    </DownloadContext.Provider>
  );
};
