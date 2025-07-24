import os
from pathlib import Path

def load_config():
    return {
        "models": {
            "classes": [
                "helmet", 
                "no_helmet",
                "gloves",
                "no_gloves",
                "goggles",
                "no_goggles",
                "mask",
                "no_mask",
                "suit",
                "no_suit",
                "shoes",
                "no_shoes"
            ]
        },
        "detection": {
            "confidence_threshold": 0.7,
            "iou_threshold": 0.45
        },
        "paths": {
            "model_dir": str(Path(__file__).parent / "models"),
            "output_dir": str(Path(__file__).parent.parent / "outputs")
        }
    }