import pygame
import pygame.camera
import time
import json
import os
import sys
import datetime
import numpy as np
import mediapipe as mp
import cv2
import random
from ultralytics import YOLO

# Add the root directory to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)

from src.network import Network
from src.utils import classify_hand_landmarks, load_env


# Load environment variables from .env file
load_env(".env")

# Initialize Pygame
pygame.init()
pygame.camera.init()

# Start camera
cam = pygame.camera.Camera(0, (640, 480))
# cam.start()

# Initialize YOLO model this is not accurate enough i replaced it with mediapipe
# model = 'YOLO("./models/rps.pt")'

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rock Paper Scissors Multiplayer")

# Initialize Mediapipe Hands and drawing utilities
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (100, 100, 100)
SHADOW_COLOR = (50, 50, 50, 100)

# Load images
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


def main():
    # grab server ip and port from env
    server_ip = os.getenv("SERVER_IP")
    server_port = os.getenv("SERVER_PORT")

    # Initialize Network
    network = Network(host=str(server_ip), port=int(server_port))

    if not network.get_player_id():
        print("Failed to connect to server")
        return

    clock = pygame.time.Clock()
    run = True
    playing = False
    countdown = 3
    waiting_for_results = False
    user_choice = None
    opponent_choice = None
    result_text = ""
    player_ready = False
    last_state_request = 0
    countdown_started = False
    last_countdown_update = 0
    state_request_interval = 100  # milliseconds
    clock = pygame.time.Clock()
    run = True
    playing = False
    countdown = 3
    waiting_for_results = False
    opponent_choice = None
    result_text = ""
    player_ready = False
    countdown_started = False
    scores = {}
    player_scores = {"wins": 0, "losses": 0, "draws": 0}
    opponent_scores = {"wins": 0, "losses": 0, "draws": 0}
    ready_players = []
    player_ready = network.get_player_id() in ready_players
    opponent_ready = (3 - network.get_player_id()) in ready_players
    players_connected = 0
    round_in_progress = False
    
    # Replace the existing game state update logic with:
    def handle_game_update(data):
        nonlocal playing, countdown, waiting_for_results, user_choice
        nonlocal opponent_choice, result_text, player_ready, countdown_started
        nonlocal players_connected, opponent_ready, player_scores, opponent_scores
        
        if data["type"] == "game_state":
            # Update connection and ready status
            players_connected = data.get("players_connected", 0)
            ready_players = data.get("ready_players", [])
            player_ready = network.get_player_id() in ready_players
            opponent_ready = (3 - network.get_player_id()) in ready_players
            
            # Update scores
            scores = data.get("scores", {})
            if scores:
                player_id = str(network.get_player_id())
                opponent_id = str(3 - network.get_player_id())
                if player_id in scores:
                    player_scores = scores[player_id]
                if opponent_id in scores:
                    opponent_scores = scores[opponent_id]

            if not data.get("round_in_progress"):
                playing = False
                countdown = -1
                countdown_started = False
            elif data.get("countdown_active") and not countdown_started:
                countdown = 3
                countdown_started = True
                playing = True
                
        elif data["type"] == "result":
            result_text = data["message"]
            choices = data.get("choices", {})
            opponent_choice = choices.get(str(3 - network.get_player_id()))
            waiting_for_results = False
            playing = False
            countdown = -1
            countdown_started = False
            player_ready = False
            
            # Update scores from result
            scores = data.get("scores", {})
            if scores:
                player_id = str(network.get_player_id())
                opponent_id = str(3 - network.get_player_id())
                if player_id in scores:
                    player_scores = scores[player_id]
                if opponent_id in scores:
                    opponent_scores = scores[opponent_id]
                    
    # Set the callback for network updates
    network.set_callback(handle_game_update)

    # Main game loop        
    while run:
        current_time = pygame.time.get_ticks()
        screen.blit(background_img, (0, 0))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB and not playing and not waiting_for_results:
                    network.set_ready()
    
        # Draw UI elements
        pygame.draw.rect(screen, LIGHT_GRAY, (0, 0, WIDTH, 80))
        pygame.draw.rect(screen, SHADOW_COLOR, (0, 80, WIDTH, 10))
        pygame.draw.line(screen, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 2)

        # Display player profiles and labels
        screen.blit(user_profile_img, (20, 5))
        screen.blit(computer_profile_img, (WIDTH - profile_size - 20, 5))
        
        player_label = small_font.render(f"Player {network.get_player_id()}", True, WHITE)
        opponent_label = small_font.render(f"Player {3 - network.get_player_id()}", True, WHITE)
        screen.blit(player_label, (20, profile_size + 15))
        screen.blit(opponent_label, (WIDTH - profile_size - opponent_label.get_width() - 20, profile_size + 15))

        # Display scores
        # Player scores
        screen.blit(win_icon, (120, 25))
        win_count_surface = small_font.render(f"x{player_scores['wins']}", True, BLACK)
        screen.blit(win_count_surface, (150, 25))

        screen.blit(loss_icon, (200, 25))
        loss_count_surface = small_font.render(f"x{player_scores['losses']}", True, BLACK)
        screen.blit(loss_count_surface, (230, 25))

        screen.blit(draw_icon, (280, 25))
        draw_count_surface = small_font.render(f"x{player_scores['draws']}", True, BLACK)
        screen.blit(draw_count_surface, (310, 25))

        # Opponent scores
        screen.blit(win_icon, (WIDTH - 360, 25))
        opponent_win_count_surface = small_font.render(f"x{opponent_scores['wins']}", True, BLACK)
        screen.blit(opponent_win_count_surface, (WIDTH - 330, 25))

        screen.blit(loss_icon, (WIDTH - 270, 25))
        opponent_loss_count_surface = small_font.render(f"x{opponent_scores['losses']}", True, BLACK)
        screen.blit(opponent_loss_count_surface, (WIDTH - 240, 25))

        screen.blit(draw_icon, (WIDTH - 180, 25))
        opponent_draw_count_surface = small_font.render(f"x{opponent_scores['draws']}", True, BLACK)
        screen.blit(opponent_draw_count_surface, (WIDTH - 150, 25))

        # Display status messages
        player_status_text = "Ready" if player_ready else "Not Ready"
        opponent_status_text = "Ready" if opponent_ready else "Not Ready"
        if not players_connected == 2:
            opponent_status_text = "Waiting for opponent..."
        
        player_status_surface = small_font.render(player_status_text, True, WHITE)
        opponent_status_surface = small_font.render(opponent_status_text, True, WHITE)
        screen.blit(player_status_surface, (20, profile_size + 40))
        screen.blit(opponent_status_surface, (WIDTH - profile_size - opponent_status_surface.get_width() - 20, profile_size + 40))

        # Handle game logic
        # Update the countdown display logic
        if playing and not waiting_for_results and countdown_started:
            if countdown > 0:
                countdown_text = str(countdown)
                countdown_surface = font.render(countdown_text, True, WHITE)
                countdown_x = WIDTH // 2 - countdown_surface.get_width() // 2
                countdown_y = HEIGHT // 2 - countdown_surface.get_height() // 2
                screen.blit(countdown_surface, (countdown_x, countdown_y))

                # Update countdown every second without blocking
                if current_time - last_countdown_update > 1000:  # 1000 ms = 1 second
                    last_countdown_update = current_time
                    countdown -= 1
            elif countdown == 0:
                user_choice = detect_user_choice()
                network.make_choice(user_choice)
                waiting_for_results = True
                countdown = -1
                countdown_started = False

        # Display choices
        if user_choice:
            user_img = globals()[f"{user_choice}_img"]
            screen.blit(user_img, (WIDTH // 4 - choice_size // 2, 200))
        if opponent_choice:
            opponent_img = globals()[f"{opponent_choice}_img"]
            screen.blit(opponent_img, (3 * WIDTH // 4 - choice_size // 2, 200))

        # Display result text
        if result_text:
            result_surface = font.render(result_text, True, WHITE)
            screen.blit(result_surface, ((WIDTH - result_surface.get_width()) // 2, HEIGHT - 100))

        # Display play again prompt
        # if not playing and countdown == -1 and not waiting_for_results:
        #     prompt_surface = small_font.render("Press Tab to Play Again", True, GRAY)
        #     screen.blit(prompt_surface, ((WIDTH - prompt_surface.get_width()) // 2, HEIGHT - 50))

        # Display initial game prompt
        if not player_ready and not playing and not waiting_for_results:
            prompt_surface = small_font.render("Press Tab to Play", True, GRAY)
            screen.blit(prompt_surface, ((WIDTH - prompt_surface.get_width()) // 2, HEIGHT - 50))
        elif not playing and not waiting_for_results:
            prompt_surface = small_font.render("Waiting for opponent...", True, GRAY)
            screen.blit(prompt_surface, ((WIDTH - prompt_surface.get_width()) // 2, HEIGHT - 50))

        pygame.display.update()
        # clock.tick(60)
        # clock.tick(30)

    network.disconnect()
    pygame.quit()

if __name__ == "__main__":
    main()