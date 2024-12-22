import cv2
import json
import os
import socket
import logging
import mediapipe as mp
import numpy as np
from typing import List, Dict, Optional, Tuple
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage
from azure.core.credentials import AzureKeyCredential


# Function to load env cause dotenv is not working in the windows environment and i can't switch because i dont have camera access in the wsl ubuntu environment
def load_env(file_path: str):
    """
    Load environment variables from a .env file.
    :param file_path: Path to the .env file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist.")
    with open(file_path, "r") as file:
        for line in file:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                os.environ[key] = value
                
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

# Function to play rock paper scissors against openai models
def run_rock_paper_scissors_openai_model(
        prompt: str = """
            You are the best rock-paper-scissors player in the world, and you are in the finals against the user. Your goal is to win the game. Below is the history of the previous rounds. In each round, "AI" represents your choice, "User" represents the user's choice, and "Result" shows who won.

            History:
            None

            Analyze the user's past choices and any patterns you observe. Then, decide your next move: Rock, Paper, or Scissors. Your goal is to maximize your chances of winning. If no clear pattern is visible, make a logical guess to counter the user's most likely next move.

            Respond in the following format:
            Choice: [Your choice]
            Reason: [Your reasoning for the choice]
        """, 
        model_name: str = "gpt-4o", 
        api_key: str = "", 
        tools: List[Dict] = [
            {
                "type": "function", 
                "function": {
                    "name": "play_rock_paper_scissors",
                    "type": "function",
                    "description": "Play Rock-Paper-Scissors against the user by analyzing the history of moves to maximize the AI's chances of winning.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "Choice": {
                                "type": "string",
                                "description": "The choice the AI makes to play, considering the given history and strategy.",
                                "enum": ["Rock", "Paper", "Scissors"]
                            },
                            "Reason": {
                                "type": "string",
                                "description": "The explanation of why the AI chose this move, considering patterns and strategy."
                            }
                        },
                        "required": ["Choice", "Reason"]
                    }
                }
            }
        ],
        tool_choice: dict = {"type": "function", "function": {"name": "play_rock_paper_scissors"}}
    ) -> Dict:
    """
    Run a Rock-Paper-Scissors model with the given parameters.

    :param prompt: The prompt describing the functionality.
    :param model_name: The name of the model to use.
    :param api_key: The API key for authentication.
    :param tools: The tools required for the model.
    :return: The response from the model.
    """

    # Initialize the client
    client = ChatCompletionsClient(
        endpoint="https://models.inference.ai.azure.com",
        credential=AzureKeyCredential(api_key),
    )

    # Make the request
    response = client.complete(
        messages=[
            SystemMessage(content=prompt)
        ],
        model=model_name,
        temperature=1,
        max_tokens=4096,
        top_p=1,
        tools=tools,
        tool_choice=tool_choice
    )


    # Extract the function arguments from the response
    try:
        tool_calls = response["choices"][0]["message"]["tool_calls"]
        function_arguments = tool_calls[0]["function"]["arguments"]
        function_arguments_json = json.loads(function_arguments)

        # Log the response to logs/log.json
        log_file_path = "logs/log.json"
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as log_file:
                logs = json.load(log_file)
        else:
            logs = []

        logs.append(function_arguments_json)

        with open(log_file_path, "w") as log_file:
            json.dump(logs, log_file, indent=4)

        return function_arguments_json
    except (KeyError, IndexError, json.JSONDecodeError):
        raise ValueError("Failed to extract function arguments from response.")
    
# Function to play rock paper scissors against openai models
def run_rock_paper_scissors_ai_vs_ai_openai_model(
        name: str = "AI1",
        prompt: str = """
            You are the best rock-paper-scissors player in the world, and you are in the finals against the user. Your goal is to win the game. Below is the history of the previous rounds. In each round, "AI" represents your choice, "User" represents the user's choice, and "Result" shows who won.

            History:
            None

            Analyze the user's past choices and any patterns you observe. Then, decide your next move: Rock, Paper, or Scissors. Your goal is to maximize your chances of winning. If no clear pattern is visible, make a logical guess to counter the user's most likely next move.

            Respond in the following format:
            Choice: [Your choice]
            Reason: [Your reasoning for the choice]
        """, 
        model_name: str = "gpt-4o", 
        api_key: str = "", 
        tools: List[Dict] = [
            {
                "type": "function", 
                "function": {
                    "name": "play_rock_paper_scissors",
                    "type": "function",
                    "description": "Play Rock-Paper-Scissors against the user by analyzing the history of moves to maximize the AI's chances of winning.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "Choice": {
                                "type": "string",
                                "description": "The choice the AI makes to play, considering the given history and strategy.",
                                "enum": ["Rock", "Paper", "Scissors"]
                            },
                            "Reason": {
                                "type": "string",
                                "description": "The explanation of why the AI chose this move, considering patterns and strategy."
                            }
                        },
                        "required": ["Choice", "Reason"]
                    }
                }
            }
        ],
        tool_choice: dict = {"type": "function", "function": {"name": "play_rock_paper_scissors"}}
    ) -> Dict:
    """
    Run a Rock-Paper-Scissors model with the given parameters.

    :param prompt: The prompt describing the functionality.
    :param model_name: The name of the model to use.
    :param api_key: The API key for authentication.
    :param tools: The tools required for the model.
    :return: The response from the model.
    """

    # Initialize the client
    client = ChatCompletionsClient(
        endpoint="https://models.inference.ai.azure.com",
        credential=AzureKeyCredential(api_key),
    )

    # Make the request
    response = client.complete(
        messages=[
            SystemMessage(content=prompt)
        ],
        model=model_name,
        temperature=1,
        max_tokens=4096,
        top_p=1,
        tools=tools,
        tool_choice=tool_choice
    )


    # Extract the function arguments from the response
    try:
        tool_calls = response["choices"][0]["message"]["tool_calls"]
        function_arguments = tool_calls[0]["function"]["arguments"]
        function_arguments_json = json.loads(function_arguments)
        function_arguments_json["Name"] = name

        # Log the response to logs/log.json
        log_file_path = "logs/log.json"
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as log_file:
                logs = json.load(log_file)
        else:
            logs = []

        logs.append(function_arguments_json)

        with open(log_file_path, "w") as log_file:
            json.dump(logs, log_file, indent=4)

        return function_arguments_json
    except (KeyError, IndexError, json.JSONDecodeError):
        raise ValueError("Failed to extract function arguments from response.")
    
def get_local_ip() -> Optional[str]:
    """
    Get the local IP address of the system that's suitable for LAN/network connections.
    Prioritizes non-localhost IPv4 addresses.
    
    Returns:
        str: The local IP address, or None if no suitable IP is found
    """
    try:
        # Fallback method if the above doesn't work
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't need to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    except Exception as e:
        logging.error(f"Error getting local IP: {str(e)}")
        return None