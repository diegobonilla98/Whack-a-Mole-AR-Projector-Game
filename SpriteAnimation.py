import time
import numpy as np
import cv2


class SpriteAnimation:
    def __init__(self, animation_frames, seconds, repetitions=1, name=""):
        self.name = name
        self.animation_frames = animation_frames
        self.animation_size = self.animation_frames.shape[1:3][::-1]
        if repetitions > 1:
            animation_frames_org = self.animation_frames.copy()
            for _ in range(repetitions - 1):
                self.animation_frames = np.concatenate([self.animation_frames, animation_frames_org], axis=0)
        self.infinite_loop = seconds < 1
        self.total_frames = self.animation_frames.shape[0]
        self.current_animation_idx = 0
        self.ttl = seconds
        self.seconds_per_frame = 1 / 12 if self.infinite_loop else self.ttl / self.total_frames
        self.last_frame_time = 0
        self.started_time = 0

    def get_static_frame(self):
        return self.animation_frames[-1]

    def get_frame(self):
        if self.last_frame_time == 0:
            self.started_time = time.time()
            self.last_frame_time = time.time()
            return self.animation_frames[self.current_animation_idx]
        if time.time() - self.last_frame_time > self.seconds_per_frame:
            self.current_animation_idx += 1
            if self.current_animation_idx >= self.total_frames:
                if self.infinite_loop:
                    self.current_animation_idx = 0
                else:
                    self.current_animation_idx = self.total_frames - 1
            self.last_frame_time = time.time()
            return self.animation_frames[self.current_animation_idx]
        else:
            return self.animation_frames[self.current_animation_idx]

    def is_done(self):
        return time.time() - self.started_time > self.ttl


class PointsMessage:
    def __init__(self, pos, points):
        self.ttl = 100
        self.message = ""
        self.init_pos = pos
        self.pos = pos
        self.points = points

    def display(self, ctx):
        cv2.putText(ctx, f"+{self.points}" if self.points >= 0 else f"{self.points}", tuple(self.pos), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3, cv2.LINE_AA)

    def update(self):
        self.ttl -= 1
        self.pos[1] -= 2

    def is_dead(self):
        return self.ttl <= 0


class DustEffectAnimation:
    def __init__(self, pos, ttl=0.5):
        self.pos = pos
        self.ttl = ttl
        self.initial_time = time.time()
        self.cut_frames = [[0., self.ttl / 3.], [self.ttl / 3., 2 * self.ttl / 3], [2 * self.ttl / 3, self.ttl]]
        self.rotate_codes = [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_180]
        self.scale = 1.

    def transform_frame(self, frame, mask, original_size):
        self.scale = np.clip(self.ttl - (time.time() - self.initial_time), 0., self.ttl)
        self.scale += 0.5
        frame = cv2.resize(frame, (int(original_size[0] * self.scale), int(original_size[1] * self.scale)))
        mask = cv2.resize(mask, (int(original_size[0] * self.scale), int(original_size[1] * self.scale)))
        idx = 0
        for i, interval in enumerate(self.cut_frames):
            if interval[0] < time.time() - self.initial_time < interval[1]:
                idx = i
                break
        frame = cv2.rotate(frame, self.rotate_codes[idx])
        mask = cv2.rotate(mask, self.rotate_codes[idx])
        return frame, mask

    def is_dead(self):
        return time.time() - self.initial_time > self.ttl
