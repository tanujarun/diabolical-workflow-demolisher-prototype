"""
Tests for the settings management system.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dwd.core.settings import (
    StorageBackend, JSONFileBackend, MemoryBackend, SettingsManager,
    get_settings_manager, init_settings_manager
)
from dwd.core.settings_schema import (
    SETTINGS_SCHEMA, validate_setting, get_default_settings,
    get_persistent_settings, get_settings_by_category
)


class TestStorageBackends:
    """Test storage backend implementations."""
    
    def test_memory_backend(self):
        """Test memory backend basic operations."""
        backend = MemoryBackend()
        
        # Test initial state
        assert not backend.exists('test_key')
        assert backend.read('test_key') is None
        assert backend.list_keys() == []
        
        # Test write and read
        backend.write('test_key', 'test_value')
        assert backend.exists('test_key')
        assert backend.read('test_key') == 'test_value'
        assert 'test_key' in backend.list_keys()
        
        # Test delete
        backend.delete('test_key')
        assert not backend.exists('test_key')
        assert backend.read('test_key') is None
    
    def test_json_file_backend(self):
        """Test JSON file backend operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / 'test_settings.json'
            backend = JSONFileBackend(file_path)
            
            # Test initial state
            assert not backend.exists('test_key')
            assert backend.read('test_key') is None
            
            # Test write and persistence
            backend.write('test_key', 'test_value')
            assert backend.exists('test_key')
            assert backend.read('test_key') == 'test_value'
            
            # Test file was created
            assert file_path.exists()
            
            # Test persistence by creating new backend instance
            backend2 = JSONFileBackend(file_path)
            assert backend2.read('test_key') == 'test_value'
            
            # Test complex data types
            backend.write('complex', {'nested': [1, 2, 3], 'value': True})
            assert backend.read('complex') == {'nested': [1, 2, 3], 'value': True}
    
    def test_json_file_backend_directory_creation(self):
        """Test that JSON backend creates necessary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / 'nested' / 'dir' / 'settings.json'
            backend = JSONFileBackend(nested_path)
            
            # Directory should be created automatically
            assert nested_path.parent.exists()
            
            # Test write works
            backend.write('test', 'value')
            assert nested_path.exists()


class TestSettingsManager:
    """Test settings manager functionality."""
    
    def setup_method(self):
        """Set up test settings manager."""
        self.persistent_backend = MemoryBackend()
        self.transient_backend = MemoryBackend()
        self.manager = SettingsManager(self.persistent_backend, self.transient_backend)
    
    def test_register_and_get_setting(self):
        """Test setting registration and retrieval."""
        # Register a setting
        self.manager.register_setting(
            'test.setting', 
            'default_value', 
            persistent=True,
            description='Test setting'
        )
        
        # Test default value
        assert self.manager.get('test.setting') == 'default_value'
        
        # Test custom default
        assert self.manager.get('nonexistent', 'custom_default') == 'custom_default'
    
    def test_set_and_get_persistent_setting(self):
        """Test persistent setting storage."""
        self.manager.register_setting('test.persistent', 'default', persistent=True)
        
        # Set value
        self.manager.set('test.persistent', 'new_value')
        
        # Verify it's stored in persistent backend
        assert self.persistent_backend.read('test.persistent') == 'new_value'
        assert self.manager.get('test.persistent') == 'new_value'
    
    def test_set_and_get_transient_setting(self):
        """Test transient setting storage."""
        self.manager.register_setting('test.transient', 'default', persistent=False)
        
        # Set value
        self.manager.set('test.transient', 'new_value')
        
        # Verify it's stored in transient backend
        assert self.transient_backend.read('test.transient') == 'new_value'
        assert self.manager.get('test.transient') == 'new_value'
        
        # Verify not in persistent backend
        assert self.persistent_backend.read('test.transient') is None
    
    def test_setting_validation(self):
        """Test setting value validation."""
        def validate_positive(value):
            return isinstance(value, int) and value > 0
        
        self.manager.register_setting(
            'test.validated', 
            10, 
            validator=validate_positive,
            description='Positive integer'
        )
        
        # Valid value should work
        self.manager.set('test.validated', 5)
        assert self.manager.get('test.validated') == 5
        
        # Invalid value should raise error
        with pytest.raises(ValueError):
            self.manager.set('test.validated', -1)
    
    def test_change_callbacks(self):
        """Test setting change notifications."""
        callback_calls = []
        
        def test_callback(key, old_value, new_value):
            callback_calls.append((key, old_value, new_value))
        
        self.manager.add_change_callback(test_callback)
        self.manager.register_setting('test.callback', 'initial')
        
        # Set value should trigger callback
        self.manager.set('test.callback', 'changed')
        
        assert len(callback_calls) == 1
        assert callback_calls[0] == ('test.callback', None, 'changed')
        
        # Remove callback
        self.manager.remove_change_callback(test_callback)
        self.manager.set('test.callback', 'changed_again')
        
        # Should not trigger callback again
        assert len(callback_calls) == 1
    
    def test_category_operations(self):
        """Test category-based setting operations."""
        # Register settings in same category
        self.manager.register_setting('ui.theme', 'dark')
        self.manager.register_setting('ui.font_size', 12)
        self.manager.register_setting('audio.format', 'wav')
        
        # Test get category
        ui_settings = self.manager.get_category('ui')
        assert 'ui.theme' in ui_settings
        assert 'ui.font_size' in ui_settings
        assert 'audio.format' not in ui_settings
        
        # Test set category
        self.manager.set_category('ui', {
            'theme': 'light',
            'font_size': 14
        })
        
        assert self.manager.get('ui.theme') == 'light'
        assert self.manager.get('ui.font_size') == 14
    
    def test_reset_to_defaults(self):
        """Test resetting settings to defaults."""
        self.manager.register_setting('test.reset', 'default_value')
        
        # Change value
        self.manager.set('test.reset', 'changed_value')
        assert self.manager.get('test.reset') == 'changed_value'
        
        # Reset to default
        self.manager.reset_to_defaults('test.reset')
        assert self.manager.get('test.reset') == 'default_value'
    
    def test_export_import_settings(self):
        """Test settings export and import."""
        # Register and set some settings
        self.manager.register_setting('test.export1', 'default1', persistent=True)
        self.manager.register_setting('test.export2', 'default2', persistent=False)
        
        self.manager.set('test.export1', 'value1')
        self.manager.set('test.export2', 'value2')
        
        # Export persistent only
        exported = self.manager.export_settings(persistent_only=True)
        assert 'test.export1' in exported
        assert 'test.export2' not in exported
        
        # Import settings
        self.manager.reset_to_defaults()
        self.manager.import_settings(exported)
        
        assert self.manager.get('test.export1') == 'value1'


class TestSettingsSchema:
    """Test settings schema validation and utilities."""
    
    def test_schema_validation(self):
        """Test schema validation functions."""
        # Test valid settings
        assert validate_setting('ui.theme', 'dark')
        assert validate_setting('ui.font_size', 12)
        assert validate_setting('audio.sample_rate', 44100)
        
        # Test invalid settings
        assert not validate_setting('ui.theme', 'invalid_theme')
        assert not validate_setting('ui.font_size', 5)  # Too small
        assert not validate_setting('ui.font_size', 'not_an_int')
        assert not validate_setting('nonexistent.setting', 'any_value')
    
    def test_default_settings_retrieval(self):
        """Test getting default settings."""
        defaults = get_default_settings()
        
        # Should contain all settings from schema
        assert 'ui.theme' in defaults
        assert 'audio.default_format' in defaults
        assert 'session.current_tab' in defaults
        
        # Check specific defaults
        assert defaults['ui.theme'] == 'dark'
        assert defaults['audio.default_format'] == 'wav'
        assert defaults['session.current_tab'] == 'audio'
    
    def test_persistent_settings_filtering(self):
        """Test filtering of persistent settings."""
        persistent = get_persistent_settings()
        
        # Should contain persistent settings
        assert 'ui.theme' in persistent
        assert 'window.width' in persistent
        
        # Should not contain transient settings
        assert 'session.current_tab' not in persistent
        assert 'session.selected_files' not in persistent
    
    def test_category_filtering(self):
        """Test category-based setting filtering."""
        ui_settings = get_settings_by_category('ui')
        audio_settings = get_settings_by_category('audio')
        
        # Check UI settings
        assert any(key.startswith('ui.') for key in ui_settings.keys())
        assert not any(key.startswith('audio.') for key in ui_settings.keys())
        
        # Check audio settings
        assert any(key.startswith('audio.') for key in audio_settings.keys())
        assert not any(key.startswith('ui.') for key in audio_settings.keys())


class TestSettingsIntegration:
    """Test settings schema integration and global manager."""

    def setup_method(self):
        """Initialize a global settings manager for integration tests."""
        self.persistent_backend = MemoryBackend()
        self.transient_backend = MemoryBackend()
        init_settings_manager(self.persistent_backend, self.transient_backend)

    def test_schema_integration(self):
        """Test that settings manager works with schema definitions."""
        manager = get_settings_manager()
        
        # Register all schema settings
        for key, config in SETTINGS_SCHEMA.items():
            manager.register_setting(
                key=key,
                default_value=config['default'],
                persistent=config.get('persistent', True),
                validator=lambda value, key=key: validate_setting(key, value),
                description=config.get('description', '')
            )
        
        # Test setting and getting schema-defined settings
        manager.set('ui.theme', 'light')
        assert manager.get('ui.theme') == 'light'
        
        manager.set('audio.sample_rate', 48000)
        assert manager.get('audio.sample_rate') == 48000
        
        # Test validation works
        with pytest.raises(ValueError):
            manager.set('ui.theme', 'invalid_theme')


if __name__ == '__main__':
    pytest.main([__file__]) 
 