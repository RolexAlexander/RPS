import os
import sys
import cv2
import mediapipe as mp

# Add the root directory to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)

# Now you can import from src
from src.utils import classify_hand_landmarks


# Main function to capture camera feed and classify hand gestures
def main():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break

            # Flip the frame horizontally for a mirror view
            frame = cv2.flip(frame, 1)

            # Convert the frame to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process the frame for hand landmarks
            result = hands.process(rgb_frame)

            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    # Draw landmarks and connections on the screen
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Extract landmarks as a list of (x, y, z)
                    landmarks = [
                        (lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark
                    ]

                    # Classify the hand gesture
                    gesture = classify_hand_landmarks(landmarks)

                    # Display the gesture on the screen
                    cv2.putText(
                        frame,
                        f"Gesture: {gesture}",
                        (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                        cv2.LINE_AA,
                    )

            # Display the frame
            cv2.imshow("Rock Paper Scissors", frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
