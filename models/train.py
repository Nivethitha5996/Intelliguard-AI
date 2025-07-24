from ultralytics import YOLO
import yaml
import os
from datetime import datetime
from .utils import load_config, setup_logging

def prepare_dataset(config_path: str = "config/config.yaml"):
    """Prepare dataset for YOLO training."""
    config = load_config(config_path)
    
    # Create dataset.yaml file expected by YOLO
    dataset_config = {
        'path': 'data/ppe',  # Base path
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'names': {i: name for i, name in enumerate(config['models']['classes'])}
    }
    
    os.makedirs('data/ppe', exist_ok=True)
    with open('data/ppe/dataset.yaml', 'w') as f:
        yaml.dump(dataset_config, f)
    
    return 'data/ppe/dataset.yaml'

def train_yolo_model():
    """Train YOLO model on PPE dataset."""
    setup_logging()
    dataset_config = prepare_dataset()
    
    # Load a pretrained YOLO model
    model = YOLO('yolov8n.pt')  # nano version for demo
    
    # Train the model
    results = model.train(
        data=dataset_config,
        epochs=100,
        imgsz=640,
        batch=16,
        name=f"ppe_yolov8_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # Export the trained model
    model.export(format='onnx')
    
    return results

if __name__ == "__main__":
    train_yolo_model()