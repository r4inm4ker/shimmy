from collections import OrderedDict
import maya.cmds as mc

from shimmy.maya.lib import getShortName, getParent, getChildren


class JointData(object):
    def __init__(self):
        self.name = None
        self.parent = None
        self.children = []

    def __eq__(self, other):
        if isinstance(other, JointData):
            return self.name == other.name
        else:
            return self.name == getShortName(other)

    def serialize(self):
        dt = OrderedDict()
        dt['name'] = self.name
        if self.parent:
            dt['parent'] = self.parent.name
        else:
            dt['parent'] = None
        dt['children'] = [each.name for each in self.children]
        return dt


def get_joint_data_map(joints=None):
    joints = joints or mc.ls(sl=1)

    joints = mc.ls(joints, dag=1, ni=1, type="joint")

    joint_data_map = {}

    for jnt in joints:
        jdata = joint_data_map.get(jnt)
        if not jdata:
            jdata = JointData()
            jdata.name = jnt
            joint_data_map[jnt] = jdata

        parJnt = getParent(jnt)
        if parJnt:
            pjdata = joint_data_map.get(parJnt)
            if not pjdata:
                pjdata = JointData()
                pjdata.name = parJnt
                joint_data_map[parJnt] = pjdata

            jdata.parent = pjdata
            if jdata not in pjdata.children:
                pjdata.children.append(jdata)

        childrenJnt = getChildren(jnt)
        if childrenJnt:
            for cjnt in childrenJnt:
                cjdata = joint_data_map.get(cjnt)
                if not cjdata:
                    cjdata = JointData()
                    cjdata.name = cjnt
                    joint_data_map[cjnt] = cjdata
                cjdata.parent = jdata
                if not cjdata in jdata.children:
                    jdata.children.append(cjdata)

    return joint_data_map
