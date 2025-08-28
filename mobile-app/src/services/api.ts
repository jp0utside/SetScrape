import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  UserSession,
  ArchiveSearchResponse,
  ConcertSearchResponse,
  DownloadResponse,
  DownloadCreate,
  DirectoryResponse,
  StatsResponse,
} from '../types/api';

// const API_BASE_URL = 'http://10.0.2.2:8000'; // For Android emulator
const API_BASE_URL = 'http://localhost:8000'; // For iOS simulator
// const API_BASE_URL = 'http://192.168.1.100:8000'; // For physical device

class ApiService {
  private api: AxiosInstance;
  private token: string | null = null;
  private onTokenExpired: (() => void) | null = null;

  setTokenExpiredCallback(callback: () => void) {
    this.onTokenExpired = callback;
  }

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      async (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle auth errors
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid - clear token without logout request
          await this.clearToken();
          // Notify the auth context
          if (this.onTokenExpired) {
            this.onTokenExpired();
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication methods
  async login(username: string, password: string): Promise<UserSession> {
    try {
      // Clear any existing token before login to prevent conflicts
      this.token = null;
      
      const response: AxiosResponse<UserSession> = await this.api.post('/auth/login', {
        username,
        password,
      });
      
      this.token = response.data.session_token;
      await AsyncStorage.setItem('authToken', this.token);
      await AsyncStorage.setItem('userData', JSON.stringify(response.data.user));
      
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async logout(): Promise<void> {
    try {
      if (this.token) {
        await this.api.post('/auth/logout');
      }
    } catch (error) {
      // Ignore logout errors
    } finally {
      this.token = null;
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('userData');
    }
  }

  async clearToken(): Promise<void> {
    // Clear token without making a logout request (for token expiration)
    this.token = null;
    await AsyncStorage.removeItem('authToken');
    await AsyncStorage.removeItem('userData');
  }

  async getStoredToken(): Promise<string | null> {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (token) {
        this.token = token;
      }
      return token;
    } catch (error) {
      return null;
    }
  }

  async validateToken(): Promise<boolean> {
    try {
      const token = await this.getStoredToken();
      if (!token) {
        return false;
      }

      // Try to make a request that requires authentication
      const response = await this.api.get('/stats');
      return response.status === 200;
    } catch (error) {
      // If we get a 401, the token is invalid
      if (error.response?.status === 401) {
        await this.clearToken();
        return false;
      }
      // For other errors, we'll assume the token is still valid
      return true;
    }
  }

  // Music browsing methods
  async browseMusic(params: {
    query?: string;
    date_range?: string;
    artist?: string;
    venue?: string;
    page?: number;
    per_page?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }): Promise<ArchiveSearchResponse> {
    try {
      const response: AxiosResponse<ArchiveSearchResponse> = await this.api.get('/music/browse', {
        params,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getItemDetails(identifier: string): Promise<any> {
    try {
      const response = await this.api.get(`/music/item/${identifier}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getDirectoryStructure(identifier: string): Promise<DirectoryResponse> {
    try {
      const response: AxiosResponse<DirectoryResponse> = await this.api.get(`/music/directory/${identifier}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Concert aggregation methods
  async browseConcerts(params: {
    query?: string;
    date_range?: string;
    page?: number;
    per_page?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    filter_by_concert_date?: boolean;
  }): Promise<ConcertSearchResponse> {
    try {
      const response: AxiosResponse<ConcertSearchResponse> = await this.api.get('/concerts', {
        params,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getConcertDetails(concertKey: string): Promise<any> {
    try {
      const response = await this.api.get(`/concerts/${concertKey}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Download methods
  async startDownload(downloadData: DownloadCreate): Promise<DownloadResponse> {
    try {
      const response: AxiosResponse<DownloadResponse> = await this.api.post('/downloads', downloadData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getDownloads(): Promise<DownloadResponse[]> {
    try {
      const response: AxiosResponse<DownloadResponse[]> = await this.api.get('/downloads');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getDownload(downloadId: string): Promise<DownloadResponse> {
    try {
      const response: AxiosResponse<DownloadResponse> = await this.api.get(`/downloads/${downloadId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async cancelDownload(downloadId: string): Promise<void> {
    try {
      await this.api.delete(`/downloads/${downloadId}`);
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async downloadFile(downloadId: string): Promise<Blob> {
    try {
      const response = await this.api.get(`/downloads/${downloadId}/file`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Stats and system methods
  async getStats(): Promise<StatsResponse> {
    try {
      const response: AxiosResponse<StatsResponse> = await this.api.get('/stats');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async healthCheck(): Promise<any> {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Error handling
  private handleError(error: any): Error {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'Server error';
      
      // Add specific handling for auth errors
      if (error.response.status === 401) {
        return new Error('token has expired');
      }
      
      return new Error(message);
    } else if (error.request) {
      // Network error - check if it's a timeout
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        return new Error('Request timed out. Please try again.');
      }
      return new Error('Network error. Please check your connection.');
    } else {
      // Other error
      return new Error(error.message || 'An unexpected error occurred');
    }
  }
}

export default new ApiService();
