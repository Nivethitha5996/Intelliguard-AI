import pytest
from app.detection import PPEDetector
import cv2
import numpy as np

@pytest.fixture
def detector():
    return PPEDetector()

def test_detection(detector):
    # Create a dummy image
    dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
    
    # Test detection
    annotated_image, violations = detector.detect(dummy_image)
    
    assert isinstance(annotated_image, np.ndarray)
    assert isinstance(violations, list)