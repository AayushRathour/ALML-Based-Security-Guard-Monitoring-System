# ml/mediapipe_pose.py - Guard pose detection using MediaPipe
import mediapipe as mp
import cv2
import numpy as np
from typing import Tuple, Optional

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    enable_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def is_guard_present(frame: np.ndarray) -> Tuple[bool, Optional[object]]:
    """
    Detect if a guard (person) is present in the frame using pose detection
    
    Args:
        frame: BGR image from cv2
        
    Returns:
        Tuple of (is_present: bool, pose_results: object)
    """
    try:
        # Convert BGR to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the image
        results = pose.process(image)
        
        # Check if pose landmarks were detected
        is_present = results.pose_landmarks is not None
        
        return is_present, results
        
    except Exception as e:
        print(f"Pose detection error: {e}")
        return False, None

def draw_pose_landmarks(frame: np.ndarray, pose_results: object) -> np.ndarray:
    """
    Draw pose landmarks on the frame
    
    Args:
        frame: BGR image
        pose_results: Results from MediaPipe pose detection
        
    Returns:
        Annotated frame with pose landmarks
    """
    if pose_results is None or pose_results.pose_landmarks is None:
        return frame
    
    annotated = frame.copy()
    
    try:
        # Draw pose landmarks
        mp_drawing.draw_landmarks(
            annotated,
            pose_results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )
    except Exception as e:
        print(f"Drawing error: {e}")
    
    return annotated

def analyze_pose(pose_results: object) -> dict:
    """
    Analyze pose characteristics (standing, sitting, etc.)
    
    Args:
        pose_results: Results from MediaPipe pose detection
        
    Returns:
        Dictionary with pose analysis
    """
    if pose_results is None or pose_results.pose_landmarks is None:
        return {
            "present": False,
            "posture": "unknown",
            "confidence": 0.0
        }
    
    landmarks = pose_results.pose_landmarks.landmark
    
    # Get key points
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    
    # Calculate average visibility
    visibility = np.mean([
        left_shoulder.visibility,
        right_shoulder.visibility,
        left_hip.visibility,
        right_hip.visibility
    ])
    
    # Estimate posture based on vertical alignment
    shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
    hip_y = (left_hip.y + right_hip.y) / 2
    knee_y = (left_knee.y + right_knee.y) / 2
    
    # Simple posture classification
    torso_length = hip_y - shoulder_y
    leg_length = knee_y - hip_y
    
    if torso_length > 0 and leg_length > 0:
        posture = "standing" if leg_length > torso_length * 0.8 else "sitting"
    else:
        posture = "unknown"
    
    return {
        "present": True,
        "posture": posture,
        "confidence": float(visibility),
        "landmarks_count": len(landmarks)
    }

def detect_guard_with_pose(frame: np.ndarray, draw_landmarks: bool = True) -> Tuple[np.ndarray, dict]:
    """
    Combined function: detect guard presence and return annotated frame with analysis
    
    Args:
        frame: Input BGR frame
        draw_landmarks: Whether to draw pose landmarks on frame
        
    Returns:
        Tuple of (annotated_frame, analysis_dict)
    """
    is_present, pose_results = is_guard_present(frame)
    
    annotated_frame = frame.copy()
    
    if is_present and draw_landmarks:
        annotated_frame = draw_pose_landmarks(annotated_frame, pose_results)
    
    analysis = analyze_pose(pose_results)
    
    # Add text overlay
    if is_present:
        status_text = f"Guard: {analysis['posture'].upper()} ({analysis['confidence']:.2f})"
        color = (0, 255, 0)
    else:
        status_text = "No Guard Detected"
        color = (0, 0, 255)
    
    cv2.putText(
        annotated_frame,
        status_text,
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2
    )
    
    return annotated_frame, analysis

# Test function
if __name__ == "__main__":
    print("🧍 Testing MediaPipe Pose Detection...")
    
    cap = cv2.VideoCapture(0)
    
    print("Press 'q' to quit")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        annotated, analysis = detect_guard_with_pose(frame)
        
        cv2.imshow('Guard Pose Detection', annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    pose.close()
