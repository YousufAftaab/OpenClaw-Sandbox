import pygame
import sys
import math
import random
import array

# =====================================================================
# CONSTANTS & CONFIGURATION
# =====================================================================
SCREEN_WIDTH = 560
SCREEN_HEIGHT = 660
TILE_SIZE = 20
FPS = 60

# Palette
COLOR_BLACK = (0, 0, 0)
COLOR_WALL = (33, 33, 222)
COLOR_WALL_INNER = (0, 0, 0)
COLOR_GATE = (255, 184, 255)
COLOR_PELLET = (255, 183, 174)
COLOR_ENERGIZER = (255, 255, 255)
COLOR_PACMAN = (255, 255, 0)
COLOR_FRIGHTENED = (36, 36, 255)
COLOR_FLASH = (255, 255, 255)
COLOR_EYES = (255, 255, 255)
COLOR_PUPIL = (0, 0, 255)
COLOR_TEXT = (255, 255, 255)
COLOR_SCORE = (255, 255, 255)

# Ghost Personalities
GHOST_COLORS = {
    "blinky": (255, 0, 0),      # Shadow / Red
    "pinky": (255, 184, 255),   # Speedy / Pink
    "inky": (0, 255, 255),      # Bashful / Cyan
    "clyde": (255, 184, 82)     # Pokey / Orange
}

# Directions: (dx, dy)
DIR_NONE = (0, 0)
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)

# 28 columns x 31 rows (Standard Arcade Maze Layout)
# W = Wall, . = Pellet, o = Energizer, G = Gate, E = Empty, H = Ghost House
MAZE_MAP = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WoWWWW.WWWWW.WW.WWWWW.WWWWoW",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W..........................W",
    "W.WWWW.WW.WWWWWWWW.WW.WWWW.W",
    "W.WWWW.WW.WWWWWWWW.WW.WWWW.W",
    "W......WW....WW....WW......W",
    "WWWWWW.WWWWW.WW.WWWWW.WWWWWW",
    "EEEEWW.WWWWW.WW.WWWWW.WWEEEE",
    "EEEEWW.WW..........WW.WWEEEE",
    "EEEEWW.WW.WWGGWWWW.WW.WWEEEE",
    "WWWWWW.WW.WHHHHHEW.WW.WWWWWW",
    "T.....E...WHHHHHHW...E.....T",
    "WWWWWW.WW.WHHHHHHW.WW.WWWWWW",
    "EEEEWW.WW.WWWWWWWW.WW.WWEEEE",
    "EEEEWW.WW..........WW.WWEEEE",
    "EEEEWW.WW.WWWWWWWW.WW.WWEEEE",
    "WWWWWW.WW.WWWWWWWW.WW.WWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "Wo..WW................WW..oW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "W......WW....WW....WW......W",
    "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
    "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
    "W..........................W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW"
]

# =====================================================================
# SYNTHETIC AUDIO SYSTEM (No external sound files required)
# =====================================================================
class SoundEffects:
    def __init__(self):
        self.enabled = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sample_rate = 22050
            self.enabled = True
            self.waka_sound = self.generate_tone(440, 550, 0.08)
            self.energizer_sound = self.generate_tone(220, 880, 0.3)
            self.eat_ghost_sound = self.generate_tone(800, 200, 0.25)
            self.death_sound = self.generate_tone(600, 100, 0.6)
            self.fruit_sound = self.generate_tone(523, 784, 0.2)
        except Exception:
            self.enabled = False

    def generate_tone(self, freq_start, freq_end, duration):
        if not self.enabled:
            return None
        n_samples = int(self.sample_rate * duration)
        buf = array.array('h')
        for i in range(n_samples):
            t = i / float(self.sample_rate)
            progress = i / float(n_samples)
            freq = freq_start + (freq_end - freq_start) * progress
            val = int(32767.0 * 0.3 * math.sin(2.0 * math.pi * freq * t))
            buf.append(val)
            buf.append(val)
        return pygame.mixer.Sound(buffer=buf)

    def play(self, sound):
        if self.enabled and sound:
            try:
                sound.play()
            except Exception:
                pass

# =====================================================================
# MAZE CLASS
# =====================================================================
class Maze:
    def __init__(self):
        self.rows = len(MAZE_MAP)
        self.cols = len(MAZE_MAP[0])
        self.grid = []
        self.total_pellets = 0
        self.reset()

    def reset(self):
        self.grid = [list(row) for row in MAZE_MAP]
        self.total_pellets = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] in ['.', 'o']:
                    self.total_pellets += 1

    def is_wall(self, col, row, is_ghost=False):
        if row < 0 or row >= self.rows:
            return False
        if col < 0 or col >= self.cols:
            return False
        tile = self.grid[row][col]
        if tile == 'W':
            return True
        if tile == 'G' and not is_ghost:
            return True
        return False

    def draw(self, surface, offset_y=40, flash=False):
        wall_color = COLOR_FLASH if flash else COLOR_WALL
        for r in range(self.rows):
            for c in range(self.cols):
                x = c * TILE_SIZE
                y = r * TILE_SIZE + offset_y
                tile = self.grid[r][c]

                if tile == 'W':
                    pygame.draw.rect(surface, wall_color, (x, y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(surface, COLOR_WALL_INNER, (x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6))
                elif tile == 'G':
                    pygame.draw.line(surface, COLOR_GATE, (x, y + TILE_SIZE // 2), (x + TILE_SIZE, y + TILE_SIZE // 2), 3)
                elif tile == '.':
                    pygame.draw.circle(surface, COLOR_PELLET, (x + TILE_SIZE // 2, y + TILE_SIZE // 2), 2)
                elif tile == 'o':
                    # Pulsing energizer
                    pulse = abs(math.sin(pygame.time.get_ticks() * 0.006))
                    radius = int(5 + pulse * 2)
                    pygame.draw.circle(surface, COLOR_ENERGIZER, (x + TILE_SIZE // 2, y + TILE_SIZE // 2), radius)

# =====================================================================
# PAC-MAN CLASS
# =====================================================================
class Pacman:
    def __init__(self, maze):
        self.maze = maze
        self.spawn_x = 13.5 * TILE_SIZE
        self.spawn_y = 23 * TILE_SIZE
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.speed = 2.2
        self.direction = DIR_NONE
        self.next_direction = DIR_NONE
        self.mouth_angle = 45
        self.mouth_change = 4
        self.lives = 3
        self.alive = True
        self.death_timer = 0

    def reset_position(self):
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.direction = DIR_NONE
        self.next_direction = DIR_NONE
        self.alive = True
        self.death_timer = 0

    def set_next_direction(self, direct):
        self.next_direction = direct

    def can_move(self, direct):
        if direct == DIR_NONE:
            return True
        dx, dy = direct
        test_x = self.x + dx * self.speed
        test_y = self.y + dy * self.speed

        # Check all 4 bounding box points
        margin = 1
        corners = [
            (test_x + margin, test_y + margin),
            (test_x + TILE_SIZE - 1 - margin, test_y + margin),
            (test_x + margin, test_y + TILE_SIZE - 1 - margin),
            (test_x + TILE_SIZE - 1 - margin, test_y + TILE_SIZE - 1 - margin)
        ]
        for px, py in corners:
            c = int(px // TILE_SIZE)
            r = int(py // TILE_SIZE)
            if self.maze.is_wall(c, r):
                return False
        return True

    def update(self, sfx):
        if not self.alive:
            self.death_timer += 1
            return

        # Attempt turn
        if self.next_direction != self.direction:
            # Check if aligned to grid enough to turn
            aligned_x = (int(self.x) % TILE_SIZE == 0)
            aligned_y = (int(self.y) % TILE_SIZE == 0)
            if self.direction == DIR_NONE or (self.next_direction[0] == -self.direction[0] and self.next_direction[1] == -self.direction[1]):
                self.direction = self.next_direction
            elif self.can_move(self.next_direction):
                self.direction = self.next_direction

        # Move
        if self.can_move(self.direction):
            self.x += self.direction[0] * self.speed
            self.y += self.direction[1] * self.speed

            # Mouth animation
            self.mouth_angle += self.mouth_change
            if self.mouth_angle >= 50 or self.mouth_angle <= 0:
                self.mouth_change *= -1

        # Screen wrap tunnel
        if self.x < -TILE_SIZE // 2:
            self.x = SCREEN_WIDTH - TILE_SIZE // 2
        elif self.x > SCREEN_WIDTH - TILE_SIZE // 2:
            self.x = -TILE_SIZE // 2

    def draw(self, surface, offset_y=40):
        center_x = int(self.x + TILE_SIZE // 2)
        center_y = int(self.y + TILE_SIZE // 2 + offset_y)
        radius = TILE_SIZE // 2

        if not self.alive:
            # Dying animation (shrink mouth open to circle disappearance)
            progress = min(1.0, self.death_timer / 50.0)
            if progress < 1.0:
                angle = int(45 + progress * 135)
                rect = (center_x - radius, center_y - radius, radius * 2, radius * 2)
                pygame.draw.arc(surface, COLOR_PACMAN, rect, math.radians(angle), math.radians(360 - angle), radius)
            return

        # Normal drawing with rotation based on direction
        rot = 0
        if self.direction == DIR_RIGHT:
            rot = 0
        elif self.direction == DIR_DOWN:
            rot = 270
        elif self.direction == DIR_LEFT:
            rot = 180
        elif self.direction == DIR_UP:
            rot = 90

        start_angle = math.radians(rot + self.mouth_angle)
        end_angle = math.radians(rot + 360 - self.mouth_angle)

        points = [(center_x, center_y)]
        steps = 20
        for i in range(steps + 1):
            theta = start_angle + (end_angle - start_angle) * (i / steps)
            px = center_x + radius * math.cos(theta)
            py = center_y - radius * math.sin(theta)
            points.append((px, py))

        if len(points) > 2:
            pygame.draw.polygon(surface, COLOR_PACMAN, points)

# =====================================================================
# GHOST CLASS
# =====================================================================
class Ghost:
    MODE_CHASE = 0
    MODE_SCATTER = 1
    MODE_FRIGHTENED = 2
    MODE_EATEN = 3

    def __init__(self, name, maze):
        self.name = name
        self.maze = maze
        self.color = GHOST_COLORS[name]
        self.speed = 1.8
        self.spawn_positions = {
            "blinky": (13.5 * TILE_SIZE, 11 * TILE_SIZE),
            "pinky": (13.5 * TILE_SIZE, 14 * TILE_SIZE),
            "inky": (11.5 * TILE_SIZE, 14 * TILE_SIZE),
            "clyde": (15.5 * TILE_SIZE, 14 * TILE_SIZE)
        }
        self.scatter_targets = {
            "blinky": (25, 0),
            "pinky": (2, 0),
            "inky": (27, 30),
            "clyde": (0, 30)
        }
        self.direction = DIR_UP
        self.mode = Ghost.MODE_SCATTER
        self.frightened_timer = 0
        self.reset_position()

    def reset_position(self):
        sx, sy = self.spawn_positions[self.name]
        self.x = sx
        self.y = sy
        self.mode = Ghost.MODE_SCATTER
        self.direction = DIR_UP if self.name == "blinky" else DIR_UP
        self.frightened_timer = 0

    def get_target_tile(self, pacman, blinky_pos):
        pac_col = int((pacman.x + TILE_SIZE // 2) // TILE_SIZE)
        pac_row = int((pacman.y + TILE_SIZE // 2) // TILE_SIZE)

        if self.mode == Ghost.MODE_SCATTER:
            return self.scatter_targets[self.name]

        if self.mode == Ghost.MODE_EATEN:
            return (13, 11)

        # Chase personalities
        if self.name == "blinky":
            # Aggressive direct chase
            return (pac_col, pac_row)
        elif self.name == "pinky":
            # Ambush 4 tiles ahead
            dx, dy = pacman.direction
            return (pac_col + dx * 4, pac_row + dy * 4)
        elif self.name == "inky":
            # Complex flank with Blinky vector
            dx, dy = pacman.direction
            pivot_c = pac_col + dx * 2
            pivot_r = pac_row + dy * 2
            b_c, b_r = blinky_pos
            return (pivot_c + (pivot_c - b_c), pivot_r + (pivot_r - b_r))
        elif self.name == "clyde":
            # Shy: Chases if far (>8 tiles), retreats to scatter corner if close
            my_c = int((self.x + TILE_SIZE // 2) // TILE_SIZE)
            my_r = int((self.y + TILE_SIZE // 2) // TILE_SIZE)
            dist = math.hypot(my_c - pac_col, my_r - pac_row)
            if dist > 8:
                return (pac_col, pac_row)
            else:
                return self.scatter_targets["clyde"]

        return (pac_col, pac_row)

    def get_valid_directions(self):
        valid = []
        c = int((self.x + TILE_SIZE // 2) // TILE_SIZE)
        r = int((self.y + TILE_SIZE // 2) // TILE_SIZE)

        for d in [DIR_UP, DIR_LEFT, DIR_DOWN, DIR_RIGHT]:
            # Ghost cannot reverse immediately unless forced
            if d[0] == -self.direction[0] and d[1] == -self.direction[1]:
                continue
            nc, nr = c + d[0], r + d[1]
            if not self.maze.is_wall(nc, nr, is_ghost=(self.mode == Ghost.MODE_EATEN)):
                valid.append(d)
        return valid

    def update(self, pacman, blinky_pos):
        if self.mode == Ghost.MODE_FRIGHTENED:
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.mode = Ghost.MODE_CHASE

        # Adjust speed based on state
        current_speed = self.speed
        if self.mode == Ghost.MODE_FRIGHTENED:
            current_speed = self.speed * 0.55
        elif self.mode == Ghost.MODE_EATEN:
            current_speed = self.speed * 2.0

        # Movement step & decision at tile intersections
        c = (self.x + TILE_SIZE // 2) / TILE_SIZE
        r = (self.y + TILE_SIZE // 2) / TILE_SIZE
        center_align_x = abs((self.x % TILE_SIZE) - 0) < current_speed
        center_align_y = abs((self.y % TILE_SIZE) - 0) < current_speed

        if center_align_x and center_align_y:
            # Snap to grid to prevent drift
            self.x = round(self.x / TILE_SIZE) * TILE_SIZE
            self.y = round(self.y / TILE_SIZE) * TILE_SIZE

            if self.mode == Ghost.MODE_EATEN and int(self.x // TILE_SIZE) == 13 and int(self.y // TILE_SIZE) == 11:
                self.mode = Ghost.MODE_CHASE

            valid_dirs = self.get_valid_directions()
            if valid_dirs:
                if self.mode == Ghost.MODE_FRIGHTENED:
                    self.direction = random.choice(valid_dirs)
                else:
                    target_c, target_r = self.get_target_tile(pacman, blinky_pos)
                    best_dir = valid_dirs[0]
                    best_dist = float('inf')
                    cur_c = int(self.x // TILE_SIZE)
                    cur_r = int(self.y // TILE_SIZE)
                    for d in valid_dirs:
                        nc, nr = cur_c + d[0], cur_r + d[1]
                        dist = (nc - target_c) ** 2 + (nr - target_r) ** 2
                        if dist < best_dist:
                            best_dist = dist
                            best_dir = d
                    self.direction = best_dir

        self.x += self.direction[0] * current_speed
        self.y += self.direction[1] * current_speed

        # Tunnel wrap
        if self.x < -TILE_SIZE // 2:
            self.x = SCREEN_WIDTH - TILE_SIZE // 2
        elif self.x > SCREEN_WIDTH - TILE_SIZE // 2:
            self.x = -TILE_SIZE // 2

    def draw(self, surface, offset_y=40):
        x = int(self.x)
        y = int(self.y + offset_y)
        w = TILE_SIZE
        h = TILE_SIZE

        if self.mode == Ghost.MODE_FRIGHTENED:
            # Flashing white near end of frightened duration
            if self.frightened_timer < 90 and (self.frightened_timer // 10) % 2 == 0:
                body_color = COLOR_FLASH
            else:
                body_color = COLOR_FRIGHTENED
        elif self.mode == Ghost.MODE_EATEN:
            body_color = None
        else:
            body_color = self.color

        if body_color is not None:
            # Ghost Dome
            pygame.draw.circle(surface, body_color, (x + w // 2, y + h // 2 - 2), w // 2)
            # Ghost Skirt
            pygame.draw.rect(surface, body_color, (x, y + h // 2 - 2, w, h // 2 + 2))
            # Wavy tentacles at bottom
            tentacle_w = w // 3
            for i in range(3):
                tx = x + i * tentacle_w
                pygame.draw.polygon(surface, body_color, [
                    (tx, y + h),
                    (tx + tentacle_w // 2, y + h - 4),
                    (tx + tentacle_w, y + h)
                ])

        # Eyes & Pupils
        eye_offset_x = self.direction[0] * 3
        eye_offset_y = self.direction[1] * 3
        left_eye_pos = (x + 5, y + 4)
        right_eye_pos = (x + 11, y + 4)

        for ex, ey in [left_eye_pos, right_eye_pos]:
            pygame.draw.ellipse(surface, COLOR_EYES, (ex, ey, 5, 7))
            pygame.draw.circle(surface, COLOR_PUPIL, (ex + 2 + eye_offset_x, ey + 3 + eye_offset_y), 2)

# =====================================================================
# BONUS FRUIT CLASS
# =====================================================================
class Fruit:
    def __init__(self):
        self.x = 13.5 * TILE_SIZE
        self.y = 17 * TILE_SIZE
        self.active = False
        self.timer = 0
        self.points = 100

    def spawn(self, level):
        self.active = True
        self.timer = 600  # 10 seconds active
        self.points = min(5000, 100 * (level * 2))

    def update(self):
        if self.active:
            self.timer -= 1
            if self.timer <= 0:
                self.active = False

    def draw(self, surface, offset_y=40):
        if self.active:
            x = int(self.x)
            y = int(self.y + offset_y)
            # Cherry icon
            pygame.draw.circle(surface, (255, 0, 0), (x + 6, y + 12), 4)
            pygame.draw.circle(surface, (255, 0, 0), (x + 14, y + 12), 4)
            pygame.draw.line(surface, (139, 69, 19), (x + 6, y + 8), (x + 10, y + 3), 2)
            pygame.draw.line(surface, (139, 69, 19), (x + 14, y + 8), (x + 10, y + 3), 2)

# =====================================================================
# MAIN GAME ENGINE
# =====================================================================
class PacmanGame:
    STATE_READY = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    STATE_PACMAN_DYING = 3
    STATE_LEVEL_CLEAR = 4
    STATE_GAME_OVER = 5

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pac-Man Arcade Classic")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier", 18, bold=True)
        self.large_font = pygame.font.SysFont("Courier", 26, bold=True)

        self.sfx = SoundEffects()
        self.maze = Maze()
        self.pacman = Pacman(self.maze)
        self.ghosts = [
            Ghost("blinky", self.maze),
            Ghost("pinky", self.maze),
            Ghost("inky", self.maze),
            Ghost("clyde", self.maze)
        ]
        self.fruit = Fruit()

        self.score = 0
        self.high_score = 10000
        self.level = 1
        self.pellets_eaten = 0
        self.ghost_combo = 0
        self.state = PacmanGame.STATE_READY
        self.state_timer = 120
        self.scatter_timer = 0
        self.scatter_phase = 0

    def switch_ghost_modes(self):
        # Timed Scatter / Chase cycle
        self.scatter_timer += 1
        # Classic timing: Scatter 7s, Chase 20s, Scatter 7s, Chase 20s...
        if self.scatter_phase % 2 == 0 and self.scatter_timer > 7 * FPS:
            for g in self.ghosts:
                if g.mode != Ghost.MODE_FRIGHTENED and g.mode != Ghost.MODE_EATEN:
                    g.mode = Ghost.MODE_CHASE
            self.scatter_phase += 1
            self.scatter_timer = 0
        elif self.scatter_phase % 2 != 0 and self.scatter_timer > 20 * FPS:
            for g in self.ghosts:
                if g.mode != Ghost.MODE_FRIGHTENED and g.mode != Ghost.MODE_EATEN:
                    g.mode = Ghost.MODE_SCATTER
            self.scatter_phase += 1
            self.scatter_timer = 0

    def trigger_energizer(self):
        self.ghost_combo = 0
        self.sfx.play(self.sfx.energizer_sound)
        for g in self.ghosts:
            if g.mode != Ghost.MODE_EATEN:
                g.mode = Ghost.MODE_FRIGHTENED
                g.frightened_timer = 360  # ~6 seconds

    def check_pellet_collision(self):
        pac_c = int((self.pacman.x + TILE_SIZE // 2) // TILE_SIZE)
        pac_r = int((self.pacman.y + TILE_SIZE // 2) // TILE_SIZE)

        if 0 <= pac_r < self.maze.rows and 0 <= pac_c < self.maze.cols:
            tile = self.maze.grid[pac_r][pac_c]
            if tile == '.':
                self.maze.grid[pac_r][pac_c] = 'E'
                self.score += 10
                self.pellets_eaten += 1
                self.sfx.play(self.waka_sound())
                if self.pellets_eaten in [70, 170]:
                    self.fruit.spawn(self.level)
            elif tile == 'o':
                self.maze.grid[pac_r][pac_c] = 'E'
                self.score += 50
                self.pellets_eaten += 1
                self.trigger_energizer()

        # Check Level Clear
        if self.pellets_eaten >= self.maze.total_pellets:
            self.state = PacmanGame.STATE_LEVEL_CLEAR
            self.state_timer = 180

    def waka_sound(self):
        return self.sfx.waka_sound

    def check_fruit_collision(self):
        if self.fruit.active:
            dist = math.hypot(self.pacman.x - self.fruit.x, self.pacman.y - self.fruit.y)
            if dist < TILE_SIZE:
                self.score += self.fruit.points
                self.fruit.active = False
                self.sfx.play(self.sfx.fruit_sound)

    def check_ghost_collisions(self):
        pac_center_x = self.pacman.x + TILE_SIZE // 2
        pac_center_y = self.pacman.y + TILE_SIZE // 2

        for g in self.ghosts:
            g_center_x = g.x + TILE_SIZE // 2
            g_center_y = g.y + TILE_SIZE // 2
            dist = math.hypot(pac_center_x - g_center_x, pac_center_y - g_center_y)

            if dist < TILE_SIZE * 0.75:
                if g.mode == Ghost.MODE_FRIGHTENED:
                    g.mode = Ghost.MODE_EATEN
                    self.ghost_combo += 1
                    g_points = 200 * (2 ** (self.ghost_combo - 1))
                    self.score += g_points
                    self.sfx.play(self.sfx.eat_ghost_sound)
                elif g.mode == Ghost.MODE_CHASE or g.mode == Ghost.MODE_SCATTER:
                    # Pac-Man dies
                    self.pacman.alive = False
                    self.state = PacmanGame.STATE_PACMAN_DYING
                    self.state_timer = 90
                    self.sfx.play(self.sfx.death_sound)
                    break

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_w]:
                    self.pacman.set_next_direction(DIR_UP)
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    self.pacman.set_next_direction(DIR_DOWN)
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    self.pacman.set_next_direction(DIR_LEFT)
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    self.pacman.set_next_direction(DIR_RIGHT)
                elif event.key == pygame.K_p and self.state == PacmanGame.STATE_PLAYING:
                    self.state = PacmanGame.STATE_PAUSED
                elif event.key == pygame.K_p and self.state == PacmanGame.STATE_PAUSED:
                    self.state = PacmanGame.STATE_PLAYING
                elif event.key == pygame.K_RETURN and self.state == PacmanGame.STATE_GAME_OVER:
                    self.restart_game()

    def restart_game(self):
        self.score = 0
        self.level = 1
        self.pacman.lives = 3
        self.pellets_eaten = 0
        self.maze.reset()
        self.pacman.reset_position()
        for g in self.ghosts:
            g.reset_position()
        self.state = PacmanGame.STATE_READY
        self.state_timer = 120

    def next_level(self):
        self.level += 1
        self.pellets_eaten = 0
        self.maze.reset()
        self.pacman.reset_position()
        for g in self.ghosts:
            g.reset_position()
            g.speed = min(3.0, 1.8 + (self.level - 1) * 0.15)
        self.state = PacmanGame.STATE_READY
        self.state_timer = 120

    def draw_hud(self):
        # Top Score Bar
        score_surface = self.font.render(f"1UP: {self.score}", True, COLOR_SCORE)
        high_score_surface = self.font.render(f"HIGH: {max(self.score, self.high_score)}", True, COLOR_SCORE)
        self.screen.blit(score_surface, (30, 10))
        self.screen.blit(high_score_surface, (SCREEN_WIDTH - 200, 10))

        # Bottom Lives & Level Bar
        for i in range(self.pacman.lives - 1):
            lx = 30 + i * 24
            ly = SCREEN_HEIGHT - 25
            pygame.draw.circle(self.screen, COLOR_PACMAN, (lx, ly), 8)
            # Wedge
            pygame.draw.polygon(self.screen, COLOR_BLACK, [(lx, ly), (lx + 9, ly - 4), (lx + 9, ly + 4)])

        level_surf = self.font.render(f"LVL {self.level}", True, COLOR_TEXT)
        self.screen.blit(level_surf, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 32))

    def run(self):
        while True:
            self.handle_input()

            # State Logic
            if self.state == PacmanGame.STATE_READY:
                self.state_timer -= 1
                if self.state_timer <= 0:
                    self.state = PacmanGame.STATE_PLAYING

            elif self.state == PacmanGame.STATE_PLAYING:
                self.switch_ghost_modes()
                self.pacman.update(self.sfx)

                blinky = self.ghosts[0]
                blinky_pos = (int(blinky.x // TILE_SIZE), int(blinky.y // TILE_SIZE))
                for g in self.ghosts:
                    g.update(self.pacman, blinky_pos)

                self.fruit.update()
                self.check_pellet_collision()
                self.check_fruit_collision()
                self.check_ghost_collisions()

            elif self.state == PacmanGame.STATE_PACMAN_DYING:
                self.pacman.update(self.sfx)
                self.state_timer -= 1
                if self.state_timer <= 0:
                    self.pacman.lives -= 1
                    if self.pacman.lives <= 0:
                        self.state = PacmanGame.STATE_GAME_OVER
                    else:
                        self.pacman.reset_position()
                        for g in self.ghosts:
                            g.reset_position()
                        self.state = PacmanGame.STATE_READY
                        self.state_timer = 90

            elif self.state == PacmanGame.STATE_LEVEL_CLEAR:
                self.state_timer -= 1
                if self.state_timer <= 0:
                    self.next_level()

            # Rendering
            self.screen.fill(COLOR_BLACK)
            flash = (self.state == PacmanGame.STATE_LEVEL_CLEAR and (self.state_timer // 15) % 2 == 0)
            self.maze.draw(self.screen, offset_y=40, flash=flash)
            self.fruit.draw(self.screen, offset_y=40)
            self.pacman.draw(self.screen, offset_y=40)

            if self.state != PacmanGame.STATE_PACMAN_DYING:
                for g in self.ghosts:
                    g.draw(self.screen, offset_y=40)

            self.draw_hud()

            # Overlay Texts
            if self.state == PacmanGame.STATE_READY:
                ready_text = self.large_font.render("READY!", True, (255, 255, 0))
                self.screen.blit(ready_text, (SCREEN_WIDTH // 2 - 45, 335))

            elif self.state == PacmanGame.STATE_PAUSED:
                pause_text = self.large_font.render("PAUSED", True, (0, 255, 255))
                self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - 45, 335))

            elif self.state == PacmanGame.STATE_GAME_OVER:
                go_text = self.large_font.render("GAME OVER", True, (255, 0, 0))
                retry_text = self.font.render("Press ENTER to Play Again", True, COLOR_TEXT)
                self.screen.blit(go_text, (SCREEN_WIDTH // 2 - 70, 315))
                self.screen.blit(retry_text, (SCREEN_WIDTH // 2 - 130, 355))

            pygame.display.flip()
            self.clock.tick(FPS)

# =====================================================================
# ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    game = PacmanGame()
    game.run()
