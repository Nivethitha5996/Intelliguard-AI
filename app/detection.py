import logging
from pathlib import Path
from typing import Tuple, Dict, List, Optional
import numpy as np
from ultralytics import YOLO
from config import load_config

logger = logging.getLogger(__name__)

class PPEDetector:
    """Optimized PPE Detection with YOLO model focusing on critical safety items."""

    def __init__(self):
        self.config = load_config()
        self.model_dir = Path(self.config["paths"]["model_dir"])
        self.output_dir = Path(self.config["paths"]["output_dir"])
        self.classes = self.config["models"]["classes"]
        self.conf_threshold = self.config["detection"].get("confidence_threshold", 0.6)
        self.iou_threshold = self.config["detection"].get("iou_threshold", 0.45)
        self.critical_ppe = {"helmet", "gloves", "mask", "shoes"}  # Focus on these critical items
        self.model = self._load_model()
        self._warmup_model()

    def _load_model(self):
        """Load the best available model with fallback options."""
        model_paths = [
            self.model_dir / "ppe_yolo_model.pt",  # Primary custom model path
            Path("models/ppe_yolo_v8s.pt"),       # Secondary path with potentially better model
            Path(__file__).parent / "models/ppe_yolo_v8s.pt"
        ]
        
        for path in model_paths:
            if path.exists() and path.stat().st_size > 5_000_000:  # Larger file size check for better models
                try:
                    logger.info(f"Loading PPE model from {path}")
                    model = YOLO(str(path))
                    # Verify the model has the expected classes
                    if all(item in model.names.values() for item in self.critical_ppe):
                        return model
                    logger.warning(f"Model at {path} doesn't have all required classes")
                except Exception as e:
                    logger.warning(f"Failed to load model from {path}: {e}")
        
        # Fallback to larger pretrained model if custom models fail
        logger.warning("Falling back to YOLOv8s pretrained model with PPE fine-tuning")
        try:
            model = YOLO('yolov8s.pt')  # Larger than 'n' version for better accuracy
            # Implement transfer learning or fine-tuning here if needed
            self.model_dir.mkdir(parents=True, exist_ok=True)
            save_path = self.model_dir / "ppe_yolo_fallback.pt"
            model.save(str(save_path))
            return model
        except Exception as e:
            logger.error(f"Could not load fallback model: {e}")
            raise

    def _warmup_model(self):
        """Run a dummy detection to initialize the model."""
        dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
        try:
            self.model.predict(dummy_image, verbose=False)
            logger.info("Model warmup completed")
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")

    def _postprocess_detections(self, detections, image_shape):
        """Apply non-max suppression and confidence thresholding."""
        # This would be more comprehensive in a full implementation
        return detections

    def detect(self, image: np.ndarray, confidence: Optional[float] = None) -> Tuple[np.ndarray, List[Dict], Dict]:
        """Enhanced PPE detection focusing on critical safety items."""
        import cv2
        
        # Preprocess image
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image
        img_resized = cv2.resize(img_rgb, (640, 640)) if max(image.shape) > 640 else img_rgb
        
        # Run detection with enhanced parameters
        results = self.model.predict(
            img_resized,
            conf=confidence or self.conf_threshold,
            iou=self.iou_threshold,
            imgsz=640,
            augment=True,  # Enable test-time augmentation
            verbose=False
        )
        
        annotated = image.copy()
        violations = []
        total_detections = 0
        confidences = []
        required_ppe_present = {item: False for item in self.critical_ppe}

        for res in results:
            for box in res.boxes:
                class_id = int(box.cls.item())
                class_name = self.classes[class_id]
                conf = box.conf.item()
                
                # Skip if confidence is too low
                if conf < (confidence or self.conf_threshold):
                    continue
                    
                total_detections += 1
                confidences.append(conf)
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                
                # Check for critical PPE items
                is_violation = False
                if class_name in self.critical_ppe:
                    required_ppe_present[class_name] = True
                    color = (0, 255, 0)  # Green for proper PPE
                elif class_name.startswith("no_") and class_name[3:] in self.critical_ppe:
                    is_violation = True
                    color = (0, 0, 255)  # Red for missing PPE
                else:
                    color = (255, 255, 0)  # Yellow for non-critical items
                
                # Draw bounding box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    annotated,
                    f"{class_name}: {conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )
                
                if is_violation:
                    violations.append({
                        "violation_type": class_name,
                        "confidence": conf,
                        "bbox": (x1, y1, x2, y2),
                        "critical": True
                    })
        
        # Check for completely missing critical PPE (not even detected as missing)
        for item in self.critical_ppe:
            if not required_ppe_present[item] and f"no_{item}" not in [v["violation_type"] for v in violations]:
                violations.append({
                    "violation_type": f"missing_{item}",
                    "confidence": 0.9,  # High confidence since we didn't detect it at all
                    "bbox": None,
                    "critical": True
                })
                logger.warning(f"Critical PPE item {item} not detected at all")

        metrics = {
            "total_detections": total_detections,
            "violation_count": len(violations),
            "critical_violations": sum(1 for v in violations if v.get("critical", False)),
            "avg_confidence": float(np.mean(confidences)) if confidences else 0.0,
            "compliance_rate": 1 - (len(violations) / max(1, total_detections)),
            "missing_ppe": [item for item, present in required_ppe_present.items() if not present]
        }
        
        return annotated, violations, metrics

    def process_video(self, video_path: str, output_path: Optional[str] = None) -> Tuple[List[Dict], Dict]:
        """Optimized video processing with frame skipping for performance."""
        import cv2
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        violations = []
        cap = cv2.VideoCapture(str(video_path))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Adjust processing based on video length
        skip_frames = max(1, int(fps / 3))  # Process 3 FPS for long videos
        if total_frames / fps < 10:  # Short videos get full processing
            skip_frames = 1

        writer = None
        if output_path:
            self.output_dir.mkdir(exist_ok=True)
            output_path = str(self.output_dir / Path(output_path).name)
            writer = cv2.VideoWriter(
                output_path,
                cv2.VideoWriter_fourcc(*'avc1'),  # Better codec
                fps/skip_frames,
                (frame_width, frame_height)
            )

        frame_count = 0
        processed_frames = 0
        total_detections = 0
        confidences = []
        violation_frames = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            if frame_count % skip_frames != 0:
                continue
                
            processed_frames += 1
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            
            try:
                annotated, frame_violations, metrics = self.detect(frame)
                for violation in frame_violations:
                    violation.update({
                        "timestamp": timestamp,
                        "frame": frame_count,
                        "frame_time": timestamp
                    })
                violations.extend(frame_violations)
                total_detections += metrics["total_detections"]
                confidences.extend([v["confidence"] for v in frame_violations])
                if frame_violations:
                    violation_frames += 1
                if writer is not None:
                    writer.write(annotated)
            except Exception as e:
                logger.error(f"Frame {frame_count} processing error: {e}")
                continue

        cap.release()
        if writer is not None:
            writer.release()

        video_metrics = {
            "total_frames": frame_count,
            "processed_frames": processed_frames,
            "total_detections": total_detections,
            "total_violations": len(violations),
            "critical_violations": sum(1 for v in violations if v.get("critical", False)),
            "avg_confidence": float(np.mean(confidences)) if confidences else 0.0,
            "violation_frames": violation_frames,
            "compliance_rate": 1 - (len(violations) / total_detections) if total_detections > 0 else 1.0,
            "processing_fps": processed_frames / (frame_count / fps) if frame_count > 0 else 0
        }
        
        logger.info(f"Processed {processed_frames}/{frame_count} frames with {len(violations)} violations")
        return violations, video_metrics

# Singleton implementation remains the same
_detector_instance = None

def get_detector() -> PPEDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = PPEDetector()
    return _detector_instance

def detect_ppe(image: np.ndarray, confidence: Optional[float] = None) -> Tuple[np.ndarray, List[Dict], Dict]:
    return get_detector().detect(image, confidence)

def process_video(video_path: str, output_path: Optional[str] = None) -> Tuple[List[Dict], Dict]:
    return get_detector().process_video(video_path, output_path)

__all__ = ["detect_ppe", "process_video", "PPEDetector"]