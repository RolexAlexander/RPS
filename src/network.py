# network.py
import socket
import json
import threading
import os
import sys

# Add the root directory to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)

# Now you can import from src
from src.utils import get_local_ip

# Define the Network class
class Network:
    def __init__(self, host=get_local_ip(), port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = host # ip of server
        self.port = port
        self.addr = (self.server, self.port)
        self.player_id = None
        self.game_state = {
            "players_connected": 0,
            "ready_players": [],
            "game_started": False,
            "countdown_active": False,
            "round_in_progress": False,
            "scores": {
                1: {"wins": 0, "losses": 0, "draws": 0},
                2: {"wins": 0, "losses": 0, "draws": 0}
            },
            "choices": {}
        }
        self.message_callback = None
        self.running = False
        self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            response = self.client.recv(2048).decode()
            welcome_data = json.loads(response)
            if welcome_data.get("type") == "welcome":
                self.player_id = welcome_data.get("player_id")
                print(f"Connected as Player {self.player_id}")
                
                # Process any remaining data in the buffer
                remaining_data = response[response.find('\n')+1:]
                if remaining_data:
                    self._process_data(remaining_data)
                
                # Start listening thread
                self.running = True
                self.receive_thread = threading.Thread(target=self._listen)
                self.receive_thread.daemon = True
                self.receive_thread.start()
                return True
            return False
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def _process_data(self, data):
        """Process received data and update game state"""
        messages = data.split('\n')
        for message in messages:
            if message:
                try:
                    parsed_data = json.loads(message)
                    self._update_game_state(parsed_data)
                    if self.message_callback:
                        self.message_callback(parsed_data)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    continue

    def _listen(self):
        """Background thread to listen for server messages"""
        buffer = ""
        while self.running:
            try:
                data = self.client.recv(2048).decode()
                if not data:
                    break
                
                buffer += data
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    if message:
                        try:
                            parsed_data = json.loads(message)
                            self._update_game_state(parsed_data)
                            if self.message_callback:
                                self.message_callback(parsed_data)
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")
                            continue
                    
            except Exception as e:
                print(f"Listen error: {e}")
                break
        
        self.running = False
        print("Disconnected from server")

    def _update_game_state(self, data):
        """Update internal game state based on server message"""
        if data.get("type") == "game_state":
            # Update all game state fields
            self.game_state["players_connected"] = data.get("players_connected", self.game_state["players_connected"])
            self.game_state["ready_players"] = data.get("ready_players", self.game_state["ready_players"])
            self.game_state["game_started"] = data.get("game_started", self.game_state["game_started"])
            self.game_state["countdown_active"] = data.get("countdown_active", self.game_state["countdown_active"])
            self.game_state["round_in_progress"] = data.get("round_in_progress", self.game_state["round_in_progress"])
            if "scores" in data:
                self.game_state["scores"] = data["scores"]
            if "choices" in data:
                self.game_state["choices"] = data["choices"]
        
        elif data.get("type") == "result":
            if "scores" in data:
                self.game_state["scores"] = data["scores"]
            if "choices" in data:
                self.game_state["choices"] = data["choices"]

    def send(self, data):
        """Send data to server"""
        try:
            message = json.dumps(data) + '\n'
            self.client.send(message.encode())
            return True
        except Exception as e:
            print(f"Send error: {e}")
            return False

    def set_callback(self, callback):
        self.message_callback = callback

    def get_player_id(self):
        return self.player_id

    def get_game_state(self):
        return self.game_state

    def set_ready(self):
        return self.send({"type": "ready"})

    def make_choice(self, choice):
        return self.send({"type": "choice", "choice": choice})

    def disconnect(self):
        self.running = False
        try:
            self.client.close()
        except:
            pass