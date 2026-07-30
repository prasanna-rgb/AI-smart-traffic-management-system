"""
Video Stream Processor & Buffer Manager for Camera Feeds, Video Files, and Synthetic Stream Loops.
"""
import time
import threading
import numpy as np
import logging
from typing import Dict, Any, Generator, Optional
from vision.yolo_detector import YOLOV8Detector

logger = logging.getLogger("smart_traffic_ai.vision.stream")

try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False


class StreamProcessor:
    """Manages asynchronous camera/video stream ingestion & YOLO processing loop."""

    def __init__(self, detector: YOLOV8Detector = None):
        self.detector = detector or YOLOV8Detector()
        self.active_source = "synthetic"
        self.cap = None
        self.is_running = False
        self._thread = None
        self.latest_frame_b64 = ""
        self.latest_metrics: Dict[str, Any] = {}
        self.lock = threading.Lock()

    def start_stream(self, source: str = "synthetic"):
        """Start stream processing loop for specified source (synthetic, webcam index, or video file URL)."""
        with self.lock:
            if self.is_running:
                self.stop_stream()

            self.active_source = source
            self.is_running = True

            if source != "synthetic" and CV2_AVAILABLE:
                try:
                    src = int(source) if source.isdigit() else source
                    self.cap = cv2.VideoCapture(src)
                    logger.info(f"Opened Video Capture Source: {source}")
                except Exception as e:
                    logger.error(f"Failed to open video source {source}: {e}. Defaulting to synthetic stream.")
                    self.active_source = "synthetic"

            self._thread = threading.Thread(target=self._stream_loop, daemon=True)
            self._thread.start()

    def stop_stream(self):
        """Stop current video processing loop."""
        self.is_running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def _stream_loop(self):
        """Background thread loop for continuous frame processing."""
        logger.info(f"Stream Loop Started on Source: {self.active_source}")

        while self.is_running:
            frame = None

            if self.active_source != "synthetic" and self.cap is not None and CV2_AVAILABLE and self.cap.isOpened():
                ret, raw_frame = self.cap.read()
                if ret:
                    frame = raw_frame
                else:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, raw_frame = self.cap.read()
                    if ret:
                        frame = raw_frame

            if frame is None:
                frame = self._generate_synthetic_frame()

            annotated_frame, metrics = self.detector.process_frame(frame, intersection_code="INT-01")
            b64_img = self.detector.encode_frame_to_base64(annotated_frame)

            with self.lock:
                self.latest_frame_b64 = b64_img
                self.latest_metrics = metrics

            time.sleep(0.1)

    def _generate_synthetic_frame(self) -> np.ndarray:
        """Generates dynamic HD camera frame buffer."""
        width, height = 640, 480
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        frame[:] = (40, 44, 52)

        if CV2_AVAILABLE:
            cv2.rectangle(frame, (240, 0), (400, height), (60, 64, 72), -1)
            cv2.rectangle(frame, (0, 180), (width, 300), (60, 64, 72), -1)

            cv2.line(frame, (320, 0), (320, 180), (0, 215, 255), 2)
            cv2.line(frame, (320, 300), (320, height), (0, 215, 255), 2)
            cv2.line(frame, (0, 240), (240, 240), (0, 215, 255), 2)
            cv2.line(frame, (400, 240), (width, 240), (0, 215, 255), 2)

            for x in range(240, 400, 20):
                cv2.rectangle(frame, (x, 165), (x + 10, 175), (255, 255, 255), -1)
                cv2.rectangle(frame, (x, 305), (x + 10, 315), (255, 255, 255), -1)

        return frame

    def get_latest_data(self) -> Dict[str, Any]:
        """Thread-safe accessor for latest processed frame base64 and metrics."""
        with self.lock:
            return {
                "frame_b64": self.latest_frame_b64,
                "metrics": self.latest_metrics,
                "source": self.active_source
            }


# Global Stream Instance
stream_processor = StreamProcessor()
