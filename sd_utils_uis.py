from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

from shiboken2 import wrapInstance

from maya import OpenMayaUI as omui

import pymel.all as pm

import sd_utils
reload(sd_utils)


def get_maya_main_window():
    """
    Find the Maya main window and wrap it using shiboken2.
    :return: A QtWidget pointing to Maya main window
    """
    win = omui.MQtUtil_mainWindow()

    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr


class SDRandomXformUI(QtWidgets.QDialog):

    def __init__(self):
        if pm.window('sd_random_xform_window', query=True, exists=True):
            pm.deleteUI('sd_random_xform_window')

        ui_parent = QtWidgets.QDialog(parent=get_maya_main_window())
        ui_parent.setObjectName('sd_random_xform_window')

        super(SDRandomXformUI, self).__init__(parent=ui_parent)

        self.sd = sd_utils

        self.interpolation_dict = self.sd.SDInterpolateTransform()

        # Set the title and width of the window.
        self.setWindowTitle('Random Xform')

        # Set window width.
        self.setMinimumWidth(250)

        # Specify window flags
        flags = QtCore.Qt.Window \
                | QtCore.Qt.WindowSystemMenuHint \
                | QtCore.Qt.WindowMinimizeButtonHint \
                | QtCore.Qt.WindowCloseButtonHint \
                | QtCore.Qt.WindowMaximizeButtonHint

        # Set window flags.
        self.setWindowFlags(flags)

        self.build_ui()

        self.show()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        rotation_layout_widget = QtWidgets.QWidget()
        rotation_layout_box = QtWidgets.QGridLayout(rotation_layout_widget)
        rotation_layout_box.setMargin(0)
        layout.addWidget(rotation_layout_widget)

        x_rot_label = QtWidgets.QLabel('X Rotation')
        rotation_layout_box.addWidget(x_rot_label, 0, 0)

        y_rot_label = QtWidgets.QLabel('Y Rotation')
        rotation_layout_box.addWidget(y_rot_label, 0, 1)

        z_rot_label = QtWidgets.QLabel('Z Rotation')
        rotation_layout_box.addWidget(z_rot_label, 0, 2)

        self.x_rot_box = QtWidgets.QLineEdit()
        rotation_layout_box.addWidget(self.x_rot_box, 1, 0)

        self.y_rot_box = QtWidgets.QLineEdit()
        rotation_layout_box.addWidget(self.y_rot_box, 1, 1)

        self.z_rot_box = QtWidgets.QLineEdit()
        rotation_layout_box.addWidget(self.z_rot_box, 1, 2)

        x_tr_label = QtWidgets.QLabel('X Translate')
        rotation_layout_box.addWidget(x_tr_label, 2, 0)

        y_tr_label = QtWidgets.QLabel('Y Translate')
        rotation_layout_box.addWidget(y_tr_label, 2, 1)

        z_tr_label = QtWidgets.QLabel('Z Translate')
        rotation_layout_box.addWidget(z_tr_label, 2, 2)

        self.x_tr_box = QtWidgets.QLineEdit()
        rotation_layout_box.addWidget(self.x_tr_box, 3, 0)

        self.y_tr_box = QtWidgets.QLineEdit()
        rotation_layout_box.addWidget(self.y_tr_box, 3, 1)

        self.z_tr_box = QtWidgets.QLineEdit()
        rotation_layout_box.addWidget(self.z_tr_box, 3, 2)

        randomize_btn = QtWidgets.QPushButton()
        randomize_btn.setText('Randomize')
        randomize_btn.clicked.connect(self.randomize)
        randomize_btn.clicked.connect(self.build_sd_interpolation)
        rotation_layout_box.addWidget(randomize_btn, 4, 1)

        self.interpolate_slider = QtWidgets.QSlider()
        self.interpolate_slider.setOrientation(QtCore.Qt.Orientation(1))
        self.interpolate_slider.setMinimum(0)
        self.interpolate_slider.setMaximum(100)
        self.interpolate_slider.setValue(100)
        self.interpolate_slider.valueChanged.connect(self.run_interpolation)
        layout.addWidget(self.interpolate_slider)

    def randomize(self):
        x_rot = self.check_and_make_float(self.x_rot_box.text())
        y_rot = self.check_and_make_float(self.y_rot_box.text())
        z_rot = self.check_and_make_float(self.z_rot_box.text())

        z_tras = self.check_and_make_float(self.z_tr_box.text())

        self.sd.SDRandomXform(x_rot, y_rot, z_rot, z_tras)

    def check_and_make_float(self, value):
        if not value:
            return 0
        try:
            return float(value)
        except ValueError:
            raise ValueError('values must be numbers')

    def build_sd_interpolation(self):
        self.interpolation_dict = self.sd.SDInterpolateTransform()

    def run_interpolation(self):
        prc = self.interpolate_slider.value()
        self.interpolation_dict.interpolate_transform(percentage=prc)