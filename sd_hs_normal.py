"""
hard surface normal adjustment tool
created by: Sean Disero

HS_Normal_Adj is for adjusting the vtx normals on any large, hard surface object.

if a face has no edges running through it then it will need to be selected manually with object selection unchecked.

if a bevel is perfectly flat and has an edge running through it, turning it into two triangles,
    that edge should be deleted, else it could constrain the vtx normals of that edge to the bevel.

if the window is reloaded it will loose its connection to the blinn mtl if one was created.

progress bars will likely be switched to the gMainProgressBar in the future in order to cancel operations.

installation:

drag HS_Normal_Adj.py into the scripts folder C:\Users\userName\Documents\maya\mayaYear(ex.maya2017)\scripts

in maya create this Python script and place it on your shelf:

import HS_Normal_Adj
reload(HS_Normal_Adj)

License: MIT
"""

import pymel.all as pm
import maya.mel as mm
import sd_decorators as sdd


class HS_Normal:

    def __init__(self):
        self.normal_shader = None
        self.blinn_tex_warning = False

    def test_type(self, selection, target_type):
        for obj in selection:
            if type(obj) == pm.MeshFace:
                return None
            elif type(obj) == pm.Transform:
                return None
            else:
                raise TypeError('you must only select faces for this function to work')

    @sdd.sd_preserve_selection
    def connected_flat(self, obj_select=True, min_tolerance=0, max_tolerance=0):
        """
        if obj_select = True, hard surfaces (perfectly flat) will automatically be
        found and corrected, but only if model properly finished.
        min_tolerance = the minimum angle that will be selected.
        max_tolerance = the maximum angle that will be selected.
        """

        self.test_type(pm.ls(sl=True, flatten=True))

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

    def hs_verts(self, f1, f2):
        """
        this function finds the average of the face normals on each side of
        an edge then adjusts the vtx normals to that average
        """
        average_n = (f1.getNormal(space='world') + f2.getNormal(space='world')) / (2, 2, 2)

        verts1 = pm.polyListComponentConversion(
            f1,
            fromFace=True,
            toVertex=True
        )

        pm.select(verts1)
        v1 = pm.ls(sl=True, flatten=True)

        verts2 = pm.polyListComponentConversion(
            f2,
            fromFace=True,
            toVertex=True
        )

        pm.select(verts2)
        v2 = pm.ls(sl=True, flatten=True)

        sVerts = [i for i in v1 if i in v2]

        pm.select(sVerts)

        pm.polyNormalPerVertex(normalXYZ=average_n)

    def hs_tube(self, edgering=True):
        """
        used for correcting normals on the ends of a hard surface pipe.
        if edgering = True, than only one edge need be selected and it will select
        the ring automatically.
        """
        if edgering:
            mm.eval('SelectEdgeRingSp;')

        oSel = pm.ls(sl=True, flatten=True)

        for obj in oSel:

            # determine weather or not the selection is a face
            if str(obj.split('.')[-1][0]) == 'f':
                # if it is, convert it to edges
                mm.eval('ConvertSelectionToContainedEdges;')
                break

        eSel = pm.ls(sl=True, flatten=True)

        # another good ol' progress bar
        progWind = pm.window(title='progress')
        pm.columnLayout()

        progressControl = pm.progressBar(maxValue=len(eSel), width=300)

        pm.showWindow(progWind)

        # for the selected edges run the hs_verts function
        for edges in eSel:
            pm.select(edges)
            mm.eval('ConvertSelectionToFaces;')
            angled_faces = pm.ls(sl=True, flatten=True)
            self.hs_verts(angled_faces[0], angled_faces[1])

            ee = eSel.index(edges)
            pm.progressBar(progressControl, edit=True, progress=ee)

        pm.deleteUI(progWind)

        pm.selectType(edge=True)

    def vtx_normal_length(self, *args):
        oSel = pm.ls(sl=True, flatten=True)
        length = pm.floatSliderGrp(self.float3, q=True, value=True)
        for objs in oSel:
            name = objs.name()
            pm.setAttr('%s.normalSize' % name, length)

    def btn_connected_flat(self, *args):
        objSel = pm.checkBox(self.objCheck, q=True, value=True)
        minTol = pm.floatSliderGrp(self.float1, q=True, value=True)
        maxTol = pm.floatSliderGrp(self.float2, q=True, value=True)
        self.connected_flat(objSel, minTol, maxTol)

    @sdd.sd_preserve_selection
    def btn_hs_tube(self, *args):
        edgeCheck = pm.checkBox(self.tubeCheck, q=True, value=True)
        print edgeCheck
        self.hs_tube(edgeCheck)

    def create_blinn(self):
        """
        creates a blinn for observing how light interacts with the surface of an object
        """
        oSel = pm.ls(sl=True)

        self.normal_shader = pm.shadingNode('blinn', asShader=True)
        self.normal_shading_group = pm.sets(renderable=True, noSurfaceShader=True, empty=True)
        pm.connectAttr('%s.outColor' % self.normal_shader, '%s.surfaceShader' % self.normal_shading_group)
        for objs in oSel:
            pm.select(objs)
            pm.hyperShade(assign='%s' % self.normal_shader)
        pm.select(oSel)

    def btn_create_blinn(self, *args):
        self.create_blinn()

    def edit_blinn(self, *args):
        if not self.normal_shader:
            if not self.blinn_tex_warning:
                pm.displayWarning('you havent made a blinn yet you potato!')
                self.blinn_tex_warning = True
        else:
            newColour = pm.colorSliderGrp(self.blinnCol, q=True, rgbValue=True)
            pm.setAttr('%s.color' % self.normal_shader, newColour, type='double3')

    def btn_show_vtx_normals(self, *args):
        oSel = pm.ls(sl=True, flatten=True)
        for objs in oSel:
            name = objs.name()
            pm.setAttr('%s.normalType' % name, 2)
            pm.setAttr('%s.displayNormal' % name, 1)

    def btn_hide_vts_normals(self, *args):
        oSel = pm.ls(sl=True, flatten=True)
        for objs in oSel:
            name = objs.name()
            pm.setAttr('%s.normalType' % name, 2)
            pm.setAttr('%s.displayNormal' % name, 0)

    def unlockVtxN(self, *args):
        pm.polyNormalPerVertex(ufn=True)

    def showUI(self):
        """
        this is teh function that creates the ui:
        in the future it will likely change to a Qt GUI
        """
        testWindow = 'HS_Normal_Tool'

        if pm.window(testWindow, exists=True):
            pm.deleteUI(testWindow)

        pm.window(testWindow, sizeable=False)

        pm.rowColumnLayout(
            'normal_Column',
            numberOfColumns=1,
            columnWidth=(1, 300),
            columnAttach=(1, 'left', 5)
        )

        pm.rowLayout(
            'flatRow',
            parent='normal_Column',
            numberOfColumns=2
        )

        pm.button(
            label='Flat Surface',
            parent='flatRow',
            width=100,
            command=self.btn_connected_flat
        )

        self.objCheck = pm.checkBox(
            label='Object Selection',
            parent='flatRow',
            value=True
        )

        self.float1 = pm.floatSliderGrp(
            label='min_tolerance',
            parent='normal_Column',
            columnAlign=(1, 'left'),
            columnWidth=(1, 80),
            field=True
        )
        self.float2 = pm.floatSliderGrp(
            label='max_tolerance',
            parent='normal_Column',
            columnAlign=(1, 'left'),
            columnWidth=(1, 80),
            field=True
        )

        pm.separator(
            parent='normal_Column',
            height=20
        )

        pm.rowLayout(
            'curveRow',
            parent='normal_Column',
            numberOfColumns=2
        )

        pm.button(
            label='Curved Surface',
            parent='curveRow',
            width=100,
            command=self.btn_hs_tube
        )

        self.tubeCheck = pm.checkBox(
            label='Edge Ring',
            parent='curveRow',
            value=True
        )

        pm.separator(
            parent='normal_Column',
            height=20
        )

        pm.button(
            label='Unlock Selected vtx Normals',
            parent='normal_Column',
            command=self.unlockVtxN
        )

        pm.separator(
            parent='normal_Column',
            height=20
        )

        pm.checkBox(
            label='Toggle vtx Normals',
            parent='normal_Column',
            onCommand=self.btn_show_vtx_normals,
            offCommand=self.btn_hide_vts_normals
        )

        self.float3 = pm.floatSliderGrp(
            label='vtx Length',
            parent='normal_Column',
            columnWidth=(1, 55),
            field=True,
            dragCommand=self.vtx_normal_length,
        )

        pm.floatSliderGrp(
            self.float3,
            label='vtx Length',
            edit=True,
            columnWidth=(2,42),
        )

        pm.separator(
            parent='normal_Column',
            height=20
        )

        pm.rowLayout(
            'blinnRow',
            parent='normal_Column',
            numberOfColumns=2,
            columnWidth=(2, 200)
        )

        pm.button(
            label='Create Blinn',
            parent='blinnRow',
            width=100,
            command=self.btn_create_blinn
        )

        self.blinnCol = pm.colorSliderGrp(
            label='',
            parent='blinnRow',
            width=190,
            columnWidth=(1, 1),
            dragCommand=self.edit_blinn
        )

        pm.showWindow(testWindow)

        pm.window(
            testWindow,
            edit=True,
            widthHeight=(300,265)
        )


tempObj = HS_Normal()
tempObj.showUI()