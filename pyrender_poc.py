"""
ISSUE: I've figured out what I need to add to pyrender to get Morph Targets working. I would have to extend or replicate
the trimesh library for blendshapes (morph targets), then I would need to implement the backend in PyRender. Feels a bit
too much like doing everything in scratch. Will find another approach.

Then, after the render, I would need to pipe to pyfakewebcam library, which seems like the easiest part.
"""

import trimesh
import pyrender

polywink = trimesh.load("~/Downloads/POLYWINK_AIX_SAMPLE_out/POLYWINK_AIX_SAMPLE.gltf")
scene = pyrender.Scene.from_trimesh_scene(polywink)
# pyrender.Viewer(scene, use_raymond_lighting=True)

import pygltflib

gltf = pygltflib.GLTF2().load("/Users/awkii/Downloads/POLYWINK_AIX_SAMPLE_out/POLYWINK_AIX_SAMPLE.gltf")
print(gltf)
