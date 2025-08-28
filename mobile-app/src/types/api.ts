export interface User {
  id: string;
  username: string;
  email?: string;
  created_at: string;
  is_active: boolean;
  storage_provider: string;
}

export interface UserSession {
  session_token: string;
  user: User;
  expires_at?: string;
}

export interface ArchiveTrack {
  track_number?: number;
  title: string;
  filename: string;
  file_format?: string;
  file_size?: number;
  duration?: number;
  download_url?: string;
}

export interface ArchiveItem {
  identifier: string;
  title: string;
  artist?: string;
  date?: string;
  venue?: string;
  location?: string;
  description?: string;
  source?: string;
  taper?: string;
  lineage?: string;
  total_tracks: number;
  total_size: number;
  tracks?: ArchiveTrack[];
  downloads: number;
}

export interface ArchiveSearchResponse {
  success: boolean;
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  results: ArchiveItem[];
}

export interface ConcertRecording {
  id: string;
  archive_identifier: string;
  title?: string;
  description?: string;
  source?: string;
  taper?: string;
  lineage?: string;
  total_tracks: number;
  total_size: number;
  tracks?: ArchiveTrack[];
  downloads: number;
  created_at: string;
}

export interface AggregatedConcert {
  id: string;
  concert_key: string;
  artist: string;
  date: string;
  venue?: string;
  location?: string;
  title?: string;
  description?: string;
  source?: string;
  taper?: string;
  lineage?: string;
  total_recordings: number;
  total_tracks: number;
  total_size: number;
  total_downloads: number;
  recordings: ConcertRecording[];
  indexed_at: string;
  last_updated: string;
}

export interface ConcertSearchResponse {
  success: boolean;
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  results: AggregatedConcert[];
}

export interface DownloadCreate {
  archive_identifier: string;
  filename: string;
  track_title?: string;
}

export interface DownloadResponse {
  id: string;
  user_id: string;
  archive_identifier: string;
  filename: string;
  track_title?: string;
  status: 'pending' | 'downloading' | 'completed' | 'failed';
  progress: number;
  file_path?: string;
  file_size?: number;
  download_url?: string;
  started_at?: string;
  download_completed_at?: string;
  error_message?: string;
  created_at: string;
}

export interface DirectoryFile {
  name: string;
  size: number;
  type: 'audio' | 'image' | 'metadata' | 'other';
  format?: string;
  download_url?: string;
}

export interface DirectoryResponse {
  identifier: string;
  title: string;
  files: DirectoryFile[];
  audio_files: DirectoryFile[];
  image_files: DirectoryFile[];
  metadata_files: DirectoryFile[];
  other_files: DirectoryFile[];
  total_files: number;
  total_size: number;
}

export interface StatsResponse {
  total_users: number;
  total_downloads: number;
  total_concerts: number;
  total_recordings: number;
  cache_stats: Record<string, any>;
  download_stats: Record<string, any>;
}
