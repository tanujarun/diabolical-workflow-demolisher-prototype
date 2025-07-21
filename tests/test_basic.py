"""
Basic tests for DWD application.
"""

import pytest
import sys
import os

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import dwd
except ImportError:
    dwd = None


class TestBasic:
    """Basic tests for project structure and imports."""
    
    def test_project_structure_exists(self):
        """Test that basic project structure exists."""
        project_root = os.path.join(os.path.dirname(__file__), '..')
        
        # Check for key files
        assert os.path.exists(os.path.join(project_root, 'README.md'))
        assert os.path.exists(os.path.join(project_root, 'requirements.txt'))
        assert os.path.exists(os.path.join(project_root, 'pyproject.toml'))
        assert os.path.exists(os.path.join(project_root, 'DWD.py'))
        
        # Check for source structure
        assert os.path.exists(os.path.join(project_root, 'src', 'dwd'))
        assert os.path.exists(os.path.join(project_root, 'src', 'dwd', '__init__.py'))
    
    def test_package_imports(self):
        """Test that the main package can be imported."""
        if dwd:
            assert hasattr(dwd, '__version__')
            assert hasattr(dwd, '__author__')
            assert hasattr(dwd, '__description__')
        else:
            pytest.skip("DWD package not importable yet")
    
    def test_main_application_exists(self):
        """Test that the main DWD.py file exists and is readable."""
        project_root = os.path.join(os.path.dirname(__file__), '..')
        dwd_file = os.path.join(project_root, 'DWD.py')
        
        assert os.path.exists(dwd_file)
        assert os.path.getsize(dwd_file) > 0
        
        # Check that file contains main class
        with open(dwd_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'DiabolicalWorkflowDemolisher' in content
            assert 'class ' in content


if __name__ == '__main__':
    pytest.main([__file__]) 
 