import pytest
from app.auth import UserAuthenticator
import cv2
import numpy as np
import os

@pytest.fixture
def authenticator():
    return UserAuthenticator()

def test_pin_based_login(authenticator):
    # Test correct PIN
    assert authenticator.pin_based_login("1234") is True
    
    # Test incorrect PIN
    assert authenticator.pin_based_login("wrong") is False

def test_face_recognition(authenticator):
    # Create a dummy image
    dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Test with dummy image (should fail)
    success, username = authenticator.recognize_face(dummy_image)
    assert success is False
    assert username is None