"""
Parses Unreal Engine 5's LiveLink UDP Stream.


"""
from enum import IntEnum

import numpy as np
import struct
from typing import NamedTuple, List


class BlendShapes(IntEnum):
    # Left eye blend shapes
    EyeBlinkLeft = 0
    EyeLookDownLeft = 1
    EyeLookInLeft = 2
    EyeLookOutLeft = 3
    EyeLookUpLeft = 4
    EyeSquintLeft = 5
    EyeWideLeft = 6
    # Right eye blend shapes
    EyeBlinkRight = 7
    EyeLookDownRight = 8
    EyeLookInRight = 9
    EyeLookOutRight = 10
    EyeLookUpRight = 11
    EyeSquintRight = 12
    EyeWideRight = 13
    # Jaw blend shapes
    JawForward = 14
    JawLeft = 15
    JawRight = 16
    JawOpen = 17
    # Mouth blend shapes
    MouthClose = 18
    MouthFunnel = 19
    MouthPucker = 20
    MouthLeft = 21
    MouthRight = 22
    MouthSmileLeft = 23
    MouthSmileRight = 24
    MouthFrownLeft = 25
    MouthFrownRight = 26
    MouthDimpleLeft = 27
    MouthDimpleRight = 28
    MouthStretchLeft = 29
    MouthStretchRight = 30
    MouthRollLower = 31
    MouthRollUpper = 32
    MouthShrugLower = 33
    MouthShrugUpper = 34
    MouthPressLeft = 35
    MouthPressRight = 36
    MouthLowerDownLeft = 37
    MouthLowerDownRight = 38
    MouthUpperUpLeft = 39
    MouthUpperUpRight = 40
    # Brow blend shapes
    BrowDownLeft = 41
    BrowDownRight = 42
    BrowInnerUp = 43
    BrowOuterUpLeft = 44
    BrowOuterUpRight = 45
    # Cheek blend shapes
    CheekPuff = 46
    CheekSquintLeft = 47
    CheekSquintRight = 48
    # Nose blend shapes
    NoseSneerLeft = 49
    NoseSneerRight = 50
    TongueOut = 51
    # Treat the head rotation as curves for LiveLink support
    HeadYaw = 52
    HeadPitch = 53
    HeadRoll = 54
    # Treat eye rotation as curves for LiveLink support
    LeftEyeYaw = 55
    LeftEyePitch = 56
    LeftEyeRoll = 57
    RightEyeYaw = 58
    RightEyePitch = 59
    RightEyeRoll = 60


BLEND_SHAPE_ARR = list(BlendShapes)


class FrameTime(NamedTuple):
    framenum: int
    subframe: int
    fps_numerator: int
    fps_denominator: int


class Livelink(NamedTuple):
    packet_ver: int
    device_id: str
    subject_name: str
    frametime: FrameTime
    blendshape_count: int
    face_blend_shapes_values: List[float]


class LivelinkBuffer:
    def __init__(self, buffer, offset=0):
        self.buffer = buffer
        self.offset = offset

    def parse(self, unpack_format: str):
        if not unpack_format.startswith('>') and not unpack_format.startswith('<'):
            unpack_format = '>' + unpack_format
        retval = struct.unpack_from(unpack_format, self.buffer, self.offset)
        self.offset += struct.calcsize(unpack_format)
        return retval

    def parse_numpy(self, dtype, count):
        np_dtype = np.dtype(dtype).newbyteorder('>')
        retval = np.frombuffer(self.buffer, offset=self.offset, dtype=np_dtype, count=count)
        self.offset += struct.calcsize(np_dtype.kind) * count
        return retval

    def parse_str(self):
        length, *_ = self.parse('i')
        if length > 0:
            retval = self.buffer[self.offset:self.offset + length]
            self.offset += length
            return retval.decode('utf8')
        return ''

    def parse_frametime(self):
        return FrameTime(*self.parse('ifii'))

    def parse_livelink(self):
        packet_ver, *_ = self.parse('B')
        if packet_ver != 6:
            raise NotImplementedError("Cannot support packet version: " + str(packet_ver))
        try:
            device_id, *_ = self.parse_str()
            subject_name = self.parse_str()
            frametime = self.parse_frametime()
            blendshape_count, *_ = self.parse('B')
            # In Unreal Engine code you have a check condition before
            # blendshape_count is serialized. If the next byte is
            # equal to the packet version, this is the start of a new packet
            if blendshape_count != len(BlendShapes):
                self.offset -= struct.calcsize('B')
                return None
            face_blend_shapes_values = self.parse_numpy(np.float32, blendshape_count).clip(0, 1)
            return Livelink(
                packet_ver, device_id, subject_name,
                frametime,
                blendshape_count, face_blend_shapes_values
            )
        # Buffer overflows and dropped packets are handled in this way.
        except struct.error:
            return None

