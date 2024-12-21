import pygame
import pygame.camera
import random
import time
import json
import cv2
import os
import datetime
import numpy as np
import mediapipe as mp
from ultralytics import YOLO
from utils import classify_hand_landmarks

# Initialize Pygame
pygame.init()
pygame.camera.init()

# start camera
cam = pygame.camera.Camera(0, (640, 480))
cam.start()

# Initialize YOLO model Deprecated because model is not accurate enough
# model = YOLO("./models/rps_v0.1.pt")
# now using mediapipe

# Initialize Mediapipe Hands and drawing utilities
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rock Paper Scissors")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (100, 100, 100)
SHADOW_COLOR = (50, 50, 50, 100)  # Semi-transparent black for shadow

# Load images (placeholder paths, replace with actual image paths)
user_profile_img = pygame.image.load("data/assets/user_profile.png").convert_alpha()
computer_profile_img = pygame.image.load("data/assets/computer_profile.png").convert_alpha()
rock_img = pygame.image.load("data/assets/rock.png").convert_alpha()
paper_img = pygame.image.load("data/assets/paper.png").convert_alpha()
scissors_img = pygame.image.load("data/assets/scissors.png").convert_alpha()
background_img = pygame.image.load("data/assets/cover3.png").convert()
win_icon = pygame.image.load("data/assets/win.png").convert_alpha()
loss_icon = pygame.image.load("data/assets/loss.png").convert_alpha()
draw_icon = pygame.image.load("data/assets/draw.png").convert_alpha()

# Scale and transform images
profile_size = 70
icon_size = 30
user_profile_img = pygame.transform.scale(user_profile_img, (profile_size, profile_size))
computer_profile_img = pygame.transform.scale(computer_profile_img, (profile_size, profile_size))
win_icon = pygame.transform.scale(win_icon, (icon_size, icon_size))
loss_icon = pygame.transform.scale(loss_icon, (icon_size, icon_size))
draw_icon = pygame.transform.scale(draw_icon, (icon_size, icon_size))

# Making profile images round
def make_round(image, size):
    round_surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.ellipse(round_surface, (255, 255, 255), round_surface.get_rect(), 0)
    round_surface.blit(image, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return round_surface

user_profile_img = make_round(user_profile_img, (profile_size, profile_size))
computer_profile_img = make_round(computer_profile_img, (profile_size, profile_size))

choice_size = 150
rock_img = pygame.transform.scale(rock_img, (choice_size, choice_size))
paper_img = pygame.transform.scale(paper_img, (choice_size, choice_size))
scissors_img = pygame.transform.scale(scissors_img, (choice_size, choice_size))

# Font settings
font = pygame.font.SysFont(None, 55)
small_font = pygame.font.SysFont(None, 35)

# Capture and classify user choice
def detect_user_choice():
    # grab the image
    img = cam.get_image()

    # save the image 
    # # Convert Pygame surface to string buffer
    # buffer = pygame.image.tostring(screen_surface, "RGB")
    
    # # Get screen dimensions
    # width, height = screen_surface.get_size()
    
    # Convert to NumPy array and reshape to OpenCV image format
    # create a copy of the surface
    view = pygame.surfarray.array3d(img)

    # convert from (width, height, channel) to (height, width, channel)
    view = view.transpose([1, 0, 2])

    # convert from rgb to bgr
    img = cv2.cvtColor(view, cv2.COLOR_RGB2BGR)

    # Process the image with Mediapipe Hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
    result = hands.process(img)
    gesture = "Unknown"

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Convert landmarks to a list of (x, y, z) tuples
            landmarks = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]

            # Classify gesture
            gesture = classify_hand_landmarks(landmarks)

            # Annotate the image
            mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS, 
                                      mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=4),
                                      mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2))

    # If gesture is unknown, generate a random result
    if gesture == "Unknown":
        gesture = random.choice(["Rock", "Paper", "Scissors"])

    # Annotate the image with the result
    cv2.putText(img, f"Gesture: {gesture}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # Save the annotated image to the logs folder with a timestamp
    logs_folder = "logs"
    os.makedirs(logs_folder, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    annotated_path = os.path.join(logs_folder, f"gesture_{timestamp}.png")
    cv2.imwrite(annotated_path, img)

    hands.close()

    return gesture.lower()

# Main game function
def main():
    clock = pygame.time.Clock()
    run = True
    playing = False
    countdown = 3
    user_choice = None
    computer_choice = None
    result_text = ""
    user_wins, user_losses, user_draws = 0, 0, 0
    computer_wins, computer_losses, computer_draws = 0, 0, 0
    
    while run:
        # Keep background and layout in place
        screen.blit(background_img, (0, 0))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB and not playing:
                    # Start the game when Tab is pressed
                    playing = True
                    countdown = 3
                    user_choice = None
                    computer_choice = None
                    result_text = ""
        
        # Draw navbar background
        pygame.draw.rect(screen, LIGHT_GRAY, (0, 0, WIDTH, 80))

        # Draw shadow under the navbar
        pygame.draw.rect(screen, SHADOW_COLOR, (0, 80, WIDTH, 10))

        # Draw profiles in the top corners
        screen.blit(user_profile_img, (20, 5))
        screen.blit(computer_profile_img, (WIDTH - profile_size - 20, 5))
        
        # Draw metrics (Wins, Losses, Draws) as icons under each profile
        screen.blit(win_icon, (120, 25))
        win_count_surface = small_font.render(f"x{user_wins}", True, BLACK)
        screen.blit(win_count_surface, (150, 25))

        screen.blit(loss_icon, (200, 25))
        loss_count_surface = small_font.render(f"x{user_losses}", True, BLACK)
        screen.blit(loss_count_surface, (230, 25))

        screen.blit(draw_icon, (280, 25))
        draw_count_surface = small_font.render(f"x{user_draws}", True, BLACK)
        screen.blit(draw_count_surface, (310, 25))

        # Repeat the above for the computer's side
        screen.blit(win_icon, (WIDTH - 360, 25))
        win_count_surface = small_font.render(f"x{computer_wins}", True, BLACK)
        screen.blit(win_count_surface, (WIDTH - 330, 25))

        screen.blit(loss_icon, (WIDTH - 270, 25))
        loss_count_surface = small_font.render(f"x{computer_losses}", True, BLACK)
        screen.blit(loss_count_surface, (WIDTH - 240, 25))

        screen.blit(draw_icon, (WIDTH - 180, 25))
        draw_count_surface = small_font.render(f"x{computer_draws}", True, BLACK)
        screen.blit(draw_count_surface, (WIDTH - 150, 25))
        
        if not playing and countdown == 3:
            # Display "Press Tab to Play"
            prompt_surface = small_font.render("Press Tab to Play", True, GRAY)
            screen.blit(prompt_surface, ((WIDTH - prompt_surface.get_width()) // 2, HEIGHT - 50))
        
        # Display countdown
        if playing:
            # Countdown
            if countdown > 0:
                countdown_surface = font.render(str(countdown), True, WHITE)
                screen.blit(countdown_surface, ((WIDTH - countdown_surface.get_width()) // 2, (HEIGHT - countdown_surface.get_height()) // 2))
                pygame.display.update()
                time.sleep(1)
                countdown -= 1
            elif countdown == 0:
                # Capture user choice using the model
                user_choice = detect_user_choice()
                
                # AI random choice
                computer_choice = random.choice(["rock", "paper", "scissors"])
                
                # Determine result
                if user_choice == computer_choice:
                    result_text = "It's a Draw!"
                    user_draws += 1
                    computer_draws += 1
                elif (user_choice == "rock" and computer_choice == "scissors") or \
                     (user_choice == "paper" and computer_choice == "rock") or \
                     (user_choice == "scissors" and computer_choice == "paper"):
                    result_text = "You Win!"
                    user_wins += 1
                    computer_losses += 1
                else:
                    result_text = "You Lose!"
                    user_losses += 1
                    computer_wins += 1
                
                countdown = -1  # Stop the countdown
                playing = False  # End the round
            
        # Display user and computer choices
        if user_choice:
            user_img = globals()[f"{user_choice}_img"]
            screen.blit(user_img, (WIDTH // 4 - choice_size // 2, 200))
        
        if computer_choice:
            computer_img = globals()[f"{computer_choice}_img"]
            screen.blit(computer_img, (3 * WIDTH // 4 - choice_size // 2, 200))
        
        # Display result
        if result_text:
            result_surface = font.render(result_text, True, WHITE)
            screen.blit(result_surface, ((WIDTH - result_surface.get_width()) // 2, HEIGHT - 100))
        
        # Display play again prompt
        if not playing and countdown == -1:
            prompt_surface = small_font.render("Press Tab to Play Again", True, GRAY)
            screen.blit(prompt_surface, ((WIDTH - prompt_surface.get_width()) // 2, HEIGHT - 50))
        
        pygame.display.update()
        clock.tick(30)
    
    pygame.quit()

# Run the game
if __name__ == "__main__":
    main()