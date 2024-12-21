import cv2
import mediapipe as mp
import numpy as np

# Initialize Mediapipe Hands and drawing utilities
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Normalize landmarks to handle variations in hand position and orientation
def normalize_landmarks(landmarks):
    if landmarks:
        base_x, base_y, _ = landmarks[0]  # Use the wrist (landmark 0) as the origin
        normalized_landmarks = []
        for x, y, z in landmarks:
            normalized_landmarks.append((x - base_x, y - base_y, z))
        return normalized_landmarks
    return landmarks

# Define a function to classify rock, paper, scissors gestures
def classify_hand_landmarks(landmarks):
    if landmarks:
        # Normalize landmarks
        landmarks = normalize_landmarks(landmarks)

        # Extract landmark points
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]

        # Extract middle points for each finger
        index_middle_point = landmarks[7]
        middle_middle_point = landmarks[11]
        ring_middle_point = landmarks[15]
        pinky_middle_point = landmarks[19]

        # Check if fingers are up
        fingers_up = {
            'index': index_tip[1] < index_middle_point[1],
            'middle': middle_tip[1] < middle_middle_point[1],
            'ring': ring_tip[1] < ring_middle_point[1],
            'pinky': pinky_tip[1] < pinky_middle_point[1]
        }

        # Logic for gestures
        if not any(fingers_up.values()):
            return "Rock"
        elif fingers_up['index'] and fingers_up['middle'] and not fingers_up['ring'] and not fingers_up['pinky']:
            return "Scissors"
        elif all(fingers_up.values()):
            return "Paper"
    return "Unknown"