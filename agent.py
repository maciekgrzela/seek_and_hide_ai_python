import sys

import torch
import random
import numpy as np
from collections import deque
from game import SeekAndHideGame, Direction, Point
from model import Linear_QNet, QTrainer
from helper import plot
import os
import pickle
import time
from tkinter import *

MAX_MEM = 100_000_000
BATCH_SIZE = 2000
LR = 0.001

BLOCK_SIZE = 20

GAMES_TO_END_BATTLE = 20


class Agent:

    def __init__(self, level, solver, game_mode):
        self.level = level
        self.game_mode = game_mode
        self.solver = solver
        self.n_games = 0
        self.iteration = 0
        self.epsilon = 0
        self.gamma = 0
        self.memory = deque(maxlen=MAX_MEM)
        self.model = self.load_evaluated_model()
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma, solver=solver)

    def load_evaluated_model(self):
        model_folder_path = './model'
        file_path = os.path.join(model_folder_path, 'model_entire_'+self.solver+'_'+self.level+'.pth')
        if not os.path.exists(file_path):
            return Linear_QNet(11, 256, 3)
        else:
            saved_model = torch.load(file_path)
            saved_model.eval()
            return saved_model


    def get_state(self, game):
        head = game.seeker[0]

        point_l = Point(head.x - BLOCK_SIZE, head.y)
        point_r = Point(head.x + BLOCK_SIZE, head.y)
        point_u = Point(head.x, head.y - BLOCK_SIZE)
        point_d = Point(head.x, head.y + BLOCK_SIZE)

        dir_l = game.direction == Direction.LEFT
        dir_r = game.direction == Direction.RIGHT
        dir_u = game.direction == Direction.UP
        dir_d = game.direction == Direction.DOWN

        state = [
            (dir_r and game.is_collision(point_r)) or
            (dir_l and game.is_collision(point_l)) or
            (dir_u and game.is_collision(point_u)) or
            (dir_d and game.is_collision(point_d)),

            (dir_u and game.is_collision(point_r)) or
            (dir_d and game.is_collision(point_l)) or
            (dir_l and game.is_collision(point_u)) or
            (dir_r and game.is_collision(point_d)),

            (dir_d and game.is_collision(point_r)) or
            (dir_u and game.is_collision(point_l)) or
            (dir_r and game.is_collision(point_u)) or
            (dir_l and game.is_collision(point_d)),

            dir_l,
            dir_r,
            dir_u,
            dir_d,

            0 if len(game.hiders) == 0 else game.hiders[0].x < game.head.x,
            0 if len(game.hiders) == 0 else game.hiders[0].x > game.head.x,
            0 if len(game.hiders) == 0 else game.hiders[0].y < game.head.y,
            0 if len(game.hiders) == 0 else game.hiders[0].y > game.head.y,
        ]

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self, training_based_on_pickle=False):
        self.iteration += 1

        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        if not training_based_on_pickle:
            with open('samples.pickle', 'wb') as pf:
                pf.close()
            with open('samples.pickle', 'wb') as pickle_file:
                pickle.dump(self.memory, pickle_file, pickle.HIGHEST_PROTOCOL)

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        self.epsilon = 80 - self.n_games
        final_move = [0, 0, 0]
        if random.randint(0, 200) < self.epsilon and not self.game_mode:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


class RunAgent:

    def __init__(self, level, solver, game_mode=True):
        self.level = level
        self.solver = solver
        self.game_mode = game_mode
        self.train()

    def close_game(self, pop):
        pop.destroy()
        sys.exit()

    def run_again(self, pop):
        pop.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)


    def train(self):
        plot_scores = []
        plot_mean_scores = []
        total_score = 0
        record = 0
        agent = Agent(level=self.level, solver=self.solver, game_mode=self.game_mode)
        game = SeekAndHideGame(game_mode=self.game_mode, level=self.level)

        while True:
            state_old = agent.get_state(game)
            final_move = agent.get_action(state_old)
            reward, done, score, player_score = game.play_step(final_move)
            state_new = agent.get_state(game)

            if not self.game_mode:
                agent.train_short_memory(state_old, final_move, reward, state_new, done)
                agent.remember(state_old, final_move, reward, state_new, done)

            if done:
                if agent.n_games + 1 == GAMES_TO_END_BATTLE and self.game_mode:

                    pop = Tk()
                    pop.title('EatTheMeat - End of the game')
                    pop.geometry("1065x900")

                    if game.score > game.player_score:
                        pop_background_image = PhotoImage(file="./EatTheMeat_loose.png")
                    elif game.score < game.player_score:
                        pop_background_image = PhotoImage(file="./EatTheMeat_win.png")
                    else:
                        pop_background_image = PhotoImage(file="./EatTheMeat_draw.png")

                    pop_background_label = Label(pop, image=pop_background_image)
                    pop_background_label.place(x=0, y=0, relwidth=1, relheight=1)

                    green_button = PhotoImage(file="./EatTheMeat_green_btn.png")

                    Button(pop, text='Nieee, już wystarczy', image=green_button, bg='white', command=lambda: self.close_game(pop), relief=FLAT, borderwidth=0, compound=CENTER).pack(side=BOTTOM)
                    Button(pop, text='Ja chce jeszcze raz!', image=green_button, bg='white', command=lambda: self.run_again(pop), relief=FLAT, borderwidth=0, compound=CENTER).pack(side=BOTTOM)

                    pop.mainloop()
                else:
                    if self.game_mode:
                        time.sleep(0.5)

                    game.reset(player_activated=self.game_mode, obstacles_placed=self.game_mode)

                    agent.n_games += 1

                    if not self.game_mode:
                        agent.train_long_memory()

                    if score > record and not self.game_mode:
                        record = score
                        agent.model.save(record=record)

                    plot_scores.append(score)
                    total_score += score
                    mean_score = total_score / agent.n_games
                    plot_mean_scores.append(mean_score)
                    if not self.game_mode:
                        plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    runAgent = RunAgent('test', 'adam', False)
