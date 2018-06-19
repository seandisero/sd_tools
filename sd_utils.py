"""
Utility functions created by: Sean Disero
"""
import pymel.all as pm
import maya.mel as mm
from maya import OpenMaya as om

import random
import os
import sys
import platform

from pprint import pprint

import sd_decorators as sdd
reload(sdd)


SCENE_PATH = pm.sceneName()


def _if_mesh_move_up(sel):
    """
    Checks to see if selection is a mesh object, if it is it will select its transform.
    :param sel: The object in question.
    :return: Transform
    """
    if sel.type() == 'mesh':
        obj = pm.listRelatives(sel, parent=True)[0]
    else:
        obj = sel

    return obj


def _is_group(sel):
    """
    determine if a group is selected or if its a bunch of transforms.
    :param sel: the selection objects.
    :return: new list made up by the children of the selected group, or the original
    selection if selection is not a group.
    """
    new_selection = [
        _if_mesh_move_up(o) for o in pm.listRelatives(sel, children=True)
        if o.type() == 'transform' or 'mesh'
    ]

    return new_selection


def sd_test_type(selection, target_types):
    for obj in selection:
        if type(obj) in target_types:
            return None
        else:
            raise TypeError('Wrong type selected.')


@sdd.sd_preserve_selection
def sd_weight_flat_surface(selection, obj_select=True, min_tolerance=0, max_tolerance=0):
    """
    if obj_select = True, hard surfaces (perfectly flat) will automatically be
    found and corrected, but only if model properly finished.
    min_tolerance = the minimum angle that will be selected.
    max_tolerance = the maximum angle that will be selected.
    """

    sd_test_type(selection, [pm.Transform, pm.MeshFace])

    if obj_select:
        # convert selection to edges
        mm.eval('ConvertSelectionToEdges;')

        # constrain the selection to a specific angle
        pm.polySelectConstraint(
            mode=3,
            type=0x8000,
            angle=True,
            anglebound=(min_tolerance, max_tolerance)
        )

        # save the selection
        oSel = pm.ls(sl=True, flatten=True)

        # turn off polySelectConstraint
        pm.polySelectConstraint(mode=0)

        # make sure its selected (just in case)
        pm.select(oSel)

        # convert to faces
        mm.eval('ConvertSelectionToFaces;')

    fSel = pm.ls(sl=True, flatten=True)

    # create a good ol' progress bar
    progWind = pm.window(title='progress')
    pm.columnLayout()

    progressControl = pm.progressBar(maxValue=len(fSel), width=300)

    pm.showWindow(progWind)

    # run through each object and get the face normal of each face
    # apply the face normal direction to the connected verts
    for face in fSel:
        pm.select(face)
        face_normal = face.getNormal(space='world')
        verts = pm.polyListComponentConversion(
            face,
            fromFace=True,
            toVertex=True
        )

        pm.select(verts)
        pm.polyNormalPerVertex(normalXYZ=face_normal)

        ff = fSel.index(face)
        pm.progressBar(progressControl, edit=True, progress=ff)

    pm.deleteUI(progWind)


def sd_get_comp_info():
    lines = []
    lines.append('Scene Info')
    lines.append('  Maya Scene:  ' + pm.sceneName())

    # Maya and Python versions
    lines.append('Maya/Python Info')
    lines.append('  Maya Version:  ' + pm.about(version=True))
    lines.append('  Qt Version:  ' + pm.about(qtVersion=True))
    lines.append('  Maya64:  ' + str(pm.about(is64=True)))
    lines.append('  PyVersion:  ' + sys.version)
    lines.append('  PyExe:  ' + sys.executable)

    # Information about the machine and OS.
    lines.append('Machine Info')
    lines.append('  OS:  ' + pm.about(os=True))
    lines.append('  Node:  ' + platform.node())
    lines.append('  OSRelease:  ' + platform.release())
    lines.append('  OSVersion:  ' + platform.version())
    lines.append('  Machine:  ' + platform.machine())
    lines.append('  Processor:  ' + platform.processor())

    # Information on the user's environment.
    lines.append('Environment Info')
    lines.append('  EnvVars')
    for k in sorted(os.environ.keys()):
        lines.append('  %s:  %s' % (k, os.environ[k]))
    lines.append('  SysPath')
    for p in sys.path:
        lines.append('    ' + p)
    return lines


def sd_setworkspace():
    scene_path_list = SCENE_PATH.split('/')
    new_path = SCENE_PATH
    new_path_list = scene_path_list
    set_workspace = '/workspace.mel'

    def _refactor_lists(a, b):
        a = a.replace('/' + b[-1], '')
        b.remove(b[-1])
        return a, b

    while not os.path.isfile(new_path + set_workspace):
        # print 'its not here'
        new_path, new_path_list = _refactor_lists(new_path, new_path_list)
    if os.path.isfile(new_path + set_workspace):
        # print 'its here'
        mm.eval('setProject "{}"'.format(new_path + '/'))


def sd_list_attr():
    o_sel = pm.ls(sl=True)

    for obj in o_sel:
        attr_list = pm.listAttr()

        for attr in attr_list:

            try:
                val = pm.getAttr('{}.{}'.format(obj, attr))
                print attr, val
            except AttributeError:
                continue


def make_random_float(value, negative=True):
    if negative:
        negative_value = -value
    else:
        negative_value = 0

    if value == 0:
        return 0
    else:
        return random.uniform(negative_value, value)


def sd_move_to_origin(obj):
    old_pivot = obj.getPivots(worldSpace=True)[0]
    obj.setTranslation(old_pivot * -1)
    return old_pivot


def sd_export_from_origin(obj):
    old_position = sd_move_to_origin(obj)
    mm.eval('ExportSelection;')
    obj.setTranslation((0, 0, 0))
    return old_position


def sd_randomize_uvs(rand=0.3):
    """
    After selecting uv's in the uv editor, this script will move
    around uv's randomly according to the object with which they belong.
    :param rand: The distance to be moved randomized between -rand and rand.
    :return: None
    """
    # Check if rand is a float or integer.
    if isinstance(rand, basestring):
        raise ValueError('please input a float or integer value')

    # define selection.
    o_sel = pm.ls(sl=True, flatten=True)

    # Check if there are any objects in the selection that are not MeshUVs.
    non_mesh_uv_objects = [o for o in o_sel if not isinstance(o, pm.MeshUV)]
    if non_mesh_uv_objects:
        raise TypeError('please only select uv points')

    # List the objects that the UVs belong to.
    u_list = [o.name().split('.')[0] for o in o_sel]

    # Create a Dictionary containing the objects and the UV vertices selected.
    uv_coord_dict = {
        o: [
            u.index() for u in o_sel if o == u.name().split('.')[0]
        ] for o in u_list
    }

    # Create random numbers relating to the objects selected.
    random_nums = {
        o: [
            random.uniform(-rand, rand),
            random.uniform(-rand, rand)
        ] for o in u_list
    }

    # Cycle through the dictionary moving the object's contained UV vertices.
    for uv in uv_coord_dict:
        for vtx in uv_coord_dict[uv]:
            pm.polyEditUV(
                '{}.map[{}]'.format(uv, vtx),
                u=random_nums[uv][0],
                v=random_nums[uv][1],
                relative=True
            )

    return None


def sd_find_dir():
    target_dir = pm.fileDialog2(fileMode=2)
    return target_dir


def get_direction(transform1, transform2):
    transform1_position = transform1.getPivots(worldSpace=True)[0]
    transform1_position = transform2.getPivots(worldSpace=True)[0]
    direction = transform1_position+transform1_position
    return direction


def transform_in_direction():
    pass


# Still in production.
def sd_explode(selection, distance):
    """
    -orgonize groups
    -get positions of key groups
    -normolize longest distence
    -move along AB--> direction according to explode distance
    :return:
    """
    print selection
    print distance

    def get_children_lists(sel, dist):
        if not sel:
            return
        selection_list = []
        for o in sel:
            ch = pm.listRelatives(o, children=True)
            [selection_list.append(o) for o in ch if type(o) == pm.Transform]
        # pprint(selection_list)
        # pprint(dist)
        get_children_lists(selection_list, (dist * 0.5))

    get_children_lists(selection, distance)


class SDInterpolateTransform(object):

    def __init__(self):
        self.o_sel = pm.ls(sl=True)

        self.attr_list = [
            'translateX',
            'translateY',
            'translateZ',
            'rotateX',
            'rotateY',
            'rotateZ',
        ]

        self.attr_dict = self.make_attr_dict()

    def make_attr_dict(self):
        object_dict = {k: k for k in self.o_sel}
        for obj in object_dict:
            object_dict[obj] = [[a, obj.getAttr(a)] for a in self.attr_list]

        return object_dict

    def interpolate_transform(self, percentage):
        prcnt = percentage * 0.01
        for obj in self.attr_dict:
            o = self.attr_dict[obj]
            for a in o:
                val = a[1]
                val = val * prcnt
                obj.setAttr('{}'.format(a[0]), val)


class SDRandomXform(object):
    """
    Randomly rotates an object acording to x, y, and/or z.
    In order for function to perform in a expected manner
    the transforms must be frozen.
    """

    def __init__(self, rx=0, ry=0, rz=0, tz=0, negative_values=True):

        self.o_sel = pm.ls(sl=True, flatten=True)

        self.x_rot = rx
        self.y_rot = ry
        self.z_rot = rz

        self.z_tr = tz

        self.random_rotation_x(self.o_sel, self.x_rot, negative_values)
        self.random_rotation_y(self.o_sel, self.y_rot, negative_values)
        self.random_rotation_z(self.o_sel, self.z_rot, negative_values)

        self.random_translation_z(self.o_sel, self.z_tr, negative_values)

    @staticmethod
    def random_rotation_x(selection, x_val, use_negative_values=True):
        """
        Randomly rotates objects in a range of -n to n where n is the z_val.
        :param selection: List containing the selected objects or group.
        :param x_val: The n value of x to determine a range between -n and n.
        :param use_negative_values: Determines weather or not the random rotation should rotate in negative values.
        :return: None
        """
        for obj in _is_group(selection):

            if x_val == 0 or None:
                obj.setAttr('rotateX', 0)
            else:
                x_rand = make_random_float(x_val, use_negative_values)

                obj.setAttr('rotateX', x_rand)

        return None

    @staticmethod
    def random_rotation_y(selection, y_val, use_negative_values=True):
        """
        Randomly rotates objects in a range of -n to n where n is the y_val.
        :param selection: list containing the selected objects or group.
        :param y_val: the n value of y to determine a range between -n and n.
        :return: None
        """
        for obj in _is_group(selection):

            if y_val == 0:
                obj.setAttr('rotateY', y_val)
            else:
                y_rand = make_random_float(y_val, use_negative_values)

                obj.setAttr('rotateY', y_rand)

        return None

    @staticmethod
    def random_rotation_z(selection, z_val, use_negative_values=True):
        """
        Randomly rotates objects in a range of -n to n where n is the z_val.
        :param selection: list containing the selected objects or group.
        :param z_val: the n value of z to determine a range between -n and n.
        :return: None
        """
        for obj in _is_group(selection):

            if z_val == 0:
                obj.setAttr('rotateZ', z_val)
            else:
                z_rand = make_random_float(z_val, use_negative_values)

                obj.setAttr('rotateZ', z_rand)

        return None

    @staticmethod
    def random_translation_z(selection, z_val, use_negative_values=True):
        """
        Randomly rotates objects in a range of -n to n where n is the z_val.
        :param selection: list containing the selected objects or group.
        :param z_val: the n value of z to determine a range between -n and n.
        :return: None
        """
        for obj in _is_group(selection):

            if z_val == 0:
                obj.setAttr('translateZ', z_val)
            else:
                z_rand = make_random_float(z_val, use_negative_values)

                obj.setAttr('translateZ', z_rand)

        return None


class SDRandomOffset(object):

    def __init__(self, x=0, y=0, z=0):
        self.o_sel = pm.ls(sl=True, flatten=True)

        self.x_val = x
        self.y_val = y
        self.z_val = z

        self.sd_random_y_offset(self.o_sel, self.y_val)

    @staticmethod
    def sd_random_y_offset(selection, y_value, both_directions=True):
        """
        Randomly offsets objects in the range of -n to n where n is the y_value if both_directions is True
        :param selection: The current selection.
        :param y_value: -n to n where n is y_value
        :param both_directions: clamps the range to 0 to n where n is y_value
        :return: None
        """
        # for obj in _is_group(selection):
        for obj in selection:
            pm.select(obj)

            if y_value == 0:
                y_random = 0
            else:
                y_random = random.uniform(-y_value, y_value)

            if not both_directions:
                y_random = abs(y_random)

            if type(obj) == pm.MeshVertex:
                pm.setAttr('{}.pnty'.format(obj), y_random)
            else:
                obj.setAttr('translateY', y_random)

        pm.select(selection)
        return None


class SDTransferAttrs(object):

    def __init__(self):
        self.o_sel = pm.ls(sl=True)

        self.sd_transfer_attributes(self.o_sel)

    def sd_transfer_attributes(self, selection):

        new_sel = selection.pop(0)

        for obj in selection:
            transfer_from = [new_sel, obj]

            pm.select(transfer_from)

            pm.transferAttributes(
                transferPositions=0,
                transferNormals=0,
                transferUVs=1,
                sourceUvSet="tiling",
                targetUvSet="map1",
                transferColors=0,
                sampleSpace=5,
                sourceUvSpace="tiling",
                targetUvSpace="map1",
                searchMethod=3,
                flipUVs=0,
                colorBorders=1
            )

            pm.delete(ch=True)


class SDChangeHarDriveNameForTex(object):

    def __init__(self, hard_drive=None):

        self.selection = pm.ls(sl=True)

        self.new_hardrive_name = SCENE_PATH.split('/')[0]

        if not hard_drive:
            self.sd_change_tex_path(self.selection, self.new_hardrive_name)
        else:
            self.sd_change_tex_path(self.selection, hard_drive)

    @staticmethod
    def sd_change_tex_path(selection, new_hardrive):
        for obj in selection:
            image_path = obj.getAttr('fileTextureName')
            old_hard_drive = image_path.split('/')[0]
            new_path = image_path.replace(old_hard_drive, '{}'.format(new_hardrive))
            obj.setAttr('fileTextureName', new_path)


def tf():
    print 'It worked.'

@sdd.sd_undo_chunk
def move_them(selection):
    for o in selection:
        o.setAttr('translateX', 100)
