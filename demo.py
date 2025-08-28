#!/usr/bin/env python3
"""
Music Player Backend Demo Script

This script demonstrates all the backend features:
- User authentication
- Music search and discovery
- Download management
- Library management
- Playlist creation
- Background processing
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://127.0.0.1:8000"
SCRAPING_URL = "http://127.0.0.1:8001"
DOWNLOAD_URL = "http://127.0.0.1:8002"

class MusicPlayerDemo:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.auth_token = None
        self.user_id = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def print_section(self, title: str):
        """Print a section header"""
        print(f"\n{'='*60}")
        print(f"🎵 {title}")
        print(f"{'='*60}")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    async def check_services(self):
        """Check if all services are running"""
        self.print_section("Service Health Check")
        
        services = [
            ("Main API", f"{BASE_URL}/health"),
            ("Scraping Service", f"{SCRAPING_URL}/health"),
            ("Download Service", f"{DOWNLOAD_URL}/health")
        ]
        
        for name, url in services:
            try:
                response = await self.client.get(url)
                if response.status_code == 200:
                    self.print_success(f"{name} is running")
                else:
                    self.print_error(f"{name} returned status {response.status_code}")
            except Exception as e:
                self.print_error(f"{name} is not accessible: {e}")
    
    async def register_user(self, username: str, email: str, password: str):
        """Register a new user"""
        self.print_section("User Registration")
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.print_success(f"User registered: {user_data['username']}")
                return user_data
            else:
                error_data = response.json()
                self.print_error(f"Registration failed: {error_data.get('detail', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.print_error(f"Registration error: {e}")
            return None
    
    async def login_user(self, username: str, password: str):
        """Login user and get auth token"""
        self.print_section("User Authentication")
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/auth/login",
                json={
                    "username": username,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self.auth_token = auth_data["session_token"]
                self.print_success(f"Login successful for user: {username}")
                return True
            else:
                error_data = response.json()
                self.print_error(f"Login failed: {error_data.get('detail', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.print_error(f"Login error: {e}")
            return False
    
    async def search_music(self, query: str):
        """Search for music in Internet Archive"""
        self.print_section(f"Music Search: '{query}'")
        
        if not self.auth_token:
            self.print_error("Not authenticated")
            return []
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/discover/search",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={
                    "query": query,
                    "search_type": "archive",
                    "page": 1,
                    "per_page": 10
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                self.print_success(f"Found {len(results)} results")
                
                for i, item in enumerate(results[:3], 1):  # Show first 3 results
                    print(f"  {i}. {item.get('title', 'Unknown')} - {item.get('artist', 'Unknown')}")
                
                return results
            else:
                error_data = response.json()
                self.print_error(f"Search failed: {error_data.get('detail', 'Unknown error')}")
                return []
                
        except Exception as e:
            self.print_error(f"Search error: {e}")
            return []
    
    async def start_download(self, music_id: str):
        """Start downloading a music file"""
        self.print_section("Download Management")
        
        if not self.auth_token:
            self.print_error("Not authenticated")
            return None
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/discover/download",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={"indexed_music_id": music_id}
            )
            
            if response.status_code == 200:
                download_data = response.json()
                self.print_success(f"Download started: {download_data.get('id', 'Unknown')}")
                return download_data
            else:
                error_data = response.json()
                self.print_error(f"Download failed: {error_data.get('detail', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.print_error(f"Download error: {e}")
            return None
    
    async def check_downloads(self):
        """Check download status"""
        self.print_section("Download Status")
        
        if not self.auth_token:
            self.print_error("Not authenticated")
            return
        
        try:
            response = await self.client.get(
                f"{BASE_URL}/downloads",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if response.status_code == 200:
                downloads = response.json()
                self.print_success(f"Found {len(downloads)} downloads")
                
                for download in downloads:
                    status = download.get("status", "unknown")
                    progress = download.get("progress", 0)
                    print(f"  - Download {download.get('id', 'Unknown')}: {status} ({progress*100:.1f}%)")
            else:
                error_data = response.json()
                self.print_error(f"Failed to get downloads: {error_data.get('detail', 'Unknown error')}")
                
        except Exception as e:
            self.print_error(f"Error checking downloads: {e}")
    
    async def create_playlist(self, name: str, description: str = ""):
        """Create a new playlist"""
        self.print_section("Playlist Management")
        
        if not self.auth_token:
            self.print_error("Not authenticated")
            return None
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/playlists",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={
                    "name": name,
                    "description": description
                }
            )
            
            if response.status_code == 200:
                playlist_data = response.json()
                self.print_success(f"Playlist created: {playlist_data.get('name', 'Unknown')}")
                return playlist_data
            else:
                error_data = response.json()
                self.print_error(f"Playlist creation failed: {error_data.get('detail', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.print_error(f"Playlist creation error: {e}")
            return None
    
    async def get_playlists(self):
        """Get user's playlists"""
        if not self.auth_token:
            self.print_error("Not authenticated")
            return []
        
        try:
            response = await self.client.get(
                f"{BASE_URL}/playlists",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if response.status_code == 200:
                playlists = response.json()
                self.print_success(f"Found {len(playlists)} playlists")
                
                for playlist in playlists:
                    print(f"  - {playlist.get('name', 'Unknown')}: {playlist.get('description', 'No description')}")
                
                return playlists
            else:
                error_data = response.json()
                self.print_error(f"Failed to get playlists: {error_data.get('detail', 'Unknown error')}")
                return []
                
        except Exception as e:
            self.print_error(f"Error getting playlists: {e}")
            return []
    
    async def get_library(self):
        """Get user's music library"""
        self.print_section("Music Library")
        
        if not self.auth_token:
            self.print_error("Not authenticated")
            return []
        
        try:
            response = await self.client.get(
                f"{BASE_URL}/library",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                library = data.get("results", [])
                self.print_success(f"Library contains {len(library)} items")
                
                for item in library[:3]:  # Show first 3 items
                    print(f"  - {item.get('title', 'Unknown')} - {item.get('artist', 'Unknown')}")
                
                return library
            else:
                error_data = response.json()
                self.print_error(f"Failed to get library: {error_data.get('detail', 'Unknown error')}")
                return []
                
        except Exception as e:
            self.print_error(f"Error getting library: {e}")
            return []
    
    async def check_background_jobs(self):
        """Check background job status"""
        self.print_section("Background Jobs")
        
        try:
            response = await self.client.get(f"{SCRAPING_URL}/jobs")
            
            if response.status_code == 200:
                jobs = response.json()
                self.print_success(f"Found {len(jobs)} background jobs")
                
                for job in jobs[:5]:  # Show first 5 jobs
                    print(f"  - Job {job.get('id', 'Unknown')}: {job.get('job_type', 'Unknown')} - {job.get('status', 'Unknown')}")
            else:
                self.print_error(f"Failed to get background jobs: {response.status_code}")
                
        except Exception as e:
            self.print_error(f"Error checking background jobs: {e}")
    
    async def get_system_stats(self):
        """Get system statistics"""
        self.print_section("System Statistics")
        
        try:
            response = await self.client.get(f"{SCRAPING_URL}/stats")
            
            if response.status_code == 200:
                stats = response.json()
                self.print_success("System statistics:")
                print(f"  - Total indexed: {stats.get('total_indexed', 0)}")
                print(f"  - Recent (24h): {stats.get('recent_indexed_24h', 0)}")
                print(f"  - Scraper running: {stats.get('scraper_status', {}).get('is_running', False)}")
            else:
                self.print_error(f"Failed to get stats: {response.status_code}")
                
        except Exception as e:
            self.print_error(f"Error getting stats: {e}")
    
    async def run_full_demo(self):
        """Run the complete demo"""
        self.print_section("Music Player Backend Demo")
        self.print_info("Starting comprehensive backend demonstration...")
        
        # 1. Check services
        await self.check_services()
        
        # 2. Register and login
        await self.register_user("demo_user", "demo@example.com", "password123")
        await self.login_user("demo_user", "password123")
        
        if not self.auth_token:
            self.print_error("Authentication failed, stopping demo")
            return
        
        # 3. Search for music
        search_results = await self.search_music("jazz")
        
        # 4. Start a download if we found results
        if search_results:
            first_result = search_results[0]
            await self.start_download(first_result.get("id"))
        
        # 5. Check download status
        await self.check_downloads()
        
        # 6. Create a playlist
        await self.create_playlist("Demo Playlist", "Created during demo")
        
        # 7. Get playlists
        await self.get_playlists()
        
        # 8. Get library
        await self.get_library()
        
        # 9. Check background jobs
        await self.check_background_jobs()
        
        # 10. Get system stats
        await self.get_system_stats()
        
        self.print_section("Demo Complete")
        self.print_success("All backend features demonstrated successfully!")
        self.print_info("You can now use the web interface at http://127.0.0.1:8000")

async def main():
    """Main demo function"""
    print("🎵 Music Player Backend Demo")
    print("This script demonstrates all backend features")
    print("Make sure all services are running: python start.py")
    print()
    
    async with MusicPlayerDemo() as demo:
        await demo.run_full_demo()

if __name__ == "__main__":
    asyncio.run(main())
