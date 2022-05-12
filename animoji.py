import time
from threading import Thread

import pyrender
import numpy as np
import tqdm
import gltflib
import socket
from multiprocessing import Array

import renderer
from livelink import BlendShapes, LivelinkBuffer

FPS = 1/60


def render_morphs(v, scene, buf):
    last_rendered = None
    with tqdm.tqdm() as pbar:
        while v.is_active:
            if not hasattr(buf, 'value'):
                time.sleep(FPS)
                continue
            livelink_data = buf.value
            if last_rendered == livelink_data:
                time.sleep(FPS)
                continue
            last_rendered = livelink_data
            livelink = LivelinkBuffer(livelink_data).parse_livelink()
            with v:
                if livelink is not None:
                    for mesh_idx, mesh in enumerate(scene.meshes):
                        if mesh.weights is not None:
                            mesh_mapping = mesh_mappings[mesh_idx]
                            if mesh_mapping:
                                mesh.weights = livelink.face_blend_shapes_values[mesh_mapping]
                            else:
                                mesh.weights = livelink.face_blend_shapes_values[:len(mesh.weights)]
            pbar.update()
            time.sleep(FPS)


def livelink_udp_spammer(v, buf):
    """Spams UDP socket reads and updates the multithreaded array"""
    UDP_IP = '0.0.0.0'
    UDP_PORT = 11111

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    while v.is_active():
        livelink_data, _ = sock.recvfrom(500)
        buf.value = livelink_data
        # time.sleep(FPS)


def livelink_file_reader(v, buf):
    with open('./experimentation/livelink.udp', 'rb') as f:
        livelink = LivelinkBuffer(f.read())
    prev_offset = 0
    while v.is_active():
        livelink.parse_livelink()
        curr_offset = livelink.offset
        buf.value = livelink.buffer[prev_offset: curr_offset]
        prev_offset = curr_offset
        time.sleep(1/20)


if __name__ == '__main__':
    gltf = gltflib.GLTF.load('./model_me.glb', load_file_resources=True)
    mesh_mappings = [
        [
            int(BlendShapes[target_name[0].upper() + target_name[1:]])
            for target_name in mesh.extras['targetNames']
        ] if 'targetNames' in mesh.extras else None
        for mesh in gltf.model.meshes
    ]

    scene = pyrender.Scene.from_gltflib_scene(gltf)

    buf = Array('b', 500)
    v = renderer.FakeWebcamRenderer(scene)
    t = Thread(target=render_morphs, args=(v, scene, buf))
    u = Thread(target=livelink_udp_spammer, args=(v, buf))
    u.start()
    t.start()
    v.start()

    # t.join(timeout=3)
    # u.join(timeout=3)
