import pygame
import random
from collections import deque
import threading

pygame.init()

WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Collect Coins Game")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 55)

player_img = pygame.image.load('player.png').convert_alpha()
coin_img = pygame.image.load('coin.png').convert_alpha()
obstacle_img = pygame.image.load('obstacle.png').convert_alpha()
spike_img = pygame.image.load('spike.png').convert_alpha()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GOLD = (255, 215, 0)


# Классы
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(player_img, (30, 30))
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.speed = 5

    def update(self, keys):
        old_rect = self.rect.copy()

        if keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_s]:
            self.rect.y += self.speed
        if keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_d]:
            self.rect.x += self.speed

        # Ограничение движения по границам окна
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT

        # Проверка столкновений с препятствиями
        if pygame.sprite.spritecollideany(self, obstacles):
            self.rect = old_rect


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(coin_img, (30, 30))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(obstacle_img, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Spike(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(spike_img, (30, 30))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)


def draw_input_box(surface, text, x, y, w, h, active):
    color = pygame.Color('lightskyblue3') if active else pygame.Color('gray15')
    pygame.draw.rect(surface, color, (x, y, w, h), 2)
    txt_surface = font.render(text, True, color)
    surface.blit(txt_surface, (x + 5, y + 5))


# Функция для поиска кратчайшего пути с использованием улучшенного BFS
def bfs_path(start, goal, obstacles):
    queue = deque([start])
    visited = set()
    visited.add(start)
    parent = {start: None}

    goal = tuple(
        [
            goal[0] // 5 * 5,
            goal[1] // 5 * 5
        ]
    )

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        x, y = current

        neighbors = []
        for variant in range(2, 5):
            for way in (x - variant * 5, y), (x + variant * 5, y), (x, y - variant * 5), (x, y + variant * 5):
                neighbors.append(way)

        for neighbor in neighbors:
            if (0 <= neighbor[0] < WIDTH and 0 <= neighbor[1] < HEIGHT and
                    neighbor not in visited and
                    not any(obstacle.rect.collidepoint(neighbor) for obstacle in obstacles) and
                    not any(spike.rect.collidepoint(neighbor) for spike in spikes)):
                queue.append(neighbor)
                visited.add(neighbor)
                parent[neighbor] = current

    # Проверка достижимости цели
    if goal not in parent:
        return []

    # Построение пути от цели к старту
    path = []
    step = goal
    while step is not None:
        path.append(step)
        step = parent[step]
    path.reverse()
    return path


def start_screen():
    input_boxes = [
        {"label": "Кол-во препятствий:", "text": "", "x": 50, "y": 50, "w": 200, "h": 50, "active": False},
        {"label": "Кол-во шипов:", "text": "", "x": 50, "y": 150, "w": 200, "h": 50, "active": False},
        {"label": "Кол-во монеток:", "text": "", "x": 50, "y": 250, "w": 200, "h": 50, "active": False},
    ]
    start_button = pygame.Rect(WIDTH // 2 - 50, HEIGHT - 100, 100, 50)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None

            if event.type == pygame.MOUSEBUTTONDOWN:
                for box in input_boxes:
                    if box['x'] <= event.pos[0] <= box['x'] + box['w'] and box['y'] <= event.pos[1] <= box['y'] + box[
                        'h']:
                        box['active'] = True
                    else:
                        box['active'] = False

                if start_button.collidepoint(event.pos):
                    return [int(box['text']) for box in input_boxes]

            if event.type == pygame.KEYDOWN:
                for box in input_boxes:
                    if box['active']:
                        if event.key == pygame.K_BACKSPACE:
                            box['text'] = box['text'][:-1]
                        else:
                            box['text'] += event.unicode

        win.fill(WHITE)
        for box in input_boxes:
            draw_text(box['label'], font, BLACK, win, box['x'], box['y'] - 50)
            draw_input_box(win, box['text'], box['x'], box['y'], box['w'], box['h'], box['active'])

        pygame.draw.rect(win, pygame.Color('dodgerblue'), start_button)
        draw_text("->", font, WHITE, win, start_button.x + 15, start_button.y + 10)

        pygame.display.flip()
        clock.tick(30)


all_sprites = pygame.sprite.Group()
coins = pygame.sprite.Group()
obstacles = pygame.sprite.Group()
spikes = pygame.sprite.Group()


# Глобальная переменная для хранения пути
path = []
path_lock = threading.Lock()


# Функция для выполнения поиска пути в отдельном потоке
def find_path(player_pos, coin_pos, obstacles):
    global path
    new_path = bfs_path(player_pos, coin_pos, obstacles)
    with path_lock:
        path = new_path


# Функция для проверки пересечения объектов с учетом минимального расстояния
def check_collision_with_distance(rect, group, min_distance=70):
    for sprite in group:
        if rect.colliderect(sprite.rect.inflate(min_distance * 2, min_distance * 2)):
            return True
    return False


def main_game(obstacles_count, spikes_count, coins_count):
    # Создание игрока
    player = Player()
    all_sprites.add(player)

    # Функция для создания объекта без пересечения и с минимальным расстоянием
    def create_non_colliding_object(group, width, height, margin=50, min_distance=70):
        attempts = 100  # Ограничение количества попыток для предотвращения бесконечного цикла
        while attempts > 0:
            x = random.randint(margin, WIDTH - margin)
            y = random.randint(margin, HEIGHT - margin)
            rect = pygame.Rect(x, y, width, height)
            if not check_collision_with_distance(rect, all_sprites, min_distance):
                return x, y
            attempts -= 1
        return None, None  # Возвращаем None, если не удалось найти место

    # Создание монеток
    for _ in range(coins_count):
        x, y = create_non_colliding_object(coins, 30, 30)
        if x is not None and y is not None:
            coin = Coin(x, y)
            all_sprites.add(coin)
            coins.add(coin)

    # Создание препятствий
    for _ in range(obstacles_count):
        x, y = create_non_colliding_object(obstacles, 50, 50)
        if x is not None and y is not None:
            obstacle = Obstacle(x, y)
            all_sprites.add(obstacle)
            obstacles.add(obstacle)

    # Создание шипов
    for _ in range(spikes_count):
        x, y = create_non_colliding_object(spikes, 30, 30)
        if x is not None and y is not None:
            spike = Spike(x, y)
            all_sprites.add(spike)
            spikes.add(spike)

    score = 0
    start_ticks = pygame.time.get_ticks()
    running = True

    coin_spawn_timer = pygame.time.get_ticks()
    message_timer = None
    message = ""

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        all_sprites.update(keys)

        collected_coins = pygame.sprite.spritecollide(player, coins, True)
        score += len(collected_coins)

        if pygame.sprite.spritecollide(player, spikes, False):
            draw_text("Вы проиграли!", font, RED, win, WIDTH // 2 - 100, HEIGHT // 2)
            pygame.display.flip()
            pygame.time.wait(5000)
            running = False

        seconds = (pygame.time.get_ticks() - start_ticks) // 1000
        if seconds > 120:
            draw_text("Время вышло!", font, RED, win, WIDTH // 2 - 100, HEIGHT // 2)
            pygame.display.flip()
            pygame.time.wait(5000)
            running = False

        if score >= 10:
            draw_text("Ты победил!", font, GOLD, win, WIDTH // 2 - 100, HEIGHT // 2)
            pygame.display.flip()
            pygame.time.wait(5000)
            running = False

        current_time = pygame.time.get_ticks()
        if current_time - coin_spawn_timer >= 5000:
            coin_spawn_timer = current_time
            if coins:
                oldest_coin = coins.sprites()[0]
                oldest_coin.kill()
            x, y = create_non_colliding_object(coins, 30, 30)
            if x is not None and y is not None:
                new_coin = Coin(x, y)
                all_sprites.add(new_coin)
                coins.add(new_coin)
                message = "Появилась новая монетка!"
                message_timer = current_time

        win.fill(WHITE)
        all_sprites.draw(win)
        draw_text(f"Счёт: {score}", font, BLACK, win, 10, 10)
        draw_text(f"Время: {120 - seconds}", font, BLACK, win, WIDTH - 200, 10)

        if message and current_time - message_timer <= 3000:
            draw_text(message, font, GREEN, win, WIDTH // 2 - 150, HEIGHT - 50)
        else:
            message = ""

        # Подсказка пути к ближайшей монетке
        if coins:
            player_pos = (player.rect.centerx, player.rect.centery)
            closest_coin = min(coins, key=lambda coin: abs(coin.rect.centerx - player.rect.centerx) + abs(
                coin.rect.centery - player.rect.centery))
            coin_pos = (closest_coin.rect.centerx, closest_coin.rect.centery)

            if threading.active_count() <= 1:  # Проверка, есть ли уже активный поток
                threading.Thread(target=find_path, args=(player_pos, coin_pos, obstacles)).start()

            with path_lock:
                for point in path:
                    pygame.draw.circle(win, RED, point, 5)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    parameters = start_screen()
    if parameters:
        main_game(*parameters)
