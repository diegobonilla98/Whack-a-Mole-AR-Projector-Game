import pyrealsense2 as rs
import numpy as np
import cv2
import os
import fcntl
import subprocess
from scipy.spatial.distance import euclidean


USBDEVFS_RESET = ord('U') << (4 * 2) | 20
spatial = pipeline = None


def get_bus_device():
    proc = subprocess.Popen(['lsusb'], stdout=subprocess.PIPE)
    out = proc.communicate()[0].decode()
    lines = out.split('\n')
    for line in lines:
        if 'RealSense' in line:
            parts = line.split()
            bus = parts[1]
            dev = parts[3][:3]
            return '/dev/bus/usb/%s/%s' % (bus, dev)


def send_reset(dev_path):
    fd = os.open(dev_path, os.O_WRONLY)
    try:
        fcntl.ioctl(fd, USBDEVFS_RESET, 0)
    finally:
        os.close(fd)


def start_camera():
    global pipeline
    pipeline = rs.pipeline()
    config = rs.config()
    pipeline_wrapper = rs.pipeline_wrapper(pipeline)
    pipeline_profile = config.resolve(pipeline_wrapper)
    device = pipeline_profile.get_device()
    device_product_line = str(device.get_info(rs.camera_info.product_line))
    for s in device.sensors:
        if s.get_info(rs.camera_info.name) == 'RGB Camera':
            break
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    if device_product_line == 'L500':
        config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
    else:
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    pipeline.start(config)


def use_filter():
    global spatial
    spatial = rs.spatial_filter()
    spatial.set_option(rs.option.filter_magnitude, 5)
    spatial.set_option(rs.option.filter_smooth_alpha, 1)
    spatial.set_option(rs.option.filter_smooth_delta, 50)
    spatial.set_option(rs.option.holes_fill, 2)


def get_frames(scale_depth=True):
    try:
        frames = pipeline.wait_for_frames()
    except RuntimeError as e:
        print(e)
        release()
        exit(1)
    depth_frame = frames.get_depth_frame()
    color_frame = frames.get_color_frame()
    if not depth_frame or not color_frame:
        return False, None, None
    if spatial is not None:
        depth_frame = spatial.process(depth_frame)
    depth_frame = np.asanyarray(depth_frame.get_data())
    if scale_depth:
        depth_frame = rescale_depth(depth_frame)
    return True, np.asanyarray(color_frame.get_data()), depth_frame


def rescale_depth(depth_image):
    return cv2.convertScaleAbs(depth_image, alpha=0.03)


def release():
    send_reset(get_bus_device())
    ctx = rs.context()
    devices = ctx.query_devices()
    for dev in devices:
        dev.hardware_reset()
    pipeline.stop()


def remap(x, oMin, oMax, nMin, nMax):
    reverseInput = False
    oldMin = min(oMin, oMax)
    oldMax = max(oMin, oMax)
    if not oldMin == oMin:
        reverseInput = True
    reverseOutput = False
    newMin = min(nMin, nMax)
    newMax = max(nMin, nMax)
    if not newMin == nMin:
        reverseOutput = True
    portion = (x - oldMin) * (newMax - newMin) / (oldMax - oldMin)
    if reverseInput:
        portion = (oldMax - x) * (newMax - newMin) / (oldMax - oldMin)
    result = portion + newMin
    if reverseOutput:
        result = newMax - portion
    return result


class PointsMessage:
    def __init__(self, pos, cent):
        self.ttl = 100
        self.message = ""
        self.init_pos = pos
        self.pos = pos
        self.dfc = euclidean(pos, cent)
        self.points = int(-0.03731217 * self.dfc + 16.53458)

    def display(self, ctx):
        cv2.putText(ctx, f"+{self.points}" if self.points >= 0 else f"{self.points}", tuple(self.pos), cv2.FONT_HERSHEY_SIMPLEX, 2, (100, 100, 100), 3, cv2.LINE_AA)

    def update(self):
        self.ttl -= 1
        self.pos[1] -= 2

    def is_dead(self):
        return self.ttl <= 0
