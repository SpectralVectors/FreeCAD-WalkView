"""
WalkTrough navigation macro for FreeCAD Perspective view by 747Developments
"""

__author__ = "Radek Reznicek - 747Developments, Spectral Vectors"
__copyright__ = "Copyright 2021, 747Developments, 2025 Spectral Vectors"
__license__ = "GPL"
__email__ = "support@747developments.com"
__version__ = "1.2"

from math import sin, cos, pi, atan
import time

import FreeCAD
import WorkingPlane
from PySide import QtGui, QtCore
from pivy import coin

## INPUTS
DEFAULT_WALK_SPEED_MM = 100.0  # camera moves default speed by keypress
DEFAULT_WALK_SPEED_INCREMENT = 10.0  # speed increment

DEFAULT_MOUSE_SPEED = 50
DEFAULT_MOUSE_SPEED_INCREMENT = 5
MOUSE_SPEED_DIVIDER = 10000

DEFAULT_AZIMUTH_INCREMENT_DEG = 1
DEFAULT_ELEVATION_INCREMENT_DEG = 1

DEG2RAD = pi / 180.0
RAD2DEG = 180.0 / pi


## WalkView CLASS
class WalkView(QtGui.QDialog):

    ## Init Class
    def __init__(self, view):
        super(WalkView, self).__init__()
        self.view = view
        self.camera = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
        self.shut_down_flag = False

        # Get actual camera position
        camera_position = self.camera.position.getValue()

        # Assign actual camera position
        self.x = camera_position[0]
        self.y = camera_position[1]
        self.z = camera_position[2]
        self.view_vector = Gui.ActiveDocument.ActiveView.getViewDirection()

        # Set default values
        self.walk_speed_mm = DEFAULT_WALK_SPEED_MM
        self.walk_speed_increment = DEFAULT_WALK_SPEED_INCREMENT
        self.mouse_speed = DEFAULT_MOUSE_SPEED
        self.mouse_speed_increment = DEFAULT_MOUSE_SPEED_INCREMENT
        self.azimuth_increment = DEFAULT_AZIMUTH_INCREMENT_DEG
        self.elevation_increment = DEFAULT_ELEVATION_INCREMENT_DEG

        self.azimuth = 0.0
        self.elevation = 0.0
        if self.view_vector[0] != 0:
            self.azimuth = atan(self.view_vector[1] / self.view_vector[0])
        if self.view_vector[1] != 0:
            self.elevation = atan(self.view_vector[2] / self.view_vector[1])
        self.d_az_init = 0.0
        self.d_el_init = 0.0
        self.d_az = 0.0
        self.d_el = 0.0

        self.pressed_keys = []

        # Create mouse and keyboard event callbacks
        self.mouseEvent = self.view.addEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(),
            self.updateMouseMotion,
        )
        self.keyEvent = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(),
            self.updateKeyPressMotion,
        )

    ## Update view by mouse motion callback
    def updateMouseMotion(self, mouseEvent):
        try:
            event = mouseEvent.getEvent()
            if event.getTypeId() == coin.SoLocation2Event.getClassTypeId():

                pos = event.getPosition()
                self.d_az = int(pos[0])
                self.d_el = int(pos[1])

                self.azimuth += (self.d_az_init - self.d_az) * (
                    self.mouse_speed / MOUSE_SPEED_DIVIDER
                )
                self.elevation += (self.d_el_init - self.d_el) * (
                    self.mouse_speed / MOUSE_SPEED_DIVIDER
                )
                print(self.elevation)

                self.d_az_init = self.d_az
                self.d_el_init = self.d_el

                self.updateViewVector()

            # # If mouse motion is FROZEN only update the camera position
            # else:
            #     # Assign actual camera position
            #     self.camera_position = self.camera.position.getValue()
            #     self.x = self.camera_position[0]
            #     self.y = self.camera_position[1]
            #     self.z = self.camera_position[2]

        except Exception as ex:
            print("Exception happened during mouse motion update: %s" % (ex))

    ## Function to update the view vector
    def updateViewVector(self):
        self.camera_position = self.camera.position.getValue()
        self.view_vector = (
            self.camera_position[0] + cos(self.azimuth),
            self.camera_position[1] + sin(self.azimuth),
            self.camera_position[2] + sin(self.elevation),
        )

        self.camera.pointAt(
            coin.SbVec3f(
                self.view_vector[0],
                self.view_vector[1],
                self.view_vector[2],
            ),
            coin.SbVec3f(0, 0, 1),
        )
        FreeCADGui.getMainWindow().statusBar().showMessage(
            f"W: Forward, S: Backward, A: Left, D: Right, Speed: {self.walk_speed_mm}"
        )

    ## Function to update azimuth
    def updateAz(self, value, increment, positive_incr):
        value_deg = value * RAD2DEG
        value_deg = value_deg % 360
        if positive_incr:
            new_value = value_deg + increment
        else:
            new_value = value_deg - increment
        return new_value * DEG2RAD

    ## Function to update elevation
    def updateEl(self, value, increment, positive_incr):
        value_deg = value * RAD2DEG
        value_mod = value_deg % 360
        if positive_incr:
            new_value = value_deg + increment
        else:
            new_value = value_deg - increment
        if new_value < 90 or new_value > 270:
            new_value = value_mod
        return new_value * DEG2RAD

    ## Hande keyboard controls
    def updateKeyPressMotion(self, keyEvent):
        try:
            event = keyEvent.getEvent()

            key_pressed = event.getKey()
            key_state = event.getState()

            if key_pressed == coin.SoKeyboardEvent.ESCAPE:
                self.endWalkTrough()
                self.shut_down_flag = True

            if key_pressed == coin.SoKeyboardEvent.W:
                self.x += self.walk_speed_mm * cos(self.azimuth)
                self.y += self.walk_speed_mm * sin(self.azimuth)

                self.z += self.walk_speed_mm * sin(self.elevation)

            if key_pressed == coin.SoKeyboardEvent.S:
                self.y -= self.walk_speed_mm * sin(self.azimuth)
                self.x -= self.walk_speed_mm * cos(self.azimuth)

                self.z -= self.walk_speed_mm * sin(self.elevation)

            if key_pressed == coin.SoKeyboardEvent.A:
                self.x += self.walk_speed_mm * cos(self.azimuth + pi / 2.0)
                self.y += self.walk_speed_mm * sin(self.azimuth + pi / 2.0)

            if key_pressed == coin.SoKeyboardEvent.D:
                self.x -= self.walk_speed_mm * cos(self.azimuth + pi / 2.0)
                self.y -= self.walk_speed_mm * sin(self.azimuth + pi / 2.0)

            if key_pressed == coin.SoKeyboardEvent.Q:
                self.z -= self.walk_speed_mm

            if key_pressed == coin.SoKeyboardEvent.E:
                self.z += self.walk_speed_mm

            if key_pressed == coin.SoKeyboardEvent.R:
                self.walk_speed_mm += self.walk_speed_increment

            if key_pressed == coin.SoKeyboardEvent.F:
                self.walk_speed_mm -= self.walk_speed_increment

            if key_pressed == coin.SoKeyboardEvent.T:
                self.mouse_speed += self.mouse_speed_increment

            if key_pressed == coin.SoKeyboardEvent.G:
                self.mouse_speed -= self.mouse_speed_increment

            if key_pressed == coin.SoKeyboardEvent.V:
                self.fitObjectToWindow()
                time.sleep(0.3)

            pos = event.getPosition()
            self.d_az = int(pos[0])
            self.d_el = int(pos[1])
            self.d_az_init = self.d_az
            self.d_el_init = self.d_el

            # adjust new X, Y,Z values
            if key_pressed != coin.SoKeyboardEvent.X:
                self.camera.position.setValue(
                    (
                        self.x,
                        self.y,
                        self.z,
                    )
                )
            # time.sleep(0.01) # delays for 10 ms
        except Exception as ex:
            print("Exception happened during key press: %s" % (ex))

    ## Function to fit the all objects to window (The same as: View -> Standard views -> Fit All)
    def fitObjectToWindow(self):
        try:
            Gui.SendMsgToActiveView("ViewFit")
        except Exception as ex:
            print("Exception happened during fitObjectToWindow: %s" % (ex))

    ## Function to change current speed of movement
    def changeSpeed(self, text):
        try:
            new_speed = float(text)
            self.walk_speed_mm = new_speed
            print("New speed: %.3f mm/keypress" % (new_speed))
        except Exception as ex:
            print("Exception happened during changeSpeed: %s" % (ex))

    ## Function to change speed increment
    def changeSpeedIncrement(self, text):
        try:
            new_speed_increment = float(text)
            self.walk_speed_increment = new_speed_increment
            print("New speed increment: %.3f mm/keypress" % (new_speed_increment))
        except Exception as ex:
            print("Exception happened during changeSpeedIncrement: %s" % (ex))

    ## Function to change speed of moue movement
    def changeMouseSpeed(self, text):
        try:
            new_speed = float(text)
            self.mouse_speed = new_speed
            print("New mouse speed: %.3f" % (new_speed))
        except Exception as ex:
            print("Exception happened during changeMouseSpeed: %s" % (ex))

    ## Function to change mouse speed increment
    def changeMouseSpeedIncrement(self, text):
        try:
            new_speed_increment = float(text)
            self.mouse_speed_increment = new_speed_increment
            print("New mouse speed increment: %.3f mm/keypress" % (new_speed_increment))
        except Exception as ex:
            print("Exception happened during changeSpeedIncrement: %s" % (ex))

    ## Function to change azimuth increment
    def changeAzIncrement(self, text):
        try:
            new_increment = float(text)
            self.azimuth_increment = new_increment
            print("New azimuth increment: %.1f" % (new_increment))
        except Exception as ex:
            print("Exception happened during changeAzIncrement: %s" % (ex))

    ## Function to change elevation increment
    def changeElIncrement(self, text):
        try:
            new_increment = float(text)
            self.elevation_increment = new_increment
            print("New elevation increment: %.1f" % (new_increment))
        except Exception as ex:
            print("Exception happened during changeElIncrement: %s" % (ex))

    ## Quit WalkTrough navigation
    def endWalkTrough(self):
        try:
            print("Remove event callbacks")
            self.view.removeEventCallbackPivy(
                coin.SoLocation2Event.getClassTypeId(),
                self.mouseEvent,
            )
            self.view.removeEventCallbackPivy(
                coin.SoKeyboardEvent.getClassTypeId(),
                self.keyEvent,
            )
            print("Setting Orthographic view")
            Gui.ActiveDocument.ActiveView.setCameraType("Orthographic")
            # print("Setting ViewFit to all object to screen")
            # Gui.SendMsgToActiveView("ViewFit")
            FreeCADGui.getMainWindow().statusBar().clearMessage()
            closeMessage()
            self.close()
        except Exception as ex:
            print("Exception happened during EXIT: %s" % (ex))
        return


## Opening message
def openMessage():
    print("<<< Walk View Start >>>")


## Closing message
def closeMessage():
    print("<<< Walk View End >>>")


## Main task
def main():

    openMessage()
    flag_open_view = True

    try:
        # CLEAR WINDOWS and console
        mw = Gui.getMainWindow()

        r = mw.findChild(QtGui.QTextEdit, "Report view")
        r.clear()
    except Exception as ex:
        print("Exception happened console clearing: %s" % (ex))
        flag_open_view = False
        closeMessage()
        return

    try:
        # GET active view
        actView = Gui.ActiveDocument.ActiveView
    except Exception as ex:
        print("Unable get ACTIVE VIEW - Make sure you have document opened: %s" % (ex))
        flag_open_view = False
        closeMessage()
        return

    try:
        print("Setting TOP working plane X-Y")
        wp = WorkingPlane.get_working_plane()
        wp.set_to_top()
        # sFreeCADGui.Snapper.setGrid()
    except Exception as ex:
        print("Unable to set Top X-Y working plane: %s" % (ex))
        flag_open_view = False
        closeMessage()
        return

    try:
        # Set view to perspective mode
        print("Setting Perspective view")
        Gui.ActiveDocument.ActiveView.setCameraType("Perspective")  # MUST be in perspective mode
    except Exception as ex:
        print("Unable to set Perspective mode: %s" % (ex))
        flag_open_view = False
        closeMessage()
        return

    if flag_open_view:
        # Start the walktrough navigation
        print("Starting Walktrough view")
        walktroughNav = WalkView(actView)
        # mw.menuBar().setEnabled(False)
        pick_style = coin.SoPickStyle()
        pick_style.style.setValue(coin.SoPickStyle.UNPICKABLE)

    else:
        closeMessage()
        return


if __name__ == "__main__":

    main()
