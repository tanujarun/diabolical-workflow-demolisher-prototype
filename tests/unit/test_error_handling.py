
"""
Unit tests for the migrated error handling system.
"""

import pytest
import sys
import os
import warnings
from unittest.mock import Mock

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

warnings.filterwarnings('ignore', category=DeprecationWarning)

from dwd.utils.error_handling import (
    ErrorManager, RetryErrorType, FallbackErrorManager
)


class TestErrorManager:
    """Test error manager functionality."""
    
    def setup_method(self):
        """Set up test error manager with mock app instance."""
        self.mock_app = Mock()
        self.mock_app.log_message = Mock()
        self.error_manager = ErrorManager(self.mock_app)
    
    def test_error_manager_creation(self):
        """Test error manager can be created with app instance."""
        assert self.error_manager is not None
        assert isinstance(self.error_manager, ErrorManager)
        assert self.error_manager.app == self.mock_app
    
    def test_error_handling_basic(self):
        """Test basic error handling functionality."""
        error_id = self.error_manager.handle_error(
            'TEST_ERROR',
            'Test error message',
            category='SYSTEM'
        )
        
        assert error_id is not None
        assert error_id.startswith('ERR_')
        
        # Verify error was logged
        assert len(self.error_manager.session_errors) == 1
        error_record = self.error_manager.session_errors[0]
        assert error_record['type'] == 'TEST_ERROR'
        assert error_record['message'] == 'Test error message'
    
    def test_error_statistics(self):
        """Test error statistics collection."""
        # Handle multiple errors
        self.error_manager.handle_error('ERROR1', 'First error', 'SYSTEM')
        self.error_manager.handle_error('ERROR2', 'Second error', 'FILE_IO')
        self.error_manager.handle_error('ERROR3', 'Third error', 'SYSTEM')
        
        stats = self.error_manager.get_error_statistics()
        assert 'SYSTEM' in stats
        assert 'FILE_IO' in stats
        assert stats['SYSTEM']['count'] == 2
        assert stats['FILE_IO']['count'] == 1


class TestRetryErrorType:
    """Test retry error type enumeration."""
    
    def test_retry_error_types_exist(self):
        """Test that retry error types are available."""
        assert RetryErrorType is not None
        
        # Test that the enum has expected values
        assert hasattr(RetryErrorType, '__members__')
        assert len(RetryErrorType.__members__) > 0
        
        # Test specific enum values
        assert RetryErrorType.TRANSIENT.value == 'transient'
        assert RetryErrorType.TERMINAL.value == 'terminal'
        assert RetryErrorType.RESOURCE.value == 'resource'
        assert RetryErrorType.UNKNOWN.value == 'unknown'


class TestFallbackErrorManager:
    """Test fallback error manager functionality."""
    
    def test_fallback_error_manager_creation(self):
        """Test that fallback error manager can be created."""
        mock_app = Mock()
        mock_app.log_message = Mock()
        
        fallback_manager = FallbackErrorManager(mock_app)
        assert fallback_manager is not None
        assert isinstance(fallback_manager, FallbackErrorManager)
    
    def test_fallback_error_handling(self):
        """Test basic fallback error handling."""
        mock_app = Mock()
        mock_app.log_message = Mock()
        
        fallback_manager = FallbackErrorManager(mock_app)
        
        # Test basic error handling
        error_id = fallback_manager.handle_error('TEST_ERROR', 'Test message')
        assert error_id is not None
        
        # Verify app.log_message was called
        mock_app.log_message.assert_called()


class TestCompatibilityShims:
    """Test error handling compatibility shims."""
    
    def test_old_error_manager_import(self):
        """Test that old import paths still work."""
        from src.dwd.core.error_manager import ErrorManager as OldErrorManager
        assert OldErrorManager is not None
    
    def test_fallback_error_manager_import(self):
        """Test fallback error manager import from compatibility shim."""
        from src.dwd.core.error_manager import FallbackErrorManager as OldFallbackManager
        assert OldFallbackManager is not None


if __name__ == '__main__':
    pytest.main([__file__])
