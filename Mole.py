import time
import random
import numpy as np


class Mole:
    def __init__(self, pos, random_sec_int=(2, 7), out_sec=2):
        self.random_sec_int = random_sec_int
        self.out_sec = out_sec
        self.pos = pos
        self.state = -2
        self.time2exit = random.random() * (self.random_sec_int[1] - self.random_sec_int[0]) + self.random_sec_int[0]
        self.last_time = time.time()
        self.time_when_outside = time.time()
        self.current_animation = None

    def start(self):
        self.state = -1
        self.last_time = time.time()

    def hit(self):
        if self.state == 0:
            self.last_time = time.time()
            self.state = 1
            self.time2exit = 1
            t = time.time() - self.time_when_outside
            if t > 1.5:
                return 10
            elif 1. < t <= 1.5:
                return 50
            elif 0.5 < t <= 1.:
                return 100
            elif 0.2 < t <= 0.5:
                return 500
            elif 0.2 > t:
                return 1000
        return 0

    def reset(self):
        self.state = -1
        self.time2exit = random.random() * (self.random_sec_int[1] - self.random_sec_int[0]) + self.random_sec_int[0]

    def update(self):
        if self.action_time():
            self.last_time = time.time()
            if self.state == -1:
                self.time_when_outside = time.time()
                self.state = 0
                self.time2exit = self.out_sec
            elif self.state == 0:
                self.state = 2
            elif self.state == 1:
                self.state = 2

    def action_time(self):
        return time.time() - self.last_time >= self.time2exit
