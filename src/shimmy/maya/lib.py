import maya.cmds as mc


def getParent(node, fullName=False):
    parent = mc.listRelatives(node, p=1, f=1) or None

    if parent:
        if fullName:
            parent = parent[0]
        else:
            # get shortest possible unique path
            parent = mc.ls(parent)[0]

    return parent


def getTransform(node):
    if mc.ls(node, shapes=1):
        return getParent(node)
    else:
        return node


def getShape(node):
    if mc.ls(node, shapes=1):
        return node
    else:
        return mc.ls(node, dag=1, ni=1, shapes=1)[0]

def getChildren(node, fullName=False):
    children = mc.listRelatives(node, c=1, f=1) or []

    if children:
        if not fullName:
            children = mc.ls(children)

    return children


def getShortName(node):
    return str(node).split("|")[-1]
