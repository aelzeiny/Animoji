# Animoji Clone

I've always wanted to join GVC/Zoom meetings with my Apple Animoji. Unfortunately, Apple has not made this a feature.
So I guess I have to take matters into my own hands.

Unreal Engine 5 comes with MetaHumans, and an online portal for MetaHuman customization, and an app called
Unreal Engine Live Link Face. Our goal is to be able to make a high-quality render of a custom Animoji or MetaHuman 
to a virtual webcam that can be used to join online meetings.

TL;DR:
```
iPhone Live Link App -> Virtual WebCam -> Google Meet / Zoom 
```

## Reverse Engineering the Unreal Engine Live Link Face App
See `Livelink UDP Structure Unpackin'.ipynb` notebook for a working example.

So this thing uses Apple's Face AR Kit to scan 61 float values, and dumps them to a UDP port. 
We can listen and record these bytes with netcat to create the `livelink.udp` file found in this repo.
The command is 
```bash
nc -ul 11111 > livelink.udp 2>&1
```

Fortunately for us, the Unreal Engine is open-source. So we can just peek the `AppleARKitLiveLinkSource.cpp`
file to reverse the serialization format the Unreal Engine uses.

## Apple's 52 Blend Shapes
Fortunately, this part is mostly documented by 3rd parties. An average AR Face Kit standardizes
on [52 blendshapes](https://arkit-face-blendshapes.com/). We can use Blender/Maya to create a 3D avatar for ourselves,
and the 52 blend-shapes needed in the 3D model to deform the mesh to make various facial expression.
These floats, clamped between [0, 1], define values like the amount the left eyebrow is raised, or the length
the tongue is protruded. I found plenty of tutorials for Blender on YouTube and services online to create these 52 
blendshapes.

The tricky part is exporting an AutoDesk FBX file to the open-source gLTF. Fortunately 
[FB open-sources FBX2glTF](https://github.com/facebookincubator/FBX2glTF) that also supports blendshapes.

## Current Plans
- [x] Reverse Engineer serialization format for LiveLink App 
- [ ] Render 3D avatar in Babylon.JS or PyRender
- [ ] Puppet 3D model with LiveLink UDP stream
- [ ] Serialize framebuffer to virtual webcam

## Maybe Future Plans?
In the future, if this works, I would love to:
- [ ] Make some type of emoji customization engine that avoids the work of making/purchasing a custom 3D avatar.
- [ ] Make this more compatible with standard webcams & non-apple devices.