"""Tests for monitor agent."""
import pytest
import time
from pathlib import Path
from queue import Queue
from src.agents.monitor_agent import MonitorAgent, ScreenshotEventHandler


class TestMonitorAgent:
    """Test MonitorAgent class."""
    
    def test_init(self, tmp_path):
        """Test monitor initialization."""
        monitor = MonitorAgent(tmp_path)
        assert monitor.folder_path == tmp_path
        assert isinstance(monitor.file_queue, Queue)
        assert not monitor.running
    
    def test_validate_folder_exists(self, tmp_path):
        """Test folder validation with existing folder."""
        monitor = MonitorAgent(tmp_path)
        monitor.validate_folder()  # Should not raise
    
    def test_validate_folder_not_exists(self):
        """Test folder validation with non-existent folder."""
        monitor = MonitorAgent(Path("/nonexistent/folder"))
        with pytest.raises(FileNotFoundError):
            monitor.validate_folder()
    
    def test_validate_folder_not_directory(self, tmp_path):
        """Test folder validation with file instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        
        monitor = MonitorAgent(file_path)
        with pytest.raises(NotADirectoryError):
            monitor.validate_folder()
    
    def test_start_stop(self, tmp_path):
        """Test starting and stopping monitor."""
        monitor = MonitorAgent(tmp_path)
        monitor.start()
        assert monitor.running
        assert monitor.observer is not None
        
        monitor.stop()
        assert not monitor.running
    
    def test_file_detection(self, tmp_path):
        """Test file detection and queuing."""
        monitor = MonitorAgent(tmp_path, completion_wait=0.1)
        monitor.start()
        
        # Create a test image file
        test_file = tmp_path / "test_screenshot.png"
        test_file.write_text("fake image data")
        
        # Wait for detection and completion check
        time.sleep(0.3)
        monitor.event_handler.check_file_completion()
        
        monitor.stop()
        
        # File should be in queue
        assert monitor.get_queue_size() > 0
    
    def test_ignore_temporary_files(self, tmp_path):
        """Test that temporary files are ignored."""
        queue = Queue()
        handler = ScreenshotEventHandler(queue)
        
        # Create temporary file
        temp_file = tmp_path / "temp.tmp"
        temp_file.touch()
        
        # Simulate event
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(temp_file))
        handler.on_created(event)
        
        # Should not be in pending files
        assert str(temp_file) not in handler.pending_files
    
    def test_ignore_non_image_files(self, tmp_path):
        """Test that non-image files are ignored."""
        queue = Queue()
        handler = ScreenshotEventHandler(queue)
        
        # Create text file
        text_file = tmp_path / "document.txt"
        text_file.touch()
        
        # Simulate event
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(text_file))
        handler.on_created(event)
        
        # Should not be in pending files
        assert str(text_file) not in handler.pending_files


class TestScreenshotEventHandler:
    """Test ScreenshotEventHandler class."""
    
    def test_file_completion_detection(self, tmp_path):
        """Test file completion detection algorithm."""
        queue = Queue()
        handler = ScreenshotEventHandler(queue, completion_wait=0.1)
        
        # Create file and add to pending
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"data")
        handler.pending_files[str(test_file)] = test_file.stat().st_size
        
        # Check completion
        handler.check_file_completion()
        
        # File should be in queue
        assert not queue.empty()
        assert queue.get() == test_file
    
    def test_file_still_writing(self, tmp_path):
        """Test detection of file still being written."""
        queue = Queue()
        handler = ScreenshotEventHandler(queue)
        
        # Create file with initial size
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"data")
        handler.pending_files[str(test_file)] = 0  # Different size
        
        # Check completion
        handler.check_file_completion()
        
        # File should still be pending
        assert str(test_file) in handler.pending_files
        assert queue.empty()


@pytest.fixture
def mock_callback():
    """Mock callback function for testing."""
    called_files = []
    
    def callback(file_path: Path):
        called_files.append(file_path)
    
    callback.called_files = called_files
    return callback


class TestMonitorIntegration:
    """Integration tests for monitor agent."""
    
    def test_monitor_with_callback(self, tmp_path, mock_callback):
        """Test monitor with callback function."""
        monitor = MonitorAgent(tmp_path, completion_wait=0.1)
        
        # Start in separate thread for testing
        import threading
        thread = threading.Thread(
            target=lambda: monitor.run(mock_callback),
            daemon=True
        )
        thread.start()
        
        # Wait for monitor to start
        time.sleep(0.2)
        
        # Create test file
        test_file = tmp_path / "screenshot.png"
        test_file.write_bytes(b"test data")
        
        # Wait for processing
        time.sleep(0.5)
        
        # Stop monitor
        monitor.running = False
        thread.join(timeout=1)
        
        # Callback should have been called
        assert len(mock_callback.called_files) > 0
