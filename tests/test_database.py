import pytest
from app.database import DatabaseHandler
from datetime import datetime, timedelta

@pytest.fixture
def db_handler():
    return DatabaseHandler()

def test_db_connection(db_handler):
    assert db_handler.conn is not None

def test_log_compliance_data(db_handler):
    metadata = {
        'location': 'test_location',
        'camera_id': 'test_cam',
        'total_people_detected': 1
    }
    violations = [{'type': 'no_helmet', 'confidence': 0.9, 'location': (0, 0, 10, 10)}]
    
    metadata_id = db_handler.log_compliance_data(metadata, violations)
    assert metadata_id is not None

def test_get_violation_stats(db_handler):
    stats = db_handler.get_violation_stats("1 day")
    assert isinstance(stats, dict)
    assert 'time_range' in stats
    assert 'violations' in stats