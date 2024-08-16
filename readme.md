# Rock Paper Scissors Game

This is my final project for CKCS149 DCY - Python Programming - P2024.

I created a Pygame-based Rock Paper Scissors game that utilizes the Ultralytics YOLOv8 model for image classification. My name is Rolex Antoine Alexander. Lecturer: Dr. Mihal Miu.

## How to Run the Game

1. Ensure your environment has access to a camera and Python installed.
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the game:
   ```
   python game.py
   ```
   or
   ```
   python3 game.py
   ```
   After running the game, press `Tab` to play.

## Game Overview

The game uses your camera to capture an image of your hand and classifies it as either "rock," "paper," or "scissors" using the YOLOv8 model. The computer then randomly selects its own choice, and the result is displayed on the screen.

## Training the Model

The model was initially trained using a publicly available dataset. You can find the dataset used for training [here](https://www.kaggle.com/datasets/sanikamal/rock-paper-scissors-dataset).

## Code Summary

- **Pygame Integration**: The game leverages Pygame for the graphical interface, handling everything from the game loop to rendering images and text.
- **YOLOv8 Model**: The Ultralytics YOLOv8 model is employed to classify images of the user's hand, identifying the user's choice as "rock," "paper," or "scissors."
- **Gameplay Logic**: The game logic includes tracking the player's and computer's wins, losses, and draws. The game starts when the user presses the Tab key and ends after each round, displaying the result.

## Disclaimer

**Note**: The current YOLOv8 model is overfitted and only predicts "scissors." Future improvements will involve curating our own dataset to create a more accurate and versatile model.