import logging
import sys
import pytest
from unittest import mock
from OBDH.logger import Logger  # Replace with actual import path

# Mock TTCHandler from OBDH.ttc_handler
@pytest.fixture(autouse=True)
def mock_ttc_handler():
    with mock.patch("OBDH.ttc_handler.TTCHandler") as MockTTC:
        yield MockTTC

def test_logger_initialization(monkeypatch, tmp_path):
    # Use a temporary file path for testing the file handler
    log_file = tmp_path / "test.log"

    logger_instance = Logger(log_to_console=True, log_file=str(log_file))
    logger = logger_instance.get_logger()

    # Check logger name
    assert logger.name == "Vector"

    # Should have at least a FileHandler and StreamHandler
    handler_types = [type(h) for h in logger.handlers]
    assert logging.FileHandler in handler_types
    assert logging.StreamHandler in handler_types

    # Should log to the file
    logger.info("Test log message")
    with open(log_file, "r") as f:
        contents = f.read()
    assert "Test log message" in contents

def test_logger_no_console(tmp_path):
    log_file = tmp_path / "test_no_console.log"
    logger_instance = Logger(log_to_console=False, log_file=str(log_file))
    logger = logger_instance.get_logger()

    handler_types = [type(h) for h in logger.handlers]
    assert logging.StreamHandler not in handler_types
    assert logging.FileHandler in handler_types

def test_set_ttc_handler(mock_ttc_handler):
    dummy_pipe = mock.Mock()

    logger_instance = Logger()
    logger_instance.set_ttc_handler(dummy_pipe)

    # Assert TTCHandler was instantiated with the correct pipe
    mock_ttc_handler.assert_called_once_with(dummy_pipe)

    # Assert that the TTCHandler was added to the logger
    assert any(isinstance(h, mock.MagicMock) for h in logger_instance.get_logger().handlers)