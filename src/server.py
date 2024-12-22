import socket
from _thread import *
import json
import time
from utils import get_local_ip

class GameState:
    def __init__(self):
        self.clients = {}
        self.ready_players = set()
        self.choices = {}
        self.scores = {
            1: {"wins": 0, "losses": 0, "draws": 0},
            2: {"wins": 0, "losses": 0, "draws": 0}
        }
        self.game_started = False
        self.countdown_active = False
        self.round_in_progress = False

    def to_dict(self):
        return {
            "type": "game_state",
            "players_connected": len(self.clients),
            "ready_players": list(self.ready_players),
            "game_started": self.game_started,
            "countdown_active": self.countdown_active,
            "round_in_progress": self.round_in_progress,
            "scores": self.scores,
            "choices": self.choices
        }

class GameServer:
    def __init__(self, host=get_local_ip(), port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        self.game_state = GameState()
        print("Server Started. Waiting for clients to connect...")

    def broadcast(self, message):
        """Send message to all clients"""
        message_str = json.dumps(message) + '\n'
        message_bytes = message_str.encode()
        
        disconnected = []
        for player_id, client in self.game_state.clients.items():
            try:
                client.send(message_bytes)
            except:
                disconnected.append(player_id)
        
        # Clean up disconnected clients
        for player_id in disconnected:
            self.handle_disconnect(player_id)

    def handle_disconnect(self, player_id):
        """Handle client disconnection"""
        if player_id in self.game_state.clients:
            del self.game_state.clients[player_id]
        if player_id in self.game_state.ready_players:
            self.game_state.ready_players.remove(player_id)
        self.game_state.round_in_progress = False
        self.game_state.countdown_active = False
        self.broadcast(self.game_state.to_dict())

    def handle_client(self, conn, player_id):
        """Handle individual client connection"""
        # Send welcome message
        welcome = {
            "type": "welcome",
            "player_id": player_id,
            "message": f"Welcome Player {player_id}"
        }
        conn.send((json.dumps(welcome) + '\n').encode())

        # Store the client connection
        self.game_state.clients[player_id] = conn
        
        # Broadcast updated game state to all clients
        self.broadcast(self.game_state.to_dict())

        while True:
            try:
                data = conn.recv(2048).decode()
                if not data:
                    break

                messages = data.split('\n')
                for message in messages:
                    if not message:
                        continue
                    
                    try:
                        data = json.loads(message)
                        self.handle_message(player_id, data)
                    except json.JSONDecodeError:
                        continue

            except:
                break

        self.handle_disconnect(player_id)

    def handle_message(self, player_id, data):
        """Process messages from clients"""
        msg_type = data.get("type")
        
        if msg_type == "ready":
            if not self.game_state.round_in_progress:
                if player_id in self.game_state.ready_players:
                    self.game_state.ready_players.remove(player_id)
                else:
                    self.game_state.ready_players.add(player_id)

                if len(self.game_state.ready_players) == 2 and len(self.game_state.clients) == 2:
                    self.game_state.game_started = True
                    self.game_state.countdown_active = True
                    self.game_state.round_in_progress = True
                    
                self.broadcast(self.game_state.to_dict())

        elif msg_type == "choice":
            self.game_state.choices[player_id] = data["choice"]
            
            if len(self.game_state.choices) == 2:
                # Determine winner and update scores
                result = self.determine_winner(
                    self.game_state.choices.get(1),
                    self.game_state.choices.get(2)
                )
                self.update_scores(result)
                
                # Broadcast result
                self.broadcast({
                    "type": "result",
                    "message": result,
                    "choices": self.game_state.choices,
                    "scores": self.game_state.scores
                })
                
                # Reset for next round
                self.game_state.choices.clear()
                self.game_state.game_started = False
                self.game_state.countdown_active = False
                self.game_state.round_in_progress = False
                self.game_state.ready_players.clear()
                
                self.broadcast(self.game_state.to_dict())

    def determine_winner(self, p1_choice, p2_choice):
        if p1_choice == p2_choice:
            return "Draw"
        elif (p1_choice == "rock" and p2_choice == "scissors") or \
             (p1_choice == "paper" and p2_choice == "rock") or \
             (p1_choice == "scissors" and p2_choice == "paper"):
            return "Player 1 Wins"
        else:
            return "Player 2 Wins"

    def update_scores(self, result):
        if result == "Draw":
            self.game_state.scores[1]["draws"] += 1
            self.game_state.scores[2]["draws"] += 1
        elif result == "Player 1 Wins":
            self.game_state.scores[1]["wins"] += 1
            self.game_state.scores[2]["losses"] += 1
        else:
            self.game_state.scores[1]["losses"] += 1
            self.game_state.scores[2]["wins"] += 1

    def run(self):
        """Main server loop"""
        while True:
            conn, addr = self.server.accept()
            if len(self.game_state.clients) < 2:
                player_id = len(self.game_state.clients) + 1
                print(f"Player {player_id} connected from: {addr}")
                start_new_thread(self.handle_client, (conn, player_id))
            else:
                conn.send(json.dumps({
                    "type": "error",
                    "message": "Server is full"
                }).encode())
                conn.close()

if __name__ == "__main__":
    server = GameServer()
    server.run()