import abc
from threading import RLock
import time

import numpy as np
import pyrender
import pyvirtualcam


def create_camera():
    return pyrender.Node(
        camera=pyrender.PerspectiveCamera(yfov=1.0471975511965976, zfar=100, znear=0.0004926449574960696),
        matrix=np.array([[0.9999451448020004, 0.010473495475301227, -0.00011523643331192809, 2.632996104694026e-05], [-0.010456117703794985, 0.9988101239021526, 0.047634084363313206, 0.0021249022974223746], [0.0006139946832835854, -0.047630266460473435, 0.9988648460765015, 0.0058722449231459], [0.0, 0.0, 0.0, 1.0]]),
        scale=np.ones(3),
        translation=np.array([0.004293392833761634, 0.0018634976900897661, 0.004657140988373949]),
        rotation=np.array([0.27059805007309856, 0.27059805007309856, 0.6532814824381883, 0.6532814824381883]),
    )


def create_lights():
    return pyrender.Viewer._create_raymond_lights(None)


class PyrenderRenderer:
    def __init__(self, scene):
        # CREATE CAMERA + LIGHTS
        cam_node = create_camera()
        scene.add_node(cam_node)
        scene.main_camera_node = cam_node

        # CREATE LIGHTS
        for light in create_lights():
            scene.add_node(light, parent_node=cam_node)

        self.viewer = pyrender.Viewer(scene, use_raymond_lighting=True, auto_start=False)

    def start(self):
        self.viewer.start()

    def is_active(self):
        return self.viewer.is_active

    def __enter__(self):
        self.viewer.render_lock.acquire()

    def __exit__(self, *args, **kwargs):
        self.viewer.render_lock.release()


class BufferFrameRenderer(abc.ABC):
    def __init__(self, scene):
        self.scene = scene

        # CREATE CAMERA
        camera_node = create_camera()
        scene.add_node(camera_node)
        scene.main_camera_node = camera_node

        # CREATE LIGHTS
        for light in pyrender.Viewer._create_raymond_lights(None):
            scene.add_node(light, parent_node=camera_node)

        self._is_active = False
        self.render_lock = RLock()
        self.renderer = pyrender.OffscreenRenderer(640,480)

    @abc.abstractmethod
    def start(self):
        pass

    def is_active(self):
        return self._is_active

    def __enter__(self):
        self.render_lock.acquire()

    def __exit__(self, *args, **kwargs):
        self.render_lock.release()


class OpenCvRenderer(BufferFrameRenderer):
    def start(self):
        import cv2
        self._is_active = True

        while True:
            with self:
                color, _ = self.renderer.render(self.scene, pyrender.RenderFlags.ALL_SOLID)
                # RGB -> BGR
            color_bgr = cv2.cvtColor(color, cv2.COLOR_RGB2BGR)
            cv2.imshow('memoji', color_bgr)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self._is_active = False
        cv2.destroyAllWindows()


class FakeWebcamRenderer(BufferFrameRenderer):
    def start(self):
        with pyvirtualcam.Camera(width=self.renderer.viewport_width, height=self.renderer.viewport_height, fps=30) as camera:
            self._is_active = True
            while True:
                with self:
                    color, _ = self.renderer.render(self.scene, pyrender.RenderFlags.ALL_SOLID)
                camera.send(color)
                camera.sleep_until_next_frame()
        self._is_active = False
