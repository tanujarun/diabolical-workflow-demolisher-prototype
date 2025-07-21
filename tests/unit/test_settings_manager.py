
"""
Unit tests for the migrated settings management system.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys
import warnings

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

warnings.filterwarnings('ignore', category=DeprecationWarning)

from dwd.state.settings.manager import (
    JSONFileBackend, MemoryBackend, SettingsManager
)


class TestStorageBackends:
    """Test storage backend implementations."""
    
    def test_memory_backend_operations(self):
        """Test memory backend basic operations."""
        backend = MemoryBackend()
        
        assert not backend.exists('test_key')
        assert backend.read('test_key') is None
        assert backend.list_keys() == []
        
        backend.write('test_key', 'test_value')
        assert backend.exists('test_key')
        assert backend.read('test_key') == 'test_value'
        
        backend.delete('test_key')
        assert not backend.exists('test_key')


class TestSettingsManager:
    """Test settings manager functionality."""
    
    def setup_method(self):
        """Set up test settings manager."""
        self.persistent_backend = MemoryBackend()
        self.transient_backend = MemoryBackend()
        self.manager = SettingsManager(self.persistent_backend, self.transient_backend)
    
    def test_setting_registration(self):
        """Test basic setting registration."""
        self.manager.register_setting('test_setting', 'default_value', persistent=True)
        assert self.manager.get('test_setting') == 'default_value'
    
    def test_persistent_storage(self):
        """Test persistent setting storage."""
        self.manager.register_setting('persistent_key', 'default', persistent=True)
        self.manager.set('persistent_key', 'new_value')
        
        assert self.persistent_backend.read('persistent_key') == 'new_value'
        assert self.manager.get('persistent_key') == 'new_value'


if __name__ == '__main__':
    pytest.main([__file__])
