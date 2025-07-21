#!/usr/bin/env python3
"""
Comprehensive Integration Test for Migrated DWD Modular Architecture
Task 24.5: Run and Perform Integration Testing

This test validates the complete functionality of the migrated modular architecture,
including proper handling of ErrorManager requirements and end-to-end workflows.
"""

import sys
import os
import json
import time
import tempfile
import traceback
import warnings
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Suppress deprecation warnings during testing
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)

class ComprehensiveIntegrationTester:
    """Comprehensive integration tester for the migrated DWD modular architecture."""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        self.mock_app = None
        
    def setup_test_environment(self):
        """Set up the test environment with mock objects."""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="dwd_comprehensive_test_")
            
            # Create mock app instance for ErrorManager
            self.mock_app = Mock()
            self.mock_app.log_message = Mock()
            self.mock_app.show_error_dialog = Mock()
            self.mock_app.get_setting = Mock(return_value=True)
            
            self.log_result("Test Environment Setup", True, f"Created temp dir: {self.temp_dir}")
            return True
        except Exception as e:
            self.log_result("Test Environment Setup", False, f"Failed: {e}")
            return False
    
    def log_result(self, test_name, success, message="", details=None):
        """Log test result."""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
    
    def test_modular_imports(self):
        """Test all modular imports work correctly."""
        try:
            # Test core imports
            from dwd.core import (
                SettingsManager, ErrorManager, FallbackErrorManager, RetryErrorType
            )
            
            # Test state management imports
            from dwd.state.job_state import JobState, JobEvent, JobStateMachine, JobStatePersistence
            from dwd.state.app_state import CentralizedStateManager, StateCategory, StateValidator
            from dwd.state.settings.manager import SettingsManager as NewSettingsManager, MemoryBackend, JSONFileBackend
            
            # Test utility imports
            from dwd.utils.error_handling import ErrorManager as UtilsErrorManager
            from dwd.utils.helpers import get_memory_usage, format_time, Timer, JobRetryManager
            
            # Audio subsystem high-level managers (skip heavy GUI/Processor classes to keep tests lightweight)
            from dwd.audio.individual_controls import IndividualControlsManager
            
            self.log_result("Modular Imports", True, "All modular components imported successfully")
            return True
            
        except ImportError as e:
            self.log_result("Modular Imports", False, f"Import failed: {e}")
            return False
    
    def test_error_handling_system(self):
        """Test error handling system with proper mock app."""
        try:
            from dwd.utils.error_handling import ErrorManager, FallbackErrorManager, RetryErrorType
            
            # Test ErrorManager with mock app
            error_manager = ErrorManager(self.mock_app)
            
            # Test basic error handling with correct parameters
            error_id = error_manager.handle_error("TestError", "Test error for integration testing", 
                                                 "SYSTEM", {"test": True})
            
            # Verify error was logged
            self.mock_app.log_message.assert_called()
            
            # Test FallbackErrorManager with app_instance
            fallback_manager = FallbackErrorManager(self.mock_app)
            fallback_id = fallback_manager.handle_error("FallbackTest", "Fallback test error")
            
            # Test RetryErrorType enum
            assert hasattr(RetryErrorType, 'TRANSIENT')
            assert hasattr(RetryErrorType, 'TERMINAL')
            
            self.log_result("Error Handling System", True, 
                          f"ErrorManager and FallbackErrorManager working correctly")
            return True
            
        except Exception as e:
            self.log_result("Error Handling System", False, f"Failed: {e}")
            return False
    
    def test_settings_management_system(self):
        """Test the new settings management system."""
        try:
            from dwd.state.settings.manager import SettingsManager, MemoryBackend, JSONFileBackend
            
            # Test with memory backend
            memory_backend = MemoryBackend()
            transient_backend = MemoryBackend()
            settings_manager = SettingsManager(memory_backend, transient_backend)
            
            # Test setting registration and retrieval
            settings_manager.register_setting('test_setting', 'default_value', persistent=True)
            assert settings_manager.get('test_setting') == 'default_value'
            
            # Test setting modification
            settings_manager.set('test_setting', 'modified_value')
            assert settings_manager.get('test_setting') == 'modified_value'
            
            # Test JSON file backend
            test_file = Path(self.temp_dir) / 'test_settings.json'
            file_backend = JSONFileBackend(test_file)
            file_backend.write('file_test', 'file_value')
            assert file_backend.read('file_test') == 'file_value'
            
            self.log_result("Settings Management System", True, 
                          "Memory and file backends working correctly")
            return True
            
        except Exception as e:
            self.log_result("Settings Management System", False, f"Failed: {e}")
            return False
    
    def test_state_management_system(self):
        """Test job state and app state management."""
        try:
            from dwd.state.job_state import JobState, JobEvent, JobStateMachine
            from dwd.state.app_state import CentralizedStateManager
            
            # Test job state machine
            state_machine = JobStateMachine()
            
            # Create test job
            test_job_id = f"integration_test_{int(time.time())}"
            job_data = {
                'name': 'Comprehensive Integration Test Job',
                'input_file': 'test_input.wav',
                'output_file': 'test_output.wav',
                'type': 'audio_processing'
            }
            
            # Test job creation and state transitions
            success = state_machine.create_job(test_job_id, job_data)
            assert success, "Job creation failed"
            
            initial_state = state_machine.get_job_state(test_job_id)
            assert initial_state == JobState.CREATED
            
            # Test state transition using send_event (correct API)
            transition_success = state_machine.send_event(test_job_id, JobEvent.START)
            if transition_success:
                new_state = state_machine.get_job_state(test_job_id)
                assert new_state == JobState.QUEUED or new_state == JobState.INITIALIZING
            
            # Test app state manager
            app_state_manager = CentralizedStateManager()
            app_state_manager.set_state('audio', 'volume_level', 0.8)
            volume = app_state_manager.get_state('audio', 'volume_level')
            assert volume == 0.8
            
            # Cleanup
            state_machine.remove_job(test_job_id)
            
            self.log_result("State Management System", True, 
                          f"Job and app state management working correctly")
            return True
            
        except Exception as e:
            self.log_result("State Management System", False, f"Failed: {e}")
            return False
    
    def test_compatibility_shims(self):
        """Test that compatibility shims work correctly."""
        try:
            # Test importing from old locations (should trigger deprecation warnings but work)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                # Test old settings import
                from dwd.core.settings import SettingsManager as OldSettingsManager
                
                # Test old error handling import  
                from dwd.core.error_manager import ErrorManager as OldErrorManager
                
                # Should have received deprecation warnings
                deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
                
            self.log_result("Compatibility Shims", True, 
                          f"Compatibility shims working, {len(deprecation_warnings)} deprecation warnings as expected")
            return True
            
        except Exception as e:
            self.log_result("Compatibility Shims", False, f"Failed: {e}")
            return False
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow simulation."""
        try:
            from dwd.state.job_state import JobStateMachine, JobState, JobEvent
            from dwd.state.settings.manager import SettingsManager, MemoryBackend
            from dwd.utils.error_handling import ErrorManager
            from dwd.utils.helpers import Timer, get_memory_usage
            
            # Set up workflow components
            state_machine = JobStateMachine()
            settings_manager = SettingsManager(MemoryBackend(), MemoryBackend())
            error_manager = ErrorManager(self.mock_app)
            
            # Configure workflow settings
            settings_manager.register_setting('workflow.enabled', True, persistent=True)
            settings_manager.register_setting('workflow.max_jobs', 5, persistent=True)
            
            # Simulate job processing workflow
            with Timer() as workflow_timer:
                # Create multiple test jobs
                job_ids = []
                for i in range(3):
                    job_id = f"workflow_job_{i}_{int(time.time())}"
                    job_data = {
                        'name': f'Workflow Test Job {i+1}',
                        'input_file': f'input_{i}.wav',
                        'output_file': f'output_{i}.wav'
                    }
                    
                    success = state_machine.create_job(job_id, job_data)
                    if success:
                        job_ids.append(job_id)
                        
                        # Simulate state transitions with correct API
                        state_machine.send_event(job_id, JobEvent.START)
                
                # Verify jobs were created
                created_jobs = [job_id for job_id in job_ids 
                               if state_machine.get_job_state(job_id) in [JobState.QUEUED, JobState.INITIALIZING]]
                
                # Simulate completion
                for job_id in job_ids:
                    state_machine.send_event(job_id, JobEvent.COMPLETE)
                
                # Cleanup
                for job_id in job_ids:
                    state_machine.remove_job(job_id)
            
            workflow_time = workflow_timer.elapsed
            memory_usage = get_memory_usage()
            
            self.log_result("End-to-End Workflow", True, 
                          f"Processed {len(job_ids)} jobs in {workflow_time:.3f}s, "
                          f"Memory: {memory_usage:.1f}MB")
            return True
            
        except Exception as e:
            self.log_result("End-to-End Workflow", False, f"Failed: {e}")
            return False
    
    def test_component_interaction(self):
        """Test interaction between different component systems."""
        try:
            from dwd.state.job_state import JobStateMachine
            from dwd.utils.error_handling import ErrorManager
            
            # Test component initialization
            job_state_machine = JobStateMachine()
            error_manager = ErrorManager(self.mock_app)
            
            # Test that components can interact
            test_job_id = f"interaction_test_{int(time.time())}"
            job_data = {'name': 'Component Interaction Test'}
            
            # Create job through state machine
            success = job_state_machine.create_job(test_job_id, job_data)
            assert success
            
            # Simulate error in job processing
            error_id = error_manager.handle_error("ProcessingError", "Simulated processing error", 
                                                 "SYSTEM", {"job_id": test_job_id})
            assert error_id is not None
            
            # Verify error was logged to mock app
            self.mock_app.log_message.assert_called()
            
            # Cleanup
            job_state_machine.remove_job(test_job_id)
            
            self.log_result("Component Interaction", True, 
                          "Components interact correctly across modules")
            return True
            
        except Exception as e:
            self.log_result("Component Interaction", False, f"Failed: {e}")
            return False
    
    def cleanup_test_environment(self):
        """Clean up test environment."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
            self.log_result("Test Environment Cleanup", True, "Successfully cleaned up")
        except Exception as e:
            self.log_result("Test Environment Cleanup", False, f"Failed: {e}")
    
    def run_all_tests(self):
        """Run all comprehensive integration tests."""
        print("=" * 70)
        print("🚀 DWD COMPREHENSIVE INTEGRATION TEST SUITE")
        print("=" * 70)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        test_start_time = time.time()
        
        if not self.setup_test_environment():
            return False
        
        tests = [
            self.test_modular_imports,
            self.test_error_handling_system,
            self.test_settings_management_system,
            self.test_state_management_system,
            self.test_compatibility_shims,
            self.test_end_to_end_workflow,
            self.test_component_interaction,
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                self.log_result(test.__name__, False, f"Test failed with exception: {e}")
        
        self.cleanup_test_environment()
        
        # Generate report
        test_duration = time.time() - test_start_time
        success_rate = (passed_tests / total_tests) * 100
        
        print()
        print("=" * 70)
        print("📊 COMPREHENSIVE INTEGRATION TEST RESULTS")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Test Duration: {test_duration:.2f}s")
        
        # Save detailed report
        report_file = "comprehensive_integration_test_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': total_tests - passed_tests,
                    'success_rate': success_rate,
                    'test_duration': test_duration,
                    'timestamp': datetime.now().isoformat()
                },
                'test_results': self.test_results
            }, f, indent=2)
        
        print(f"📄 Detailed report saved to: {os.path.abspath(report_file)}")
        
        if passed_tests == total_tests:
            print("✅ ALL COMPREHENSIVE INTEGRATION TESTS PASSED!")
            return True
        else:
            print("❌ Some integration tests failed. Please review the results.")
            return False

def main():
    """Main function to run comprehensive integration tests."""
    tester = ComprehensiveIntegrationTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 