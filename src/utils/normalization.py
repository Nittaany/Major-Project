import numpy as np

def normalize_features(results):
    """
    Standardizes landmarks to be Scale-Invariant and Translation-Invariant.
    Logic:
    1. Center everything on the user's chest (Midpoint of shoulders).
    2. Scale everything by the width of the shoulders.
    """
    # 1. EXTRACT RAW LANDMARKS (Handle missing data with zeros)
    # We only take the top 25 pose landmarks (ignore legs to reduce noise)
    if results.pose_landmarks:
        pose = np.array([[res.x, res.y, res.z] for res in results.pose_landmarks.landmark[:25]])
    else:
        pose = np.zeros((25, 3))
        
    if results.left_hand_landmarks:
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark])
    else:
        lh = np.zeros((21, 3))

    if results.right_hand_landmarks:
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark])
    else:
        rh = np.zeros((21, 3))
    
    # 2. CALCULATE ANCHOR POINTS (Shoulders)
    # Pose Index 11 = Left Shoulder, 12 = Right Shoulder
    left_shoulder = pose[11]
    right_shoulder = pose[12]
    
    # Check if shoulders are actually detected
    if np.all(left_shoulder == 0) or np.all(right_shoulder == 0):
        # Fallback: Return raw data if body not found
        return np.concatenate([pose.flatten(), lh.flatten(), rh.flatten()])

    # 3. TRANSLATION INVARIANCE (Centering)
    # Find the center of the chest
    chest_center = (left_shoulder + right_shoulder) / 2.0
    
    # 4. SCALE INVARIANCE (Resizing)
    # Calculate shoulder width
    shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)
    
    # Safety check to avoid division by zero
    if shoulder_width < 0.01:
        shoulder_width = 1.0

    def standardize(landmarks):
        # (Coordinate - Center) / Width
        return (landmarks - chest_center) / shoulder_width

    # Apply to all groups
    pose_norm = standardize(pose).flatten()
    lh_norm = standardize(lh).flatten()
    rh_norm = standardize(rh).flatten()
    
    # Concatenate into one big vector (Size: 75 + 63 + 63 = 201)
    return np.concatenate([pose_norm, lh_norm, rh_norm])