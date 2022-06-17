import pygame
import random
from scipy.spatial import distance
from enum import Enum
from collections import namedtuple
import numpy as np

pygame.init()
font = pygame.font.Font('arial.ttf', 25)


class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4


class Angle(Enum):
    NINTY = 1,
    ONE_EIGHTY = 2,
    TWO_SEVENTY = 3


WIDTH = 1280
HEIGHT = 960
BLOCK_SIZE = 40
SPEED = 100
HIDERS_AMOUNT = 10
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (200, 0, 0)
BLUE1 = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0, 0, 0)
TRANSPARENT = (255, 255, 255, 0)
EATING_LENGTH = 5
GAMES_TO_USER_ACTIVATION = 1000

AVAILABLE_ANGLES = [Angle.NINTY, Angle.ONE_EIGHTY, Angle.TWO_SEVENTY]

Point = namedtuple('Point', 'x, y')
bg = pygame.image.load("lasagne.png")
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

herbs = pygame.image.load("leaf.png")
herbs = pygame.transform.scale(herbs, (BLOCK_SIZE, BLOCK_SIZE))

meat = pygame.image.load("chicken.png")
meat = pygame.transform.scale(meat, (BLOCK_SIZE, BLOCK_SIZE))

emoji = pygame.image.load("smile_face.png")
emoji = pygame.transform.scale(emoji, (BLOCK_SIZE, BLOCK_SIZE))

emoji_eat = pygame.image.load("eating_face_yellow.png")
emoji_eat = pygame.transform.scale(emoji_eat, (BLOCK_SIZE, BLOCK_SIZE))

player = pygame.image.load("smile_face_orange.png")
player = pygame.transform.scale(player, (BLOCK_SIZE, BLOCK_SIZE))

player_eat = pygame.image.load("eating_face.png")
player_eat = pygame.transform.scale(player_eat, (BLOCK_SIZE, BLOCK_SIZE))

AVAILABLE_OBSTACLES = [
    [Point(0, 0), Point(1 * BLOCK_SIZE, 0), Point(2 * BLOCK_SIZE, 0), Point(3 * BLOCK_SIZE, 0), Point(3 * BLOCK_SIZE,
                                                                                                      -1 * BLOCK_SIZE)],

    [Point(0, 0), Point(1 * BLOCK_SIZE, 0), Point(2 * BLOCK_SIZE, 0), Point(3 * BLOCK_SIZE, 0), Point(3 * BLOCK_SIZE,
                                                                                                      1 * BLOCK_SIZE)],

    [Point(0, 1 * BLOCK_SIZE), Point(0, 0), Point(1 * BLOCK_SIZE, 0), Point(2 * BLOCK_SIZE, 0),
     Point(3 * BLOCK_SIZE, 0),
     Point(3 * BLOCK_SIZE, 1 * BLOCK_SIZE)],

    [Point(0, 1 * BLOCK_SIZE), Point(0, 0), Point(1 * BLOCK_SIZE, 0), Point(2 * BLOCK_SIZE, 0),
     Point(3 * BLOCK_SIZE, 0),
     Point(3 * BLOCK_SIZE, -1 * BLOCK_SIZE)]
]


class SeekAndHideGame:

    def __init__(self, w=WIDTH, h=HEIGHT):
        self.w = w
        self.h = h

        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('EatTheMeat Game')
        self.clock = pygame.time.Clock()
        self.eating_length = 0
        self.player_eating_length = 0
        self.player_activated = False
        self.obstacles_placed = False
        self.games_played = 0
        self.computed_obstacle_arrangement = []
        self.frame_iteration = 0
        self.reset()

    def reset(self, player_activated=False, obstacles_placed=False):
        self.player_activated = player_activated
        self.direction = Direction.RIGHT
        self.player_direction = Direction.RIGHT
        self.head = Point(self.w / 2, self.h / 2)
        self.player_head = Point(self.w / 2, self.h / 2)
        self.seeker = [self.head,
                       Point(self.head.x - BLOCK_SIZE, self.head.y),
                       Point(self.head.x - (2 * BLOCK_SIZE), self.head.y)]

        self.player_seeker = [self.player_head,
                              Point(self.player_head.x - BLOCK_SIZE, self.player_head.y),
                              Point(self.player_head.x - (2 * BLOCK_SIZE), self.player_head.y)]

        self.score = 0
        self.player_score = 0
        self.hiders = []
        self.obstacles = []
        self.frame_iteration = 0

        if self.player_activated or obstacles_placed:
            self._place_obstacles()

        self.games_played = 0 if self.games_played is None else self.games_played + 1
        self._place_hiders()

    def _place_hiders(self):
        for i in range(HIDERS_AMOUNT):
            while True:
                overlap_obstacle = False
                x = random.randint(0, (self.w - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
                y = random.randint(0, (self.h - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
                hider = Point(x, y)
                for obstacle in self.obstacles:
                    if hider in obstacle:
                        overlap_obstacle = True
                if hider not in self.seeker or hider not in self.player_seeker or (
                        hider.x >= self.w - BLOCK_SIZE or hider.x <= BLOCK_SIZE or hider.y >= self.h - BLOCK_SIZE or hider.y <= BLOCK_SIZE) or overlap_obstacle is False:
                    self.hiders.append(hider)
                    break

    def random_obstacle_transition(self, obstacle, obstacle_index):
        if obstacle_index == 0:
            angle_index = 0
            shift_ratio = 11
        elif obstacle_index == 1:
            angle_index = 1
            shift_ratio = 17
        elif obstacle_index == 2:
            angle_index = 1
            shift_ratio = 22
        else:
            angle_index = 2
            shift_ratio = 5

        return self.fixed_obstacle_transition(obstacle, angle_index, shift_ratio)

    def fixed_obstacle_transition(self, obstacle, angle_index, shift_ratio):
        random_shift = shift_ratio * BLOCK_SIZE
        angle = AVAILABLE_ANGLES[angle_index]
        transformed_obstacle = []
        shifted_obstacle = []
        if angle == Angle.NINTY:
            for point in obstacle:
                new_point = Point(point.y, -point.x)
                transformed_obstacle.append(new_point)
        elif angle == Angle.ONE_EIGHTY:
            for point in obstacle:
                new_point = Point(-point.x, -point.y)
                transformed_obstacle.append(new_point)
        else:
            for point in obstacle:
                new_point = Point(-point.y, point.x)
                transformed_obstacle.append(new_point)

        for point in transformed_obstacle:
            shifted_obstacle.append(Point(point.x + random_shift, point.y + random_shift))

        return shifted_obstacle

    def _place_obstacles(self):
        for obstacle_idx, obstacle in enumerate(AVAILABLE_OBSTACLES):
            while True:
                overlap = False
                out_of_canvas = False
                transformed_obstacle = self.random_obstacle_transition(obstacle, obstacle_idx)
                for placed_obstacle in self.obstacles:
                    bordered_obstacle = self.get_bordered_obstacle(placed_obstacle)
                    for point in transformed_obstacle:
                        if point in bordered_obstacle:
                            overlap = True

                max_x = max([point.x for point in transformed_obstacle])
                min_x = min([point.x for point in transformed_obstacle])
                max_y = max([point.y for point in transformed_obstacle])
                min_y = min([point.y for point in transformed_obstacle])

                if max_x >= self.w - BLOCK_SIZE or min_x <= BLOCK_SIZE or max_y >= self.h - BLOCK_SIZE or min_y <= BLOCK_SIZE:
                    out_of_canvas = True

                if transformed_obstacle not in self.seeker and transformed_obstacle not in self.player_seeker and transformed_obstacle not in self.hiders and overlap is False and out_of_canvas is False:
                    self.obstacles.append(transformed_obstacle)
                    break

    def get_distance_to_closer_obstacle(self):
        minimum_distance = 100000000000
        for obstacle in self.obstacles:
            for obstacle_point in obstacle:
                current_distance = self.get_euclidean_distance(obstacle_point, self.head)
                if current_distance < minimum_distance:
                    minimum_distance = current_distance

        if self.head.x > self.w - BLOCK_SIZE or self.head.x < 0 or self.head.y > self.h - BLOCK_SIZE or self.head.y < 0:
            minimum_distance = 0

        return int(minimum_distance)

    def get_euclidean_distance(self, point1, point2):
        return distance.euclidean((point1.x, point1.y), (point2.x, point2.y))

    def get_bordered_obstacle(self, obstacle):
        bordered_obstacle = [point for point in obstacle]
        for point in obstacle:
            bordered_obstacle.append(Point(point.x + BLOCK_SIZE, point.y + BLOCK_SIZE))
            bordered_obstacle.append(Point(point.x, point.y + BLOCK_SIZE))
            bordered_obstacle.append(Point(point.x - BLOCK_SIZE, point.y + BLOCK_SIZE))
            bordered_obstacle.append(Point(point.x - BLOCK_SIZE, point.y))
            bordered_obstacle.append(Point(point.x - BLOCK_SIZE, point.y - BLOCK_SIZE))
            bordered_obstacle.append(Point(point.x, point.y - BLOCK_SIZE))
            bordered_obstacle.append(Point(point.x + BLOCK_SIZE, point.y - BLOCK_SIZE))
            bordered_obstacle.append(Point(point.x + BLOCK_SIZE, point.y))

        return bordered_obstacle

    def play_step(self, action):
        player_new_direction = self.player_direction
        self.frame_iteration += 1

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    player_new_direction = Direction.LEFT
                if event.key == pygame.K_RIGHT:
                    player_new_direction = Direction.RIGHT
                if event.key == pygame.K_DOWN:
                    player_new_direction = Direction.DOWN
                if event.key == pygame.K_UP:
                    player_new_direction = Direction.UP
                if event.key == pygame.K_1:
                    return -10, True, self.score, self.player_score
                if event.key == pygame.K_2:
                    return 20, True, self.score, self.player_score

            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        self._move(action, player_new_direction)
        self.seeker.insert(0, self.head)
        self.player_seeker.insert(0, self.player_head)

        reward = 0
        game_over = False

        if self.player_activated:
            if self.is_player_collision():
                game_over = True
                return reward, game_over, self.score, self.player_score

        if self.is_collision():
            game_over = True
            reward = -10
            return reward, game_over, self.score, self.player_score

        # if self.frame_iteration > 300:
        #     game_over = True
        #     reward = -100000
        #     return reward, game_over, self.score, self.player_score

        if self.player_activated:
            if self.player_head in self.hiders:
                self.player_score += 1
                icon = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                icon.blit(player_eat, (0, 0))
                self.display.blit(icon, (self.player_head.x, self.player_head.y))
                self.player_eating_length = EATING_LENGTH

                if len(self.hiders) - 1 == 0:
                    self._place_hiders()

                self.hiders.remove(self.player_head)
            else:
                self.player_seeker.pop()

        if self.head in self.hiders:
            self.score += 1
            self.frame_iteration = 0
            eat = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
            eat.blit(emoji_eat, (0, 0))
            self.display.blit(eat, (self.head.x, self.head.y))
            self.eating_length = EATING_LENGTH

            if len(self.hiders) - 1 == 0:
                self._place_hiders()

            reward = 10
            self.hiders.remove(self.head)
        else:
            self.seeker.pop()

        self._update_ui()
        self.clock.tick(SPEED)

        return reward, game_over, self.score, self.player_score

    def is_collision(self, pt=None):
        if pt is None:
            pt = self.head

        if pt.x > self.w - BLOCK_SIZE or pt.x < 0 or pt.y > self.h - BLOCK_SIZE or pt.y < 0:
            return True

        for obstacle in self.obstacles:
            if pt in obstacle:
                return True

        return False

    def is_player_collision(self):
        player_coords = self.player_head

        if self.player_activated:
            if player_coords.x > self.w - BLOCK_SIZE or player_coords.x < 0 or player_coords.y > self.h - BLOCK_SIZE or player_coords.y < 0:
                return True

            for obstacle in self.obstacles:
                if player_coords in obstacle:
                    return True

        return False

    def perform_emoji_transformation(self, emoji_icon, direction_object):
        if direction_object == Direction.UP:
            icon = pygame.transform.rotate(emoji_icon, 270)
            icon = pygame.transform.flip(icon, False, True)
            return icon
        elif direction_object == Direction.DOWN:
            icon = pygame.transform.rotate(emoji_icon, 90)
            icon = pygame.transform.flip(icon, False, True)
            return icon
        elif direction_object == Direction.LEFT:
            return pygame.transform.flip(emoji_icon, True, False)
        else:
            return emoji_icon

    def _update_ui(self):
        # if self.games_played >= 50:
            self.display.blit(bg, (0, 0))

            for pt in self.seeker:
                s = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                s.set_alpha(0)
                s.fill((255, 255, 255))
                self.display.blit(s, (pt.x, pt.y))

            if self.player_activated:
                for pt in self.player_seeker:
                    s = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                    s.set_alpha(0)
                    s.fill((255, 255, 255))
                    self.display.blit(s, (pt.x, pt.y))

            s = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)

            emoji_transformed = self.perform_emoji_transformation(emoji, self.direction)
            emoji_eat_transformed = self.perform_emoji_transformation(emoji_eat, self.direction)

            if self.player_activated:
                player_transformed = self.perform_emoji_transformation(player, self.player_direction)
                player_eat_transformed = self.perform_emoji_transformation(player_eat, self.player_direction)

                if self.player_eating_length <= 0:
                    s.blit(player_transformed, (0, 0))
                    self.display.blit(s, (self.player_seeker[0].x, self.player_seeker[0].y))
                else:
                    s.blit(player_eat_transformed, (0, 0))
                    self.display.blit(s, (self.player_seeker[0].x, self.player_seeker[0].y))
                    self.player_eating_length -= 1

            if self.eating_length <= 0:
                s.blit(emoji_transformed, (0, 0))
                self.display.blit(s, (self.seeker[0].x, self.seeker[0].y))
            else:
                s.blit(emoji_eat_transformed, (0, 0))
                self.display.blit(s, (self.seeker[0].x, self.seeker[0].y))
                self.eating_length -= 1

            for pt in self.hiders:
                s = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                s.blit(meat, (0, 0))
                self.display.blit(s, (pt.x, pt.y))

            for obstacle in self.obstacles:
                for pt in obstacle:
                    s = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                    s.blit(herbs, (0, 0))
                    self.display.blit(s, (pt.x, pt.y))

            if self.player_activated:
                text = font.render("Score: " + str(self.score), True, WHITE, BLACK)
                text2 = font.render("Player score: " + str(self.player_score), True, WHITE, BLACK)
                self.display.blit(text2, [0, 30])
            else:
                text = font.render(
                    "AI is learning... " + str((GAMES_TO_USER_ACTIVATION - self.games_played) + 2) + " games left", True,
                    WHITE, BLACK)

            self.display.blit(text, [0, 0])
            pygame.display.flip()

    def _move(self, action, player_direction):
        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        idx = clock_wise.index(self.direction)

        if np.array_equal(action, [1, 0, 0]):
            new_dir = clock_wise[idx]
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx]
        else:
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx]

        self.direction = new_dir
        self.player_direction = player_direction

        x = self.head.x
        y = self.head.y

        x_player = self.player_head.x
        y_player = self.player_head.y

        if self.player_direction == Direction.RIGHT:
            x_player += BLOCK_SIZE
        elif self.player_direction == Direction.LEFT:
            x_player -= BLOCK_SIZE
        elif self.player_direction == Direction.DOWN:
            y_player += BLOCK_SIZE
        elif self.player_direction == Direction.UP:
            y_player -= BLOCK_SIZE

        if self.direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif self.direction == Direction.UP:
            y -= BLOCK_SIZE

        self.head = Point(x, y)
        self.player_head = Point(x_player, y_player)