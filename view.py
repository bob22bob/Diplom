from PyQt5 import QtWidgets, QtCore, QtGui
from pygrabber.dshow_graph import FilterGraph
import cv2
import numpy as np
import qimage2ndarray
from multipledispatch import dispatch
from tracker import *
from processing import *


# noinspection PyUnresolvedReferences
class View(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.resolution_scale = 1
        self.minimum_center_distance = 20
        self.param1 = 50
        self.param2 = 30
        self.minimum_radius = 1
        self.maximum_radius = 50
        self.tracking_distance = 25

        self.frequency = 50

        self.graph = FilterGraph()
        self.camera_thread = QtCore.QThread(self)
        self.camera_timer = QtCore.QTimer(self.camera_thread)
        self.camera_connected = False
        self.camera_only = False
        self.tracker = Tracker(self.tracking_distance)

        self.scaling_pos1 = QtCore.QPoint(0, 0)
        self.scaling_pos2 = QtCore.QPoint(0, 0)
        self.scaling_distance = 0

        try:
            self.load_from_settings()
        except Exception as e:
            print(str(e) + '(file settings incorrect)')

        self.menubar = QtWidgets.QMenuBar(self)
        self.statusbar = QtWidgets.QStatusBar(self)

        self.image_label = QtWidgets.QLabel(self)

        self.camera_list_box = QtWidgets.QComboBox(self)
        self.camera_refresh_button = QtWidgets.QPushButton(self)
        self.camera_connect_button = QtWidgets.QPushButton(self)

        self.TextLabel = QtWidgets.QLabel(self)
        self.GrayCheckBox = QtWidgets.QCheckBox(self)
        self.DP = QtWidgets.QDoubleSpinBox(self)
        self.MinDist = QtWidgets.QSpinBox(self)
        self.Param1 = QtWidgets.QSpinBox(self)
        self.Param2 = QtWidgets.QDoubleSpinBox(self)
        self.MinRadius1 = QtWidgets.QSpinBox(self)
        self.MaxRadius1 = QtWidgets.QSpinBox(self)

        self.tracking_distance_box = QtWidgets.QSpinBox(self)

        self.scaling_value_box = QtWidgets.QDoubleSpinBox(self)

        self.setup_ui()

        self.update_camera_list()

    # region Utils region
    def save_to_settings(self):
        file = open('settings.txt', 'w')
        file.write(str(self.resolution_scale) + '\n')
        file.write(str(self.minimum_center_distance) + '\n')
        file.write(str(self.param1) + '\n')
        file.write(str(self.param2) + '\n')
        file.write(str(self.minimum_radius) + '\n')
        file.write(str(self.maximum_radius) + '\n')
        file.write(str(self.tracking_distance) + '\n')
        file.close()

    def load_from_settings(self):
        file = open('settings.txt', 'r')
        if not file:
            return
        self.resolution_scale = float(file.readline())
        self.minimum_center_distance = int(file.readline())
        self.param1 = int(file.readline())
        self.param2 = float(file.readline())
        self.minimum_radius = int(file.readline())
        self.maximum_radius = int(file.readline())
        self.tracking_distance = int(file.readline())
        file.close()

    # endregion

    # region UI region
    def mousePressEvent(self, a0: QtGui.QMouseEvent):
        if a0.button() == 1:
            self.scaling_pos1 = a0.pos()
        elif a0.button() == 2:
            self.scaling_pos2 = a0.pos()
        self.scaling_distance = np.sqrt(
            (self.scaling_pos2.x() - self.scaling_pos1.x()) ** 2 + (self.scaling_pos2.y() - self.scaling_pos1.y()) ** 2)

    def closeEvent(self, event):
        self.disconnect_camera()
        self.save_to_settings()

    def setup_ui(self):
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setWindowTitle('Optical determination of the viscosity of a liquid')
        self.setFixedSize(1000, 500)

        self.setup_menubar()

        self.statusbar.setStatusTip('Here will be displayed tips to a program interface')
        self.setStatusBar(self.statusbar)

        self.image_label.move(5, 25)
        self.image_label.resize(800, 450)
        self.image_label.setScaledContents(True)
        self.image_label.setStatusTip('Here will be displayed processed video')
        self.set_image()

        self.camera_list_box.move(810, 25)
        self.camera_list_box.resize(150, 30)
        self.camera_list_box.setStatusTip('Selector of camera')

        self.camera_refresh_button.move(965, 25)
        self.camera_refresh_button.resize(30, 30)
        self.camera_refresh_button.setText('🔍')
        self.camera_refresh_button.clicked.connect(self.update_camera_list)
        self.camera_refresh_button.setStatusTip('Refresh camera list')

        self.camera_connect_button.move(810, 60)
        self.camera_connect_button.resize(185, 30)
        self.camera_connect_button.setText('Connect / Disconnect')
        self.camera_connect_button.clicked.connect(
            lambda: self.disconnect_camera() if self.camera_connected else self.connect_camera())
        self.camera_connect_button.setStatusTip('Connect/disconnect to camera or disable video')

        self.TextLabel.setText('Detection settings')
        self.TextLabel.move(810, 100)
        self.TextLabel.resize(185, 20)
        self.TextLabel.setStatusTip('Settings')

        self.GrayCheckBox.setText('Gray')
        self.GrayCheckBox.move(955, 101)
        self.GrayCheckBox.resize(50, 20)
        self.GrayCheckBox.setStatusTip('Output in gray or normal')
        # =============================
        self.DP.move(810, 125)
        self.DP.resize(185, 20)
        self.DP.setMinimum(1)
        self.DP.setMaximum(10)
        self.DP.setValue(self.resolution_scale)
        self.DP.setSingleStep(0.05)
        self.DP.valueChanged.connect(lambda value: self.set_resolution_scale(value))
        self.DP.setStatusTip('Resolution scale (1 - native, 2 - half)')
        # =============================
        self.MinDist.move(810, 150)
        self.MinDist.resize(185, 20)
        self.MinDist.setMinimum(1)
        self.MinDist.setMaximum(500)
        self.MinDist.setValue(self.minimum_center_distance)
        self.MinDist.setSingleStep(1)
        self.MinDist.valueChanged.connect(lambda value: self.set_minimum_center_distance(value))
        self.MinDist.setStatusTip('Minimum center distance between circles (in pixels)')
        # =============================
        self.Param1.move(810, 175)
        self.Param1.resize(185, 20)
        self.Param1.setMinimum(1)
        self.Param1.setMaximum(1000)
        self.Param1.setValue(self.param1)
        self.Param1.setSingleStep(1)
        self.Param1.valueChanged.connect(lambda value: self.update_param1_value(value))
        self.Param1.setStatusTip('PARAM1 LABEL')
        # =============================
        self.Param2.move(810, 200)
        self.Param2.resize(185, 20)
        self.Param2.setMinimum(0.01)
        self.Param2.setMaximum(30)
        self.Param2.setValue(self.param2)
        self.Param2.setSingleStep(1)
        self.Param2.valueChanged.connect(lambda value: self.update_param2_value(value))
        self.Param2.setStatusTip('PARAM2 LABEL')
        # =============================
        self.MinRadius1.move(810, 225)
        self.MinRadius1.resize(185, 20)
        self.MinRadius1.setMinimum(1)
        self.MinRadius1.setMaximum(5000)
        self.MinRadius1.setValue(self.minimum_radius)
        self.MinRadius1.setSingleStep(1)
        self.MinRadius1.valueChanged.connect(lambda value: self.set_minimum_radius(value))
        self.MinRadius1.setStatusTip('Minimum radius of circle (in pixels)')
        # =============================
        self.MaxRadius1.move(810, 250)
        self.MaxRadius1.resize(185, 20)
        self.MaxRadius1.setMinimum(1)
        self.MaxRadius1.setMaximum(5000)
        self.MaxRadius1.setValue(self.maximum_radius)
        self.MaxRadius1.setSingleStep(1)
        self.MaxRadius1.valueChanged.connect(lambda value: self.set_maximum_radius(value))
        self.MaxRadius1.setStatusTip('Maximum radius of circle (in pixels)')
        # =============================
        self.scaling_value_box.move(810, 455)
        self.scaling_value_box.resize(185, 20)
        self.scaling_value_box.setMinimum(0)
        self.scaling_value_box.setMaximum(500)
        self.scaling_value_box.setStatusTip('Value in millimeters (used for calibration)')
        # =============================
        self.tracking_distance_box.move(810, 430)
        self.tracking_distance_box.resize(185, 20)
        self.tracking_distance_box.setMinimum(1)
        self.tracking_distance_box.setMaximum(5000)
        self.tracking_distance_box.setSingleStep(1)
        self.tracking_distance_box.setValue(self.tracking_distance)
        self.tracking_distance_box.valueChanged.connect(lambda value: self.set_tracking_distance(value))
        self.tracking_distance_box.setStatusTip('Tracking distance (in pixels)')

    def setup_menubar(self):
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1000, 20))
        self.setMenuBar(self.menubar)

        file_action = QtWidgets.QAction('Load file', self)
        file_action.setShortcut('Alt+1')
        file_action.setStatusTip('Load video file')
        file_action.triggered.connect(lambda: self.load_from_file())

        file = self.menubar.addMenu('File')
        file.addActions({file_action})

    # endregion

    # region Set image and grab frames region
    def load_from_file(self):
        self.disconnect_camera()
        video_path = QtWidgets.QFileDialog.getOpenFileName(filter='Video (*.mov *.mp4)')
        if video_path[0]:
            self.camera_connected = True
            self.camera_thread.started.connect(lambda: self.process_video(video_path))
            self.camera_thread.start()

    def process_video(self, video_path):
        video = cv2.VideoCapture(video_path[0])
        self.frequency = int(video.get(cv2.CAP_PROP_FPS))
        while self.camera_connected and not self.camera_only:
            ret, frame = video.read()
            if not ret:
                break
            self.set_image(frame)
            cv2.waitKey(1000 // 25)
        video.release()

    @dispatch()
    def set_image(self):
        pixmap = QtGui.QPixmap(self.image_label.size())
        pixmap.fill(QtGui.QColor('grey'))
        self.image_label.setPixmap(pixmap)

    # todo: refactor
    @dispatch(np.ndarray)
    def set_image(self, img):
        img = cv2.resize(img, (800, 450))  # !!!
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.blur(gray, (3, 3))
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            self.resolution_scale,
            self.minimum_center_distance,
            param1=self.param1,
            param2=self.param2,
            minRadius=int(self.minimum_radius),
            maxRadius=int(self.maximum_radius)
        )
        detections = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for pt in circles[0, :]:
                x, y, r = pt[0], pt[1], pt[2]
                detections.append([x, y, r])
        scaling_coefficient = 1
        if self.scaling_value_box.value() != 0 and self.scaling_distance != 0:
            scaling_coefficient = self.scaling_value_box.value() / self.scaling_distance
        ids = self.tracker.update(detections, self.frequency, scaling_coefficient)
        output_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if self.GrayCheckBox.isChecked():
            output_image = gray
        for i in ids:
            x, y, r, id_ = i
            cv2.circle(output_image, (x, y), r, (75, 175, 75), 2)
            radius_size = str(np.around(r, 1))
            if self.scaling_value_box.value() != 0 and self.scaling_distance != 0:
                radius_size = str(np.around(r * self.scaling_value_box.value() / self.scaling_distance, 1))
            cv2.putText(output_image,
                        str(radius_size) + '|' + str(id_),
                        (x, y),
                        fontFace=cv2.FONT_HERSHEY_DUPLEX,
                        fontScale=1,
                        color=(0, 255, 0))
        output_image = qimage2ndarray.array2qimage(output_image)
        self.image_label.setPixmap(QtGui.QPixmap.fromImage(output_image))

    def grab_frame(self):
        self.graph.grab_frame()

    # endregion

    # region Connect / disconnect / update camera list region
    def update_camera_list(self):
        try:
            current_camera = self.camera_list_box.currentText()
            self.camera_list_box.clear()
            camera_list = self.graph.get_input_devices()
            self.camera_list_box.addItems(camera_list)
            for i in range(len(camera_list)):
                if current_camera == camera_list[i]:
                    self.camera_list_box.setCurrentIndex(i)
        except Exception as e:
            print(e)
            print('No camera found!!!')

    def connect_camera(self):
        if not self.camera_connected:
            try:
                self.camera_only = True
                self.camera_connected = True
                self.graph.add_video_input_device(self.camera_list_box.currentIndex())
                self.graph.add_sample_grabber(lambda image: self.set_image(image))
                self.graph.add_null_render()
                self.graph.prepare_preview_graph()
                self.graph.run()
                self.camera_timer.setInterval(20)
                self.camera_timer.timeout.connect(self.grab_frame)
                self.camera_thread.started.connect(self.camera_timer.start)
                self.camera_thread.finished.connect(self.camera_timer.stop)
                self.camera_thread.start()
            except Exception as e:
                self.disconnect_camera()
                print(e)

    def disconnect_camera(self):
        self.camera_connected = False
        self.camera_only = False
        self.camera_thread.terminate()
        self.graph = FilterGraph()
        self.set_image()
        if len(self.tracker.for_processing) > 0:
            self.hide()
            dialog = Processing(parent=self,
                                data=self.tracker.for_processing,
                                scaling_pix=self.scaling_distance,
                                scaling_mm=self.scaling_value_box.value())
            dialog.show()
        self.tracker = Tracker(self.tracking_distance)
        self.frequency = 50

    # endregion

    # region pyqtSlots region
    @QtCore.pyqtSlot(float)
    def set_resolution_scale(self, value):
        self.resolution_scale = value

    @QtCore.pyqtSlot(int)
    def set_minimum_center_distance(self, value):
        self.minimum_center_distance = value

    # todo: rename & remake on pyqtSlot decorator
    def update_param1_value(self, param1):
        self.param1 = param1

    # todo: remake & on pyqtSlot decorator
    def update_param2_value(self, param2):
        self.param2 = param2

    @QtCore.pyqtSlot(int)
    def set_minimum_radius(self, value):
        self.minimum_radius = value

    @QtCore.pyqtSlot(int)
    def set_maximum_radius(self, value):
        self.maximum_radius = value

    @QtCore.pyqtSlot(int)
    def set_tracking_distance(self, value):
        self.tracking_distance = value
        self.tracker.tracking_distance = value

    # endregion
