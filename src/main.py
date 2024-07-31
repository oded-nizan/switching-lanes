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
                  high_score INTEGER NOT NULL)''')

# table 2 - leaderboard
cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
    name TEXT NOT NULL,
    highest_score INTEGER NOT NULL)''')

con.commit()

# initialize pygame
pygame.init()

# display variables
WIDTH: int = 900
HEIGHT: int = 900 # To fit the macOS screen
WINDOW_NAME: str = "Switching Lanes"

# initialize display
screen: pygame.display = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(WINDOW_NAME)

# colors
WHITE: tuple = (255, 255, 255)
BLACK: tuple = (0, 0, 0)
RED: tuple = (255, 0, 0)

# resources path's
BG_PATH: str = "resources/background.jpg"
CHAR_PATH: str = "resources/player.png"
PROJECTILE_PATH: str = "resources/projectile.png"
OBSTACLE_PATH: str = "resources/obstacle.png"

# load images
player_img = pygame.image.load(CHAR_PATH).convert_alpha()
obstacle_img = pygame.image.load(OBSTACLE_PATH).convert_alpha()
projectile_img = pygame.image.load(PROJECTILE_PATH).convert_alpha()
background_img = pygame.image.load(BG_PATH).convert_alpha()

# game variables
clock: pygame.time.Clock = pygame.time.Clock()
FPS: int = 60

# player variables
PLAYER_WIDTH: int = 90
PLAYER_HEIGHT: int = 140
player_x: int = WIDTH // 2 - PLAYER_WIDTH // 2
player_y: int = HEIGHT - PLAYER_HEIGHT - 20
player_speed: float = 5
current_lane: float = 1  # 0: left, 1: center, 2: right

# obstacle variables
OBSTACLE_WIDTH: int = 120
OBSTACLE_HEIGHT: int = 80
obstacles = []
obstacle_speed: float = 3
obstacle_spawn_time: int = 2000  # in milliseconds
last_obstacle_spawn: int = pygame.time.get_ticks()
obstacle_min_health: int = 1
obstacle_max_health: int = 4

# projectile variables
PROJECTILE_WIDTH: int = 50
PROJECTILE_HEIGHT: int = 50
projectiles = []
projectile_speed: float = 12
projectile_damage: float = 1
projectile_cooldown: int = 750  # in milliseconds
last_projectile_time: int = 0

# difficulty increase variables
SPEED_INCREASE_RATE: float = 1
COOLDOWN_DECREASE_RATE: int = 50
HEALTH_INCREASE_RATE: float = 2
DAMAGE_INCREASE_RATE: float = 1

# wave mechanics
wave_number: int = 1
points_this_wave: int = 0
points_per_wave: int = 10
WAVE_NOTIFICATION_DURATION = 1500  # in milliseconds

# player inactivity variables
player_last_move_time: int = 0
player_inactive_cycles: int = 0
INACTIVITY_THRESHOLD: int = 3

# scale images if needed
player_img = pygame.transform.rotate(player_img, 90)
player_img = pygame.transform.scale(player_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
obstacle_img = pygame.transform.scale(obstacle_img, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT))
projectile_img = pygame.transform.scale(projectile_img, (PROJECTILE_WIDTH, PROJECTILE_HEIGHT))
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

# game state
score: int = 0
previous_score: int = 0
game_state: str = "playing"  # playing, game_over, input_name, leaderboard, player_data
player_name: str = ""

# font setup
font: pygame.font.Font = pygame.font.Font(None, 36)


# database functions
def chk_usr(name: str, player_score: int) -> None:
    cursor.execute('''SELECT * FROM players WHERE name = ?''', (name,))
    row = cursor.fetchone()

    if row:
        current_high_score: int = row[3]
        new_high_score: int = int(max(current_high_score, player_score))
        cursor.execute('''UPDATE players SET plays = plays+1, high_score = ? WHERE name = ?''', (new_high_score, name))
    else:
        cursor.execute('''INSERT INTO players (name, plays, high_score) VALUES (?, ?, ?)''', (name, 1, score))
    con.commit()
    return None


# drawing functions
def draw_player(x: int, y: int) -> None:
    screen.blit(player_img, (x, y))
    return None


def draw_obstacle(x: int, y: int, health: int) -> None:
    screen.blit(obstacle_img, (x, y))
    health_text: pygame.Surface = font.render(str(int(health)), True, WHITE)
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
    global obstacles
    lanes_spawned: [int] = []
    num_chances: int = int(max(3, wave_number))
    for _ in range(num_chances):
        chk: int = random.randint(0, (wave_number + 2) // 2)
        if chk == 0:
            lane: int = random.randint(0, 2)
            while lane in lanes_spawned:
                lane: int = random.randint(0, 2)
            lanes_spawned.append(lane)
            x = get_lane_x(lane)
            y = -OBSTACLE_HEIGHT
            health = random.uniform(obstacle_min_health, obstacle_max_health)
            obstacles.append({'x': x, 'y': y, 'health': health})
        if len(lanes_spawned) == 3:
            return None
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

    cursor.execute('''SELECT name, highest_score FROM leaderboard ORDER BY highest_score DESC LIMIT 10''')
    for idx, (name, high_score) in enumerate(cursor.fetchall(), 1):
        entry_text: pygame.Surface = font.render(f"{idx}. {name}: {high_score}", True, WHITE)
        screen.blit(entry_text, (WIDTH // 2 - entry_text.get_width() // 2, 100 + idx * 40))

    continue_text: pygame.Surface = font.render("Press ENTER to continue", True, WHITE)
    screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT - 100))

    return None


def show_wave_notification(wave: int) -> None:
    notification_text: pygame.Surface = font.render(f"Wave: {wave}", True, WHITE)
    screen.blit(notification_text, (WIDTH // 2 - notification_text.get_width() // 2, HEIGHT // 2))
    pygame.display.flip()
    pygame.time.wait(WAVE_NOTIFICATION_DURATION)
    return None


def show_player_data() -> None:
    global game_state

    # fetch all player's data, ordered by number of plays
    cursor.execute('''SELECT name, plays, high_score FROM players ORDER BY plays DESC''')
    player_data = cursor.fetchall()

    # variables for scrolling
    scroll_position: int = 0
    players_per_page: int = 10

    while game_state == "player_data":
        screen.fill(WHITE)

        # display title
        title_text: pygame.Surface = font.render("Player Data", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 20))

        # displaying player's data
        for i, (name, plays, high_score) in enumerate(player_data[scroll_position:scroll_position + players_per_page]):
            player_text: pygame.Surface = font.render(f"{i+scroll_position+1}. {name}: {plays} times played, High "
                                                      f"Score: {high_score}", True, WHITE)
            screen.blit(player_text, (50, 80 + i * 40))

        # display scroll instructions
        if len(player_data) > players_per_page:
            scroll_text: pygame.Surface = font.render("Use Up/Down arrows to scroll", True, WHITE)
            screen.blit(scroll_text, (WIDTH // 2 - scroll_text.get_width() // 2, HEIGHT - 60))

        # display continue instructions
        continue_text: pygame.Surface = font.render("Press ENTER to restart the game", True, WHITE)
        screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT - 30))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and scroll_position > 0:
                    scroll_position -= 1
                elif event.key == pygame.K_DOWN and scroll_position < len(player_data) - players_per_page:
                    scroll_position += 1
                elif event.key == pygame.K_RETURN:
                    game_state = "playing"
                    reset_game()
        clock.tick(FPS)
        return None


def reset_game() -> None:
    global player_x, current_lane, obstacles, projectiles, score, game_state, obstacle_speed, previous_score, \
        wave_number, points_this_wave, points_per_wave
    player_x = WIDTH // 2 - PLAYER_WIDTH // 2
    current_lane = 1
    obstacles = []
    projectiles = []
    score = 0
    previous_score = 0
    game_state = "playing"
    obstacle_speed = 3
    wave_number = 1
    points_this_wave = 0
    points_per_wave = 10
    return None


# main function
def main() -> None:
    global current_lane, player_x, score, last_obstacle_spawn, game_state, obstacle_spawn_time, obstacle_speed, \
        last_projectile_time, player_name, projectile_damage, projectile_cooldown, obstacle_min_health, \
        obstacle_max_health, player_speed, projectile_speed, previous_score, points_this_wave, wave_number, \
        points_per_wave, player_last_move_time, player_inactive_cycles
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
                    if event.key == pygame.K_RETURN:
                        game_state = "player_data"
                elif game_state == "player_data":
                    if event.key == pygame.K_RETURN:
                        reset_game()

        keys = pygame.key.get_pressed()
        if game_state == "playing":

            current_time: int = pygame.time.get_ticks()
            player_moved: bool = False

            # move player
            if keys[pygame.K_a] and current_lane > 0:
                current_lane = max(0, current_lane - 0.1)
                player_moved = True
            if keys[pygame.K_d] and current_lane < 2:
                current_lane = min(2, current_lane + 0.1)
                player_moved = True

            # check player activity
            if player_moved:
                player_last_move_time = current_time
                player_inactive_cycles = 0

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

                # adjust for player activity
                if not player_moved:
                    player_inactive_cycles += 1
                    if player_inactive_cycles >= INACTIVITY_THRESHOLD:
                        # randomly move the player to a different lane to prevent farming
                        new_lane: int = current_lane
                        while new_lane == current_lane:
                            new_lane = random.randint(0, 2)
                        current_lane = new_lane
                        player_inactive_cycles = 0

            # move and remove obstacles
            for obstacle in obstacles[:]:
                obstacle['y'] += obstacle_speed
                if obstacle['y'] > HEIGHT:
                    obstacles.remove(obstacle)
                    points_this_wave += 1
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
                        obstacle['health'] = int(obstacle['health'] - projectile_damage)
                        if obstacle['health'] <= 0:
                            obstacles.remove(obstacle)
                            points_this_wave += 2
                            score += 2
                        break

            # increase difficulty
            if points_this_wave >= points_per_wave:
                wave_number += 1
                points_this_wave = points_this_wave - points_per_wave
                points_per_wave += 2

                # Show wave notification
                show_wave_notification(wave_number)

                # Increase obstacle health
                obstacle_min_health += HEALTH_INCREASE_RATE
                obstacle_max_health += HEALTH_INCREASE_RATE

                # Ensure min and max health are integers
                obstacle_min_health = int(obstacle_min_health)
                obstacle_max_health = int(obstacle_max_health)

                # Cap the max and min health
                obstacle_max_health = min(obstacle_max_health, 50)
                obstacle_min_health = min(obstacle_min_health, obstacle_max_health - 2)

                # Increase projectile damage every 4 waves
                if wave_number % 4 == 0:
                    projectile_damage += DAMAGE_INCREASE_RATE
                    projectile_damage = min(projectile_damage, 25)

                    # increase obstacle speed often
                    obstacle_speed += SPEED_INCREASE_RATE - (wave_number // 10)

                    # Increase obstacle health
                    obstacle_min_health += HEALTH_INCREASE_RATE
                    obstacle_max_health += HEALTH_INCREASE_RATE

                    # Ensure min and max health are integers
                    obstacle_min_health = int(obstacle_min_health)
                    obstacle_max_health = int(obstacle_max_health)

                    # Cap the max and min health
                    obstacle_max_health = min(obstacle_max_health, 50)
                    obstacle_min_health = min(obstacle_min_health, obstacle_max_health - 2)

                # Adjust speed increases
                player_speed += SPEED_INCREASE_RATE - (wave_number / 10)
                obstacle_speed += SPEED_INCREASE_RATE - (wave_number // 10)

                # Decrease cooldowns
                obstacle_spawn_time = max(obstacle_spawn_time - (COOLDOWN_DECREASE_RATE*4), 250)
                projectile_cooldown = max(projectile_cooldown - COOLDOWN_DECREASE_RATE, 75)

                # Print difficulty stats for debugging
                print(f"Wave: {wave_number}, Player Speed: {player_speed:.2f}, Obstacle Speed: {obstacle_speed:.2f}")
                print(
                    f"Obstacle Health: {obstacle_min_health}-{obstacle_max_health}, Projectile Damage: "
                    f"{projectile_damage:.2f}")

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
        elif game_state == "player_data":
            show_player_data()

        pygame.display.flip()

    # quit the game
    con.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
