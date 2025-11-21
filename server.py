import socket
import json
import threading
import time
import random

WIDTH, HEIGHT = 800, 600
BALL_SPEED = 5
PADDLE_SPEED = 10
COUNTDOWN_START = 3

PADDLE_W = 60
PADDLE_H = 300
BALL_RADIUS = 60
PADDLE_X_OFFSET = 20
TOP_UI_HEIGHT = 60

P1_DRAW_X = PADDLE_X_OFFSET
P2_DRAW_X = WIDTH - PADDLE_X_OFFSET - PADDLE_W

P1_COLLISION_X = P1_DRAW_X + PADDLE_W
P2_COLLISION_X = P2_DRAW_X

class GameServer:
    def __init__(self, host='', port=5052):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        print("🎮 Server started")

        self.clients = {0: None, 1: None}
        self.connected = {0: False, 1: False}
        self.lock = threading.Lock()
        self.reset_game_state()
        self.sound_event = None

    def reset_game_state(self):
        self.paddles = {0: 250, 1: 250}
        self.scores = [0, 0]
        self.ball = {
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "vx": BALL_SPEED * random.choice([-1, 1]),
            "vy": BALL_SPEED * random.choice([-1, 1])
        }
        self.countdown = COUNTDOWN_START
        self.game_over = False
        self.winner = None

    def handle_client(self, pid):
        conn = self.clients[pid]
        try:
            while True:
                data = conn.recv(64).decode()
                with self.lock:
                    if data == "UP":
                        self.paddles[pid] = max(TOP_UI_HEIGHT, self.paddles[pid] - PADDLE_SPEED)
                    elif data == "DOWN":
                        self.paddles[pid] = min(HEIGHT - PADDLE_H, self.paddles[pid] + PADDLE_SPEED)
        except:
            with self.lock:
                self.connected[pid] = False
                self.game_over = True
                self.winner = 1 - pid 
                print(f"Гравець {pid} відключився. Переміг гравець {1 - pid}.")

    def broadcast_state(self):
        state = json.dumps({
            "paddles": self.paddles,
            "ball": self.ball,
            "scores": self.scores,
            "countdown": max(self.countdown, 0),
            "winner": self.winner if self.game_over else None,
            "sound_event": self.sound_event
        }) + "\n"
        for pid, conn in self.clients.items():
            if conn:
                try:
                    conn.sendall(state.encode())
                except:
                    self.connected[pid] = False

    def ball_logic(self):
        while self.countdown > 0:
            time.sleep(1)
            with self.lock:
                self.countdown -= 1
                self.broadcast_state()

        while not self.game_over:
            with self.lock:
                self.ball['x'] += self.ball['vx']
                self.ball['y'] += self.ball['vy']

                if self.ball['y'] <= TOP_UI_HEIGHT or self.ball['y'] >= HEIGHT - BALL_RADIUS:
                    self.ball['vy'] *= -1
                    self.sound_event = "wall_hit"

                if (self.ball['x'] <= P1_COLLISION_X and self.paddles[0] <= self.ball['y'] <= self.paddles[0] + PADDLE_H) or \
                   (self.ball['x'] >= P2_COLLISION_X and self.paddles[1] <= self.ball['y'] <= self.paddles[1] + PADDLE_H):
                    self.ball['vx'] *= -1
                    self.sound_event = 'platform_hit'

                if self.ball['x'] < 0:
                    self.scores[1] += 1
                    self.reset_ball()
                elif self.ball['x'] > WIDTH:
                    self.scores[0] += 1
                    self.reset_ball()

                if self.scores[0] >= 10:
                    self.game_over = True
                    self.winner = 0
                elif self.scores[1] >= 10:
                    self.game_over = True
                    self.winner = 1

                self.broadcast_state()
                self.sound_event = None
            time.sleep(0.016)

    def reset_ball(self):
        self.ball = {
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "vx": BALL_SPEED * random.choice([-1, 1]),
            "vy": BALL_SPEED * random.choice([-1, 1])
        }

    def accept_players(self):
        for pid in [0, 1]:
            print(f"Очікуємо гравця {pid}...")
            conn, _ = self.server.accept()
            self.clients[pid] = conn
            conn.sendall((str(pid) + "\n").encode())
            self.connected[pid] = True
            print(f"Гравець {pid} приєднався")
            threading.Thread(target=self.handle_client, args=(pid,), daemon=True).start()

    def run(self):
        while True:
            self.accept_players()
            self.reset_game_state()
            threading.Thread(target=self.ball_logic, daemon=True).start()

            while not self.game_over and all(self.connected.values()):
                time.sleep(0.1)

            print(f"Гравець {self.winner} переміг!")
            time.sleep(5)

            for pid in [0, 1]:
                try:
                    self.clients[pid].close()
                except:
                    pass
                self.clients[pid] = None
                self.connected[pid] = False

GameServer().run()