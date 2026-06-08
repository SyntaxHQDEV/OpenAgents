import pytest
from unittest.mock import patch, Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from api.routes.agents import validate_endpoint

@patch('api.routes.agents.http_requests.head')
def test_valid_url(mock_head):
    mock_head.return_value = Mock(status_code=200)
    assert validate_endpoint('https://example.com') == 'https://example.com'

def test_invalid_format():
    with pytest.raises(ValueError, match="Invalid URL format"):
        validate_endpoint('not_a_url')
    with pytest.raises(ValueError, match="Invalid URL format"):
        validate_endpoint('ftp://example.com')

def test_private_ip():
    with pytest.raises(ValueError, match="Private/internal IP addresses not allowed"):
        validate_endpoint('http://127.0.0.1/api')
    with pytest.raises(ValueError, match="Private/internal IP addresses not allowed"):
        validate_endpoint('http://10.0.0.5/api')
    with pytest.raises(ValueError, match="Private/internal IP addresses not allowed"):
        validate_endpoint('http://192.168.1.100/api')

@patch('api.routes.agents.http_requests.head')
def test_timeout(mock_head):
    import requests
    mock_head.side_effect = requests.exceptions.Timeout("Timeout")
    with pytest.raises(ValueError, match="Endpoint not reachable"):
        validate_endpoint('https://timeout.com')
