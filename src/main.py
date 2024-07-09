# imports
import pygame
import sys
import sqlite3
import random

# handle database initialization
# connect to a database or create one if it does not exist
con: sqlite3.Connection = sqlite3.connect("database.db")

# create a cursor object
cursor: sqlite3.Cursor = con.cursor()

# create tables
# table 1 - players
cursor.execute('''CREATE TABLE IF NOT EXISTS players (
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL,
                  plays INTEGER NOT NULL,
                  highest_score INTEGER NOT NULL)''')

# table 2 - leaderboard
cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
    name TEXT NOT NULL,
    highest_score INTEGER NOT NULL)''')

con.commit()

# initialize pygame
pygame.init()

# display variables
WIDTH: int = 800
HEIGHT: int = 800
WINDOW_NAME: str = "Switching Lanes"

# initialize display
screen: pygame.display = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(WINDOW_NAME)

# colors
WHITE: tuple = (255, 255, 255)
BLACK: tuple = (0, 0, 0)
RED: tuple = (255, 0, 0)

# resources path's
BG_PATH: str = r"C:\Users\Oded\PycharmProjects\switching_lanes\src\resources\tunnel_road.jpg"
CHAR_PATH: str = r"C:\Users\Oded\PycharmProjects\switching_lanes\src\resources\spr_bike_0.png"
PROJECTILE_PATH: str = r"C:\Users\Oded\PycharmProjects\switching_lanes\src\resources\blade_3.png"
OBSTACLE_PATH: str = r"C:\Users\Oded\PycharmProjects\switching_lanes\src\resources\swinging_spike_stick.png"

# load images
player_img = pygame.image.load(CHAR_PATH).convert_alpha()
obstacle_img = pygame.image.load(OBSTACLE_PATH).convert_alpha()
projectile_img = pygame.image.load(PROJECTILE_PATH).convert_alpha()
background_img = pygame.image.load(BG_PATH).convert_alpha()

# game variables
clock: pygame.time.Clock = pygame.time.Clock()
FPS: int = 60

# player variables
PLAYER_WIDTH: int = 50
PLAYER_HEIGHT: int = 100
player_x: int = WIDTH // 2 - PLAYER_WIDTH // 2
player_y: int = HEIGHT - PLAYER_HEIGHT - 20
player_speed: float = 5
current_lane: float = 1  # 0: left, 1: center, 2: right

# obstacle variables
OBSTACLE_WIDTH: int = 60
OBSTACLE_HEIGHT: int = 60
obstacles = []
obstacle_speed: float = 2
obstacle_spawn_time: int = 2500  # in milliseconds
last_obstacle_spawn: int = pygame.time.get_ticks()
obstacle_min_health: float = 1
obstacle_max_health: float = 3

# projectile variables
PROJECTILE_WIDTH: int = 50
PROJECTILE_HEIGHT: int = 50
projectiles = []
projectile_speed: float = 15
projectile_damage: float = 1
projectile_cooldown: int = 400  # in milliseconds
last_projectile_time: int = 0

# scale images if needed
player_img = pygame.transform.scale(player_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
obstacle_img = pygame.transform.scale(obstacle_img, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT))
projectile_img = pygame.transform.scale(projectile_img, (PROJECTILE_WIDTH, PROJECTILE_HEIGHT))
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

# game state
score: int = 0
game_state: str = "playing"  # playing, game_over, input_name, leaderboard
player_name: str = ""

# font setup
font: pygame.font.Font = pygame.font.Font(None, 36)


# database functions
def chk_usr(name: str, player_score: int) -> bool:
    found: bool = False
    current_highest_score: int = 0
    cursor.execute('''SELECT * FROM players''')
    rows = cursor.fetchall()
    for row in rows:
        if row[1] == name:
            current_highest_score = row[3]
            found = True

    if found:
        new_highest_score: int = max(player_score, current_highest_score)
        cursor.execute(
            f'''UPDATE players set plays = plays + 1 and highest_score = {new_highest_score} where name = {name}''')
    else:
        cursor.execute('''INSERT INTO players (name, plays, highest_score) VALUES (?, ?, ?)''', (name, 1, score))
    con.commit()
    return found


# drawing functions
def draw_player(x: int, y: int) -> None:
    screen.blit(player_img, (x, y))
    return None


def draw_obstacle(x: int, y: int, health: int) -> None:
    screen.blit(obstacle_img, (x, y))
    health_text: pygame.Surface = font.render(str(health), True, WHITE)
    screen.blit(health_text, (
        x + OBSTACLE_WIDTH // 2 - health_text.get_width() // 2,
        y + OBSTACLE_HEIGHT // 2 - health_text.get_height() // 2))
    return None


def draw_projectile(x: int, y: int) -> None:
    screen.blit(projectile_img, (x, y))
    return None


# more useful functions
def get_lane_x(lane: int) -> int:
    lane_width: int = WIDTH // 3
    return lane * lane_width + (lane_width - PLAYER_WIDTH) // 2


def spawn_obstacle() -> None:
    lane: int = random.randint(0, 2)
    x = get_lane_x(lane)
    y = -OBSTACLE_HEIGHT
    health = random.randint(obstacle_min_health, obstacle_max_health)
    obstacles.append({'x': x, 'y': y, 'health': health})
    return None


def show_game_over() -> None:
    game_over_text: pygame.Surface = font.render("GAME OVER", True, WHITE)
    score_text: pygame.Surface = font.render(f"Final Score: {score}", True, WHITE)
    continue_text: pygame.Surface = font.render("Press ENTER to continue", True, WHITE)
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + 50))
    screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT // 2 + 100))
    pygame.display.flip()
    return None


def show_name_input() -> None:
    global player_name
    input_text: pygame.Surface = font.render("Enter your name: ", True, WHITE)
    name_text: pygame.Surface = font.render(player_name, True, WHITE)
    screen.blit(input_text, (WIDTH // 2 - input_text.get_width() // 2, HEIGHT // 2 - 50))
    pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 100, HEIGHT // 2, 200, 40), 2)
    screen.blit(name_text, (WIDTH // 2 - 95, HEIGHT // 2 + 5))
    return None


def show_leaderboard() -> None:
    leaderboard_text: pygame.Surface = font.render("Leaderboard", True, WHITE)
    screen.blit(leaderboard_text, (WIDTH // 2 - leaderboard_text.get_width() // 2, 50))

    cursor.execute('''SELECT name, highest_score FROM leaderboard ORDER BY highest_score DESC LIMIT 5''')
    for idx, (name, high_score) in enumerate(cursor.fetchall(), 1):
        entry_text: pygame.Surface = font.render(f"{idx}. {name}: {high_score}", True, WHITE)
        screen.blit(entry_text, (WIDTH // 2 - entry_text.get_width() // 2, 100 + idx * 40))

    restart_text: pygame.Surface = font.render("Press R to restart", True, WHITE)
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT - 100))

    return None


def reset_game() -> None:
    global player_x, current_lane, obstacles, projectiles, score, game_state, obstacle_speed
    player_x = WIDTH // 2 - PLAYER_WIDTH // 2
    current_lane = 1
    obstacles = []
    projectiles = []
    score = 0
    game_state = "playing"
    obstacle_speed = 3
    return None


# main function
def main() -> None:
    global current_lane, player_x, score, last_obstacle_spawn, game_state, obstacle_spawn_time, obstacle_speed, \
        last_projectile_time, player_name, projectile_damage, projectile_cooldown, obstacle_min_health, \
        obstacle_max_health, player_speed, projectile_speed
    running: bool = True
    while running:
        clock.tick(FPS)
        screen.blit(background_img, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_state == "playing":
                    if event.key == pygame.K_SPACE:
                        current_time: int = pygame.time.get_ticks()
                        if current_time - last_projectile_time > projectile_cooldown:
                            projectiles.append(
                                {'x': player_x + PLAYER_WIDTH // 2 - PROJECTILE_WIDTH // 2, 'y': player_y})
                            last_projectile_time = current_time
                elif game_state == "game_over":
                    if event.key == pygame.K_RETURN:
                        game_state = "input_name"
                elif game_state == "input_name":
                    if event.key == pygame.K_RETURN:
                        # Save score to database
                        chk_usr(player_name, score)
                        cursor.execute('''INSERT INTO leaderboard (name, highest_score) VALUES (?, ?)''',
                                       (player_name, score))
                        con.commit()
                        game_state = "leaderboard"
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    else:
                        player_name += event.unicode
                elif game_state == "leaderboard":
                    if event.key == pygame.K_r:
                        reset_game()

        keys = pygame.key.get_pressed()
        if game_state == "playing":
            # move player
            if keys[pygame.K_a] and current_lane > 0:
                current_lane = max(0, current_lane - 0.1)
            if keys[pygame.K_d] and current_lane < 2:
                current_lane = min(2, current_lane + 0.1)

            target_x: int = get_lane_x(int(current_lane))
            if player_x < target_x:
                player_x = min(player_x + player_speed, target_x)
            elif player_x > target_x:
                player_x = max(player_x - player_speed, target_x)

            # spawn obstacles
            current_time: int = pygame.time.get_ticks()
            if current_time - last_obstacle_spawn > obstacle_spawn_time:
                spawn_obstacle()
                last_obstacle_spawn = current_time

            # move and remove obstacles
            for obstacle in obstacles[:]:
                obstacle['y'] += obstacle_speed
                if obstacle['y'] > HEIGHT:
                    obstacles.remove(obstacle)
                    score += 1

                # check collision with player
                if (player_x < obstacle['x'] + OBSTACLE_WIDTH and
                        player_x + PLAYER_WIDTH > obstacle["x"] and
                        player_y < obstacle['y'] + OBSTACLE_HEIGHT and
                        player_y + PLAYER_HEIGHT > obstacle["y"]):
                    game_state = "game_over"

            # move and remove projectiles
            for projectile in projectiles[:]:
                projectile['y'] -= projectile_speed
                if projectile['y'] + PROJECTILE_HEIGHT < 0:
                    projectiles.remove(projectile)

            # check projectile collisions
            for projectile in projectiles[:]:
                for obstacle in obstacles[:]:
                    if (projectile['x'] < obstacle['x'] + OBSTACLE_WIDTH and
                            projectile['x'] + PROJECTILE_WIDTH > obstacle['x'] and
                            projectile['y'] < obstacle['y'] + OBSTACLE_HEIGHT and
                            projectile['y'] + PROJECTILE_HEIGHT > obstacle['y']):
                        projectiles.remove(projectile)
                        obstacle['health'] -= projectile_damage
                        if obstacle['health'] <= 0:
                            obstacles.remove(obstacle)
                            score += 1
                        break

            # increase difficulty
            if score % 10 == 0 and score > 0:
                player_speed += 0.02
                obstacle_speed += 0.01
                obstacle_spawn_time = max(500, obstacle_spawn_time - 20)
                if obstacle_min_health < 10:
                    obstacle_min_health += 0.1
                if obstacle_max_health < 15:
                    obstacle_max_health += 0.1
                if projectile_damage < 10:
                    projectile_damage += 0.1
                projectile_cooldown = max(50, projectile_cooldown - 25)

            # draw game objects
            draw_player(player_x, player_y)
            for obstacle in obstacles:
                draw_obstacle(obstacle['x'], obstacle['y'], obstacle['health'])
            for projectile in projectiles:
                draw_projectile(projectile['x'], projectile['y'])

            # draw score
            score_text: pygame.Surface = font.render(f"Score: {score}", True, BLACK)
            screen.blit(score_text, (10, 10))

        elif game_state == "game_over":
            show_game_over()
        elif game_state == "input_name":
            show_name_input()
        elif game_state == "leaderboard":
            show_leaderboard()

        pygame.display.flip()

    # quit the game
    con.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
