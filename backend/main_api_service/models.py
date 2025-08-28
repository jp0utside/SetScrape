# Import SQLAlchemy models from shared
from shared.database_models import (
    User, IndexedMusic, Download, UserLibrary, Playlist, 
    PlaylistTrack, UserSession, SearchHistory, BackgroundJob
)

# Re-export for convenience
__all__ = [
    'User', 'IndexedMusic', 'Download', 'UserLibrary', 'Playlist', 
    'PlaylistTrack', 'UserSession', 'SearchHistory', 'BackgroundJob'
]
