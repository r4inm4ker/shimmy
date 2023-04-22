# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
#https://github.com/gildor2/UModel/blob/master/Exporters/Psk.h

""" This module imports psa animation as maya keyframes
referenced  from https://github.com/Befzz/blender3d_import_psk_psa
author: Jefri Haryono
website : https://jefriyeh.com
"""


from struct import unpack, unpack_from, Struct

import maya.cmds as mc
import maya.api.OpenMaya as om2

from shimmy.lib import Path, timeIt

from .funcs import get_joint_data_map

Vector = om2.MVector
Quaternion = om2.MQuaternion
Matrix = om2.MMatrix
Angle = om2.MAngle



# since names have type ANSICHAR(signed char) - using cp1251(or 'ASCII'?)
def util_bytes_to_str(in_bytes):
    return in_bytes.rstrip(b'\x00').decode(encoding='cp1252', errors='replace')


class PSA_Joint(object):
    def __init__(self, joint):
        self.name = joint
        self.default_translate = [0,0,0]
        self.default_rotate = [0,0,0]


class ChunkData(object):
    def __init__(self):
        self.chunk_id = None
        self.chunk_type = None
        self.chunk_datasize = None
        self.chunk_datacount = None
        self.chunk_data = None

    @classmethod
    def read(cls, fd):
        cd = cls()
        cd.chunk_id, cd.chunk_type, cd.chunk_datasize, cd.chunk_datacount = unpack('20s3i', fd.read(32))
        cd.chunk_data = fd.read(cd.chunk_datacount * cd.chunk_datasize)
        return cd


class PSA_Joint_Map(object):
    def __init__(self):
        self.joint_count = None
        self.psa_bones = {}
        self.PsaBonesToProcess = []
        self.BoneNotFoundList = []

class PSA_Anim(object):
    def __init__(self):
        self.Raw_Key_Nums = None
        self.Action_List = []

class PSA_Keyframes(object):
    def __init__(self):
        self.Raw_Key_List = None

class PSA_Reader(object):
    FILE_HEADER =  b'ANIMHEAD\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    @classmethod
    def is_header_valid(cls, chunk_data):
        """Return True if chunk_id is a valid psa (file_ext) 'magic number'."""
        if chunk_data.chunk_id != cls.FILE_HEADER:
            return False
        return True


    file_ext = 'psa'

    def __init__(self, psaPath, jointData, first_frame=11, easin_frames=10, translate_value_multiplier=100):
        self.first_frame = first_frame
        self.easin_frames = easin_frames
        self.filePath = psaPath
        self.jointData = jointData
        self.translate_value_multiplier = translate_value_multiplier

        self.joints = self.jointData.keys()

        self.fd = open(self.filePath,"rb")



    def read_psa(self):
        header = self.read_header()
        joint_map = self.read_joints()
        anim_map = self.read_anim()
        keyframe_map = self.read_key_frames()
        self.fd.close()
        self.import_keys(joint_map, anim_map, keyframe_map)

    @timeIt("prefix = apply key frames: ")
    def import_keys(self, jm, am, km):
        raw_key_index = 0
        gen_name_part = self.filePath.namebase

        for counter, (action_name, group_name, total_bones, num_raw_frames) in enumerate(am.Action_List):
            print counter, action_name, group_name, total_bones, num_raw_frames

            if group_name != 'None':
                action_name = "(%s) %s" % (group_name, action_name)
            action_name = "(%s) %s" % (gen_name_part, action_name)

            # force print usefull information to console(due to possible long execution)
            print("Action {0:>3d}/{1:<3d} frames: {2:>4d}  name: {3}".format(
                counter + 1, len(am.Action_List), num_raw_frames, action_name)
            )

            maxframes = 99999999

            # create all fcurves(for all bones) for an action
            for psa_bone in jm.PsaBonesToProcess:
                if psa_bone is None:
                    continue

                joint = psa_bone.name

                default_frame = self.first_frame - self.easin_frames

                mc.setKeyframe(joint, t=default_frame, at='rx')
                mc.setKeyframe(joint, t=default_frame, at='ry')
                mc.setKeyframe(joint, t=default_frame, at='rz')

                mc.setKeyframe(joint, t=default_frame, at='tx')
                mc.setKeyframe(joint, t=default_frame, at='ty')
                mc.setKeyframe(joint, t=default_frame, at='tz')

                psa_bone.default_translate = mc.getAttr(joint+".translate")[0]
                psa_bone.default_rotate = mc.getAttr(joint+".rotate")[0]


            for i in range(0, min(maxframes, num_raw_frames)):
                # raw_key_index+= total_bones * 5 #55
                for j in range(total_bones):
                    if j in jm.BoneNotFoundList:
                        raw_key_index += 1
                        continue

                    psa_bone = jm.PsaBonesToProcess[j]
                    # pose_bone = psa_bone.pose_bone

                    joint = psa_bone.name

                    p_pos = km.Raw_Key_List[raw_key_index][0]


                    p_quat = km.Raw_Key_List[raw_key_index][1]

                    quat = Quaternion(p_quat).conjugate()
                    rotate = quat.asEulerRotation()

                    x, y, z = rotate.x, rotate.y, rotate.z

                    rotX, rotY, rotZ = Angle(x).asDegrees(), Angle(y).asDegrees(), Angle(z).asDegrees()

                    currFrame = i+self.first_frame
                    isRoot = False
                    # check if it's root joint. if so, apply translation
                    parent = mc.listRelatives(joint,p=1,f=1)
                    if not parent or mc.nodeType(parent[0]) != "joint":
                        isRoot = True

                    # if not parent or mc.nodeType(parent[0]) != "joint":
                    multiplier = self.translate_value_multiplier
                    if isRoot:
                        # ignore rotation for root.

                        t = [0,0,0]
                        t[0] = p_pos[0] * multiplier
                        t[1] = p_pos[2] * multiplier
                        t[2] = p_pos[1] * -1 * multiplier
                        # p_pos = t

                        mc.setKeyframe(joint, t=currFrame, v=t[0], at='tx')
                        mc.setKeyframe(joint, t=currFrame, v=t[1], at='ty')
                        mc.setKeyframe(joint, t=currFrame, v=t[2], at='tz')

                    if not isRoot:
                        t = [0,0,0]
                        t[0] = p_pos[0] * multiplier
                        t[1] = p_pos[1] * multiplier
                        t[2] = p_pos[2] * multiplier

                        mc.setKeyframe(joint, t=currFrame, v=t[0], at='tx')
                        mc.setKeyframe(joint, t=currFrame, v=t[1], at='ty')
                        mc.setKeyframe(joint, t=currFrame, v=t[2], at='tz')


                        mc.setKeyframe(joint, t=currFrame, v=rotX, at='rx')
                        mc.setKeyframe(joint, t=currFrame, v=rotY, at='ry')
                        mc.setKeyframe(joint, t=currFrame, v=rotZ, at='rz')

                    raw_key_index += 1


            # apply post processing
            for psa_bone in jm.PsaBonesToProcess:
                if psa_bone:
                    joint = psa_bone.name

                    # apply euler filter
                    attrs = ["rx","ry","rz"]
                    curves = []
                    for attr in attrs:
                        conns = mc.listConnections(joint+"."+attr,s=1,d=0)
                        animCurve = next((each for each in conns if "animCurve" in mc.nodeType(each)), None)
                        if animCurve:
                            curves.append(animCurve)
                    if curves:
                        mc.filterCurve(*curves)

            raw_key_index += (num_raw_frames - min(maxframes, num_raw_frames)) * total_bones

    @timeIt("prefix = read header time: ")
    def read_header(self):
        chunkData = ChunkData.read(self.fd)
        if not self.is_header_valid(chunkData):
            raise ValueError("HEADER ERROR")
        return chunkData

    @timeIt("prefix = read joints time: ")
    def read_joints(self):
        skeleton_bones_lowered = {}
        for bone_name in self.joints:
            skeleton_bones_lowered[bone_name.lower()] = bone_name

        data = ChunkData.read(self.fd)
        joint_count = data.chunk_datacount
        psa_bones = {}
        PsaBonesToProcess = [None] * joint_count
        BoneNotFoundList = []

        for idx in range(joint_count):
            (indata) = unpack_from('64s56x', data.chunk_data, data.chunk_datasize * idx)
            in_name = util_bytes_to_str(indata[0])

            in_name_lowered = in_name.lower()
            if in_name_lowered in skeleton_bones_lowered:
                orig_name = skeleton_bones_lowered[in_name_lowered]

                obj = PSA_Joint(orig_name)
                PsaBonesToProcess[idx] = obj
                psa_bones[orig_name] = obj
            else:
                BoneNotFoundList.append(idx)

        jd = PSA_Joint_Map()
        jd.joint_count = joint_count
        jd.psa_bones = psa_bones
        jd.PsaBonesToProcess = PsaBonesToProcess
        jd.BoneNotFoundList = BoneNotFoundList
        return jd

    @timeIt("prefix = read anim time: ")
    def read_anim(self):
        data = ChunkData.read(self.fd)
        Raw_Key_Nums = 0
        Action_List = [None] * data.chunk_datacount

        for counter in range(data.chunk_datacount):
            (action_name_raw,  # 0
             group_name_raw,  # 1
             total_bones,  # 2
             RootInclude,  # 3
             KeyCompressionStyle,  # 4
             KeyQuotum,  # 5
             KeyReduction,  # 6
             TrackTime,  # 7
             AnimRate,  # 8
             StartBone,  # 9
             FirstRawFrame,  # 10
             num_raw_frames  # 11
             ) = unpack_from('64s64s4i3f3i', data.chunk_data, data.chunk_datasize * counter)

            action_name = util_bytes_to_str(action_name_raw)
            group_name = util_bytes_to_str(group_name_raw)

            Raw_Key_Nums += total_bones * num_raw_frames
            Action_List[counter] = (action_name, group_name, total_bones, num_raw_frames)

        ad = PSA_Anim()
        ad.Raw_Key_Nums=Raw_Key_Nums
        ad.Action_List = Action_List

        return ad

    @timeIt("prefix = keyframe time: ")
    def read_key_frames(self):
        bScaleDown= True
        data = ChunkData.read(self.fd)
        Raw_Key_List = [None] * data.chunk_datacount

        unpack_data = Struct('3f4f4x').unpack_from

        for counter in range(data.chunk_datacount):
            pos = Vector()
            quat = Quaternion()

            (pos.x, pos.y, pos.z,
             quat.x, quat.y, quat.z, quat.w
             ) = unpack_data(data.chunk_data, data.chunk_datasize * counter)

            if bScaleDown:
                Raw_Key_List[counter] = (pos * 0.01, quat)
            else:
                Raw_Key_List[counter] = (pos, quat)

        km = PSA_Keyframes()
        km.Raw_Key_List = Raw_Key_List

        return km



def custom_remap_translation(translation, multiplier=100):
    t = translation
    t[0] = translation[0]
    t[1] = translation[2] * multiplier
    t[2] = translation[1] * multiplier * -1
    translation = t

    return translation


def psa_import(psa_file=None, joint_data_map=None, joints=None, first_frame=11, easin_frames=10):
    if not joint_data_map:
        joint_data_map = get_joint_data_map(joints=joints)

    psa_file = Path(psa_file)

    reader = PSA_Reader(psa_file, joint_data_map, first_frame=first_frame, easin_frames=easin_frames, translate_value_multiplier=100)
    reader.read_psa()
