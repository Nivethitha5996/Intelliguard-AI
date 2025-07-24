# utils.py
import yaml
import os
import cv2
import numpy as np
from typing import Dict, Any, Union, Optional
import logging
from pathlib import Path
import io
import time
from ultralytics import YOLO
from dotenv import load_dotenv

def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file with robust error handling.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found at {config_path}")
            
        with open(config_file, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            
        if not config:
            raise ValueError("Config file is empty")
            
        return config
        
    except Exception as e:
        logging.error(f"Error loading config: {str(e)}")
        raise

def setup_logging(log_dir: str = "logs", log_level: int = logging.INFO) -> None:
    """
    Set up comprehensive logging configuration.
    
    Args:
        log_dir: Directory to store log files
        log_level: Minimum logging level (DEBUG, INFO, WARNING, etc.)
    """
    try:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        handlers = [
            logging.FileHandler(log_path / 'intelliguard.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt=date_format,
            handlers=handlers
        )
        
        # Silence noisy library logs
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        
    except Exception as e:
        print(f"Failed to configure logging: {str(e)}")
        raise

def read_image(file: Union[str, Path, io.BytesIO]) -> np.ndarray:
    """
    Read an image file into a numpy array with validation.
    
    Args:
        file: File path, BytesIO object, or file-like object
        
    Returns:
        Numpy array of the image in BGR format
        
    Raises:
        ValueError: If image cannot be read or is invalid
    """
    try:
        if isinstance(file, (str, Path)):
            if not Path(file).exists():
                raise FileNotFoundError(f"Image file not found: {file}")
            image = cv2.imread(str(file))
        else:
            file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
        if image is None:
            raise ValueError("Failed to decode image - possibly corrupt or unsupported format")
            
        return image
        
    except Exception as e:
        logging.error(f"Error reading image: {str(e)}")
        raise

def save_uploaded_file(uploaded_file: io.BytesIO, 
                      save_dir: str = "uploads",
                      allowed_extensions: Optional[list] = None) -> Path:
    """
    Securely save an uploaded file with validation.
    
    Args:
        uploaded_file: Streamlit UploadedFile object or BytesIO
        save_dir: Directory to save the file
        allowed_extensions: List of permitted file extensions (e.g. ['.jpg', '.png'])
        
    Returns:
        Path to the saved file
        
    Raises:
        ValueError: For invalid file types or save failures
    """
    try:
        # Validate file extension if restrictions provided
        if allowed_extensions:
            ext = Path(uploaded_file.name).suffix.lower()
            if ext not in allowed_extensions:
                raise ValueError(f"Invalid file extension {ext}. Allowed: {allowed_extensions}")
                
        # Create save directory if needed
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename and path
        original_name = Path(uploaded_file.name).name  # Remove any path components
        safe_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '.', '_', '-'))
        file_path = save_path / safe_name
        
        # Save file content
        with open(file_path, "wb") as f:
            if hasattr(uploaded_file, 'getbuffer'):
                f.write(uploaded_file.getbuffer())
            else:
                f.write(uploaded_file.read())
                
        logging.info(f"Saved uploaded file to {file_path}")
        return file_path
        
    except Exception as e:
        logging.error(f"Failed to save uploaded file: {str(e)}")
        raise

def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    Validate a file extension against allowed list.
    
    Args:
        filename: Name or path of the file
        allowed_extensions: List of permitted extensions (e.g. ['.jpg', '.png'])
        
    Returns:
        bool: True if extension is allowed
    """
    try:
        ext = Path(filename).suffix.lower()
        return ext in allowed_extensions
    except Exception as e:
        logging.warning(f"Extension validation error: {str(e)}")
        return False

def clean_temp_files(directory: Union[str, Path], pattern: str = "*", max_age_hours: int = 24) -> None:
    """
    Clean up temporary files older than specified age.
    
    Args:
        directory: Directory to clean
        pattern: File pattern to match (e.g. "*.tmp")
        max_age_hours: Maximum age in hours before deletion
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return
            
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        for file_path in dir_path.glob(pattern):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    logging.info(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    logging.warning(f"Could not delete {file_path}: {str(e)}")
                    
    except Exception as e:
        logging.error(f"Error during temp file cleanup: {str(e)}")

def load_env():
    """
    Load environment variables from .env file
    """
    load_dotenv()

def load_config_yaml(path="config/config.yaml"):
    """
    Load configuration from YAML file
    
    Args:
        path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing configuration
    """
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_email_config():
    """
    Get email configuration from environment variables
    
    Returns:
        Dictionary containing SMTP server, port, sender email, password, and recipient emails
    """
    return {
        "smtp_server": os.getenv("SMTP_SERVER"),
        "smtp_port": int(os.getenv("SMTP_PORT", 587)),
        "sender_email": os.getenv("SMTP_USER"),
        "sender_password": os.getenv("SMTP_PASSWORD"),
        "recipient_emails": [e.strip() for e in os.getenv("ALERT_RECIPIENTS", "").split(",") if e.strip()]
    }