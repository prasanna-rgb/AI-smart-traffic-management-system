"""
YOLOv8 Computer Vision Feed Simulator.
Generates synthetic HD CCTV video frames with bounding box HUD overlays for vehicle detection.
"""
import io
import base64
import random
import time
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont


COLOR_PALETTE = {
    "car": (56, 189, 248),        # Sky Blue
    "ambulance": (239, 68, 68),   # Red
    "fire_truck": (245, 158, 11), # Orange
    "bus": (168, 85, 247),        # Purple
    "motorcycle": (34, 197, 94)   # Green
}


class VisionSimulator:
    """Class to render real-time CCTV stream HUD overlays with YOLOv8 bounding boxes."""

    @staticmethod
    def generate_cctv_frame(road_name: str, telemetry: Dict[str, Any]) -> str:
        """
        Generates a synthetic HD camera frame (800x450) with YOLOv8 detection boxes and HUD telemetry.
        
        Returns:
            Base64 encoded JPEG image data string.
        """
        width, height = 800, 450
        
        # Create dark road background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Draw asphalt background gradient
        frame[:, :] = [18, 24, 38]
        
        # Draw road lanes (asphalt grey lines)
        cv_img = Image.fromarray(frame)
        draw = ImageDraw.Draw(cv_img)
        
        # Road lane lines
        draw.rectangle([50, 100, 750, 400], fill=(30, 41, 59), outline=(71, 85, 105), width=2)
        # Center lane dashed markings
        for x in range(70, 730, 40):
            draw.line([(x, 250), (x + 20, 250)], fill=(234, 179, 8), width=3)

        # Retrieve counts from telemetry
        num_vehicles = telemetry.get("vehicles", telemetry.get("vehicle_count", 45))
        has_emergency = telemetry.get("emergency_vehicle", False)
        emergency_type = telemetry.get("emergency_type", "Ambulance") if has_emergency else None
        
        # Seed random box coordinates deterministically based on road and count
        rng = random.Random(hash(road_name) + int(time.time() // 3))
        
        detected_counts = {"car": 0, "ambulance": 0, "bus": 0, "motorcycle": 0}
        
        # Place Emergency Vehicle if active
        if has_emergency:
            e_type = "ambulance"
            b_width, b_height = 110, 60
            bx = rng.randint(250, 500)
            by = rng.randint(180, 280)
            
            # Emergency Bounding Box
            color = COLOR_PALETTE["ambulance"]
            draw.rectangle([bx, by, bx + b_width, by + b_height], outline=color, width=3)

            # Pulsing Siren effect box
            draw.rectangle([bx - 4, by - 4, bx + b_width + 4, by + b_height + 4], outline=(255, 0, 0), width=1)

            label = f"🚨 {emergency_type.upper()} {rng.randint(95, 99)}%"
            draw.rectangle([bx, by - 22, bx + 160, by], fill=color)
            draw.text((bx + 6, by - 18), label, fill=(255, 255, 255))
            detected_counts["ambulance"] += 1

        # Place regular vehicles
        display_boxes = min(14, max(4, num_vehicles // 6))
        for _ in range(display_boxes):
            v_type = rng.choice(["car", "car", "car", "bus", "motorcycle"])
            b_w = 80 if v_type == "car" else (120 if v_type == "bus" else 45)
            b_h = 50 if v_type == "car" else (65 if v_type == "bus" else 35)
            
            bx = rng.randint(60, 670)
            by = rng.randint(110, 340)
            
            color = COLOR_PALETTE.get(v_type, (56, 189, 248))
            draw.rectangle([bx, by, bx + b_w, by + b_h], outline=color, width=2)
            
            conf = rng.randint(88, 98)
            label = f"{v_type.capitalize()} {conf}%"
            draw.rectangle([bx, by - 18, bx + 90, by], fill=color)
            draw.text((bx + 4, by - 16), label, fill=(15, 23, 42))
            
            if v_type in detected_counts:
                detected_counts[v_type] += 1

        # Place driver behavior violation bounding box tags (overspeeding, wrong-way, sudden braking, illegal U-turn, lane drift)
        speed = telemetry.get("average_speed", 35.0)
        accident = telemetry.get("accident", False)
        
        # Violations overlay logic
        if speed > 65.0:
            bx, by = 550, 140
            draw.rectangle([bx, by, bx + 120, by + 65], outline=(239, 68, 68), width=3)
            draw.rectangle([bx, by - 20, bx + 140, by], fill=(239, 68, 68))
            draw.text((bx + 4, by - 17), f"⚡ OVERSPEED ({int(speed + 15)} km/h)", fill=(255, 255, 255))

        if accident or rng.random() < 0.2:
            bx, by = 180, 290
            draw.rectangle([bx, by, bx + 110, by + 60], outline=(245, 158, 11), width=3)
            draw.rectangle([bx, by - 20, bx + 130, by], fill=(245, 158, 11))
            draw.text((bx + 4, by - 17), "🛑 SUDDEN BRAKING", fill=(255, 255, 255))

        if accident and rng.random() < 0.5:
            bx, by = 380, 130
            draw.rectangle([bx, by, bx + 100, by + 55], outline=(239, 68, 68), width=3)
            draw.rectangle([bx, by - 20, bx + 140, by], fill=(239, 68, 68))
            draw.text((bx + 4, by - 17), "⛔ WRONG-WAY DRIVER", fill=(255, 255, 255))

        # Render Camera HUD Top Overlay
        draw.rectangle([0, 0, width, 40], fill=(15, 23, 42, 230))
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
        hud_text = f"🎥 CAM-04: {road_name.upper()} | LIVE 30 FPS | YOLOv8 + Behavior AI | {timestamp_str}"
        draw.text((16, 12), hud_text, fill=(56, 189, 248))
        
        # Render Camera Status Badge
        status_color = (239, 68, 68) if (has_emergency or speed > 65 or accident) else (34, 197, 94)
        status_msg = "🚨 VIOLATION DETECTED" if (speed > 65 or accident) else ("🚨 EMERGENCY OVERRIDE" if has_emergency else "🟢 NOMINAL FLOW")
        draw.rectangle([width - 210, 8, width - 12, 32], fill=status_color)
        draw.text((width - 200, 12), status_msg, fill=(255, 255, 255))
        
        # Render Bottom Telemetry Ribbon
        draw.rectangle([0, height - 35, width, height], fill=(15, 23, 42, 230))
        bottom_text = f"DETECTIONS: Cars: {detected_counts['car']} | Buses: {detected_counts['bus']} | Ambulances: {detected_counts['ambulance']} | Speed: {telemetry.get('average_speed', 35)} km/h | Driver Risk: {'HIGH 🚨' if (speed > 65 or accident) else 'SAFE 🟢'}"
        draw.text((16, height - 25), bottom_text, fill=(226, 232, 240))
        
        # Convert to Base64
        buffered = io.BytesIO()
        cv_img.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
