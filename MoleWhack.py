import cv2
import numpy as np
import time
from FPS import CountsPerSec
from SpriteAnimation import SpriteAnimation, PointsMessage, DustEffectAnimation
from Mole import Mole
import simpleaudio as sa
from scipy.spatial.distance import euclidean

did_click = False
click_pos = (-1, -1)


def click(event, mouse_x, mouse_y, flags, param):
    global click_pos, did_click
    if event == cv2.EVENT_LBUTTONDBLCLK:
        print(f"{mouse_x}, {mouse_y}")
        print()
    if event == cv2.EVENT_LBUTTONDOWN:
        did_click = True
        click_pos = (mouse_x, mouse_y)


cv2.namedWindow('Output', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Output', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setMouseCallback('Output', click)

se_mole_hit = sa.WaveObject.from_wave_file('103526__tschapajew__pain-scream-hard-1.wav')
se_mole_exit = sa.WaveObject.from_wave_file('252028__mananimal__dig-stones.wav')
se_smash = sa.WaveObject.from_wave_file('rock-smash-6304.wav')

mole_sprite_size = (250, 250)

title = cv2.imread("frame_1637511634485.png", cv2.IMREAD_UNCHANGED)
title = cv2.resize(title, (1920 // 3, 1080 // 3))
title_mask = cv2.cvtColor(title[:, :, 3], cv2.COLOR_GRAY2RGB)
title = title[:, :, :3]

dust = cv2.imread("fight-dust-cloud-png.png", cv2.IMREAD_UNCHANGED)
dust = cv2.resize(dust, mole_sprite_size)
dust_mask = cv2.cvtColor(dust[:, :, 3], cv2.COLOR_GRAY2RGB) / 255.
dust = dust[:, :, :3]

background = SpriteAnimation(np.load('background.npy'), 0)
mole_hole = np.load('mole_hole.npy')
mole_hit = np.load('mole_hit.npy')
fps = CountsPerSec().start()

free_canvas_start = (522, 176)
free_canvas_size = (1239, 808)
num_moles_x = 3
num_moles_y = 2
space_within_x = int((free_canvas_size[0] - num_moles_x * mole_sprite_size[0]) / (num_moles_x + 1))
space_within_y = int((free_canvas_size[1] - num_moles_y * mole_sprite_size[1]) / (num_moles_y + 1))
moles = []
for i in range(num_moles_x):
    for j in range(num_moles_y):
        moles.append(Mole((free_canvas_start[0] + space_within_x + space_within_x * i + i * mole_sprite_size[0],
                           free_canvas_start[1] + space_within_y + space_within_x * j + j * mole_sprite_size[1])))
first_frame = True
start_menu = True
points = 0
animation_points_message = []
animation_dust_effect = []

while True:
    init_frame = time.time()
    frame = background.get_frame()
    canvas = frame.copy()

    if start_menu:
        scale = (np.sin(fps.num_occurrences * 0.2) + 2.) / 2. * (1.1 - 0.9) + 0.9
        title_a = cv2.resize(title, None, fx=scale, fy=scale)
        title_mask_a = cv2.resize(title_mask, None, fx=scale, fy=scale)
        canvas = cv2.GaussianBlur(canvas, (21, 21), 0)
        pos = (canvas.shape[0] // 2, canvas.shape[1] // 2)
        back = canvas.copy()
        back_mask = np.zeros_like(back)
        image_first_half = [title_a.shape[0] // 2, title_a.shape[1] // 2]
        image_second_half = [title_a.shape[0] - image_first_half[0], title_a.shape[1] - image_first_half[1]]
        back[pos[0] - image_first_half[0]: pos[0] + image_second_half[0],
             pos[1] - image_first_half[1]: pos[1] + image_second_half[1]] = title_a
        back_mask[pos[0] - image_first_half[0]: pos[0] + image_second_half[0],
                  pos[1] - image_first_half[1]: pos[1] + image_second_half[1]] = title_mask_a
        back_mask = back_mask.astype(np.float32) / 255.
        canvas_a = np.uint8(back * back_mask + canvas * (1. - back_mask))
        if did_click:
            if pos[1] - title_a.shape[1] / 2 < click_pos[0] < pos[1] + title_a.shape[1] / 2 and pos[0] - title_a.shape[0] / 2 < click_pos[1] < pos[0] + title_a.shape[0] / 2:
                start_menu = False
        did_click = False
        cv2.imshow('Output', canvas_a)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        fps.increment()
        continue

    if first_frame:
        first_frame = False
        for mole in moles:
            mole.start()

    if did_click:
        se_smash.play()
    for mole in moles:
        mole.update()
        if mole.state == 0:
            if mole.current_animation is None or mole.current_animation.name != "exit":
                se_mole_exit.play()
                mole.current_animation = SpriteAnimation(mole_hole.copy(), 1, name="exit")
        if mole.state == 1:
            if mole.current_animation is None or mole.current_animation.name != "hit":
                se_mole_hit.play()
                mole.current_animation = SpriteAnimation(mole_hit.copy(), 1, 3, name="hit")
        if mole.state == 2:
            if mole.current_animation is None or mole.current_animation.name != "enter":
                mole.current_animation = SpriteAnimation(mole_hole.copy()[::-1], 1, name="enter")

        if mole.current_animation is not None:
            sprite = mole.current_animation.get_frame()
            canvas[mole.pos[1]: mole.pos[1] + mole_sprite_size[1],
                   mole.pos[0]: mole.pos[0] + mole_sprite_size[0]] = sprite
            if mole.current_animation.is_done():
                if mole.current_animation.name == "enter":
                    mole.reset()
        if did_click:
            if mole.pos[0] + mole_sprite_size[0] > click_pos[0] > mole.pos[0] and mole.pos[1] + mole_sprite_size[1] > click_pos[1] > mole.pos[1]:
                plus = mole.hit()
                if plus != 0:
                    points += plus
                    animation_points_message.append(PointsMessage([mole.pos[0] + mole_sprite_size[0] // 2, mole.pos[1] + mole_sprite_size[1] // 2], plus))
    if did_click:
        animation_dust_effect.append(DustEffectAnimation(click_pos))

    for anim in reversed(animation_dust_effect):
        try:
            dust_a, dust_mask_a = anim.transform_frame(dust.copy(), dust_mask.copy(), mole_sprite_size)
            cut = canvas[anim.pos[1] - int(mole_sprite_size[1] * anim.scale) // 2: anim.pos[1] + int(mole_sprite_size[1] * anim.scale) // 2,
                         anim.pos[0] - int(mole_sprite_size[0] * anim.scale) // 2: anim.pos[0] + int(mole_sprite_size[0] * anim.scale) // 2]
            dust_a = cv2.resize(dust_a, (cut.shape[1], cut.shape[0]))
            dust_mask_a = cv2.resize(dust_mask_a, (cut.shape[1], cut.shape[0]))
            cut = np.uint8(dust_a * dust_mask_a + cut * (1. - dust_mask_a))
            canvas[anim.pos[1] - int(mole_sprite_size[1] * anim.scale) // 2: anim.pos[1] + int(mole_sprite_size[1] * anim.scale) // 2,
                   anim.pos[0] - int(mole_sprite_size[0] * anim.scale) // 2: anim.pos[0] + int(mole_sprite_size[0] * anim.scale) // 2] = cut
        except Exception as e:
            pass
        if anim.is_dead():
            animation_dust_effect.remove(anim)

    for anim in reversed(animation_points_message):
        anim.display(canvas)
        anim.update()
        if anim.is_dead():
            animation_points_message.remove(anim)

    cv2.putText(canvas, f"Points: {points}", (400, 65), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3, cv2.LINE_AA)

    did_click = False
    cv2.imshow('Output', canvas)

    wait_ms = int(np.clip(1000. * (1. / 64 - (time.time() - init_frame)), 1, np.inf))
    key = cv2.waitKey(wait_ms)
    if key == ord('q'):
        break
    fps.increment()

cv2.destroyAllWindows()
