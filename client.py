from pygame import *
import socket
import json
from threading import Thread
import os 

# ---ПУГАМЕ НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
init()
mixer.init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Пong")

# --- РОЗМІРИ ОБ'ЄКТІВ ---
PADDLE_W = 130
PADDLE_H = 300
BALL_RADIUS = 50
BALL_DIAMETER = BALL_RADIUS * 2
PADDLE_X_OFFSET = 20

P1_DRAW_X = PADDLE_X_OFFSET
P2_DRAW_X = WIDTH - PADDLE_X_OFFSET - PADDLE_W

# ---СЕРВЕР ---
def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 5052)) 
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass

def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break

# --- ШРИФТИ ---
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)

# --- ЗОБРАЖЕННЯ ----
IMAGE_PATH = "images" 
use_images = True 

try:
    background_img = image.load(os.path.join(IMAGE_PATH, "riatsun_background.jpg")).convert()
    background_img = transform.scale(background_img, (WIDTH, HEIGHT))
    
    paddle1_img = image.load(os.path.join(IMAGE_PATH, "riatsun_paddle1.png")).convert_alpha()
    paddle1_img = transform.scale(paddle1_img, (PADDLE_W, PADDLE_H)) 
    
    paddle2_img = image.load(os.path.join(IMAGE_PATH, "riatsun_paddle2.png")).convert_alpha()
    paddle2_img = transform.scale(paddle2_img, (PADDLE_W, PADDLE_H)) 
    
    ball_img = image.load(os.path.join(IMAGE_PATH, "riatsun_ball.png")).convert_alpha()
    ball_img = transform.scale(ball_img, (BALL_DIAMETER, BALL_DIAMETER)) 

except FileNotFoundError as e:
    print(f"ПОМИЛКА: Не знайдено картинку! {e}")
    print("Гра буде малювати прості фігури замість картинок.")
    use_images = False 

# --- ЗВУКИ ---
mixer.music.load(os.path.join("sounds", "riatsun_music.ogg"))
wall_hit_sound = mixer.Sound(os.path.join("sounds", "riatsun_hit.wav"))
platform_hit_sound = mixer.Sound(os.path.join("sounds", "riatsun_wallhit.wav"))
win_sound = mixer.Sound(os.path.join("sounds", "riatsun_win.wav"))
lose_sound = mixer.Sound(os.path.join("sounds", "riatsun_lose.wav"))

mixer.music.set_volume(0.3)

# --- ГРА ---
game_over = False
winner = None
you_winner = None
my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()

mixer.music.play(-1) 

while True:
    for e in event.get():
        if e.type == QUIT:
            exit()

    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.fill((0, 0, 0))
        countdown_text = font.Font(None, 72).render(str(game_state["countdown"]), True, (255, 255, 255))
        screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
        display.update()
        continue 

    if "winner" in game_state and game_state["winner"] is not None:
        screen.fill((20, 20, 20))

        if you_winner is None: 
            mixer.music.stop() 
            
            if game_state["winner"] == my_id:
                you_winner = True
                win_sound.play() 
            else:
                you_winner = False
                lose_sound.play() 

        if you_winner:
            text = "Ти переміг!"
        else:
            text = "Пощастить наступним разом!"

        win_text = font_win.render(text, True, (255, 215, 0))
        text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(win_text, text_rect)

        text = font_win.render('К - рестарт', True, (255, 215, 0))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
        screen.blit(text, text_rect)

        display.update()
        continue 

    if game_state:
        if use_images: 
            screen.blit(background_img, (0, 0)) 
            screen.blit(paddle1_img, (P1_DRAW_X, game_state['paddles']['0']))
            screen.blit(paddle2_img, (P2_DRAW_X, game_state['paddles']['1']))
            
            ball_x = game_state['ball']['x'] - (ball_img.get_width() // 2)
            ball_y = game_state['ball']['y'] - (ball_img.get_height() // 2)
            screen.blit(ball_img, (ball_x, ball_y))

        else:
            screen.fill((30, 30, 30))
            draw.rect(screen, (0, 255, 0), (P1_DRAW_X, game_state['paddles']['0'], PADDLE_W, PADDLE_H))
            draw.rect(screen, (255, 0, 255), (P2_DRAW_X, game_state['paddles']['1'], PADDLE_W, PADDLE_H))
            draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), BALL_RADIUS)
        
        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 -25, 20))

        if game_state['sound_event']:
            if game_state['sound_event'] == 'wall_hit':
                wall_hit_sound.play() 
            if game_state['sound_event'] == 'platform_hit':
                platform_hit_sound.play() 
            
            game_state['sound_event'] = None 

    else:
        if use_images:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill((30, 30, 30))
            
        wating_text = font_main.render(f"Очікування гравців...", True, (255, 255, 255))
        screen.blit(wating_text, (WIDTH // 2 - 25, 20))

    display.update()
    clock.tick(60)

    keys = key.get_pressed()
    if keys[K_w]:
        client.send(b"UP")
    elif keys[K_s]:
        client.send(b"DOWN")