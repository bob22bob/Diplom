from PyQt5 import QtWidgets, QtGui


class Processing(QtWidgets.QMainWindow):
    def __init__(self, data: dict, scaling_mm, scaling_pix, parent=None):
        super().__init__(parent)

        self.data = data

        self.setWindowTitle('Data processing')
        self.setFixedSize(500, 800)
        self.setWindowIcon(QtGui.QIcon('icon.png'))

        self.calculate_button = QtWidgets.QPushButton(self)

        self.pix_spinbox = QtWidgets.QSpinBox(self)
        self.pix_label = QtWidgets.QLabel(self)
        self.mm_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.mm_label = QtWidgets.QLabel(self)
        self.checkbox = QtWidgets.QCheckBox(self)
        self.rescale_label = QtWidgets.QLabel(self)
        self.rescale_button = QtWidgets.QPushButton(self)

        self.fluid_density_label = QtWidgets.QLabel(self)
        self.fluid_density_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.objects_density_label = QtWidgets.QLabel(self)
        self.objects_density_spinbox = QtWidgets.QDoubleSpinBox(self)

        self.legend_label = QtWidgets.QLabel(self)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.setup_ui()

        self.formLayout = QtWidgets.QFormLayout(self)
        self.groupBox = QtWidgets.QGroupBox(self)
        self.scroll = QtWidgets.QScrollArea(self)

        self.update_scale()

        self.pix_spinbox.setValue(scaling_pix)
        self.mm_spinbox.setValue(scaling_mm)

    def setup_ui(self):
        self.calculate_button.move(5, 30)
        self.calculate_button.setText('Calculate')
        self.calculate_button.resize(100, 50)
        self.calculate_button.clicked.connect(self.calculate_coefficient)

        self.pix_spinbox.move(120, 30)
        self.pix_spinbox.setMinimum(1)
        self.pix_spinbox.setMaximum(1920)

        self.pix_label.move(150, 50)
        self.pix_label.setText('pixels')

        self.mm_spinbox.move(250, 30)
        self.mm_spinbox.setMinimum(0.01)
        self.mm_spinbox.setMaximum(1000)

        self.mm_label.move(270, 50)
        self.mm_label.setText('millimeters')

        self.rescale_label.move(230, 30)
        self.rescale_label.setText('=>')

        self.checkbox.move(200, 60)
        self.checkbox.setText('use scale')

        self.rescale_button.move(190, 90)
        self.rescale_button.setText('Rescale')
        self.rescale_button.clicked.connect(self.update_scale)

        self.fluid_density_label.move(395, 0)
        self.fluid_density_label.setText('Fluid density')

        self.fluid_density_spinbox.move(395, 30)
        self.fluid_density_spinbox.setMinimum(0.01)
        self.fluid_density_spinbox.setMaximum(10000)
        self.fluid_density_spinbox.setValue(1)
        self.fluid_density_spinbox.setStatusTip('Density in g/cm^3 (г/см^3)')

        self.objects_density_label.move(395, 60)
        self.objects_density_label.setText('Objects density')

        self.objects_density_spinbox.move(395, 90)
        self.objects_density_spinbox.setMinimum(0.01)
        self.objects_density_spinbox.setMaximum(10000)
        self.objects_density_spinbox.setValue(1.05)
        self.fluid_density_spinbox.setStatusTip('Density in g/cm^3 (г/см^3)')

        self.legend_label.move(10, 130)
        self.legend_label.resize(1000, 20)
        self.legend_label.setText('id | frames | radius | distance | avg.speed)')

    def closeEvent(self, event):
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if type(widget) is not (Processing or QtWidgets.QMenu):
                widget.show()

    def update_scale(self):
        for i in reversed(range(self.formLayout.count())):
            self.formLayout.itemAt(i).widget().setParent(None)
        for key, value in self.data.items():
            if value[3] <= 0.1:
                continue
            if self.checkbox.isChecked():
                scaling_coefficient = self.mm_spinbox.value() / self.pix_spinbox.value()
                label1 = QtWidgets.QLabel(
                    str('%-4.4s %-12.12s %-10.10s %-12.2f %-11.2f' % (
                        key, value[0], value[1] * scaling_coefficient, value[2] * scaling_coefficient,
                        value[3] * scaling_coefficient)))
            else:
                label1 = QtWidgets.QLabel(
                    str('%-4.4s %-12.12s %-10.10s %-12.2f %-11.2f' % (key, value[0], value[1], value[2], value[3])))
            button = QtWidgets.QPushButton(self)
            button.setText('Disable in calculations')
            self.formLayout.addRow(label1, button)
        self.groupBox.setLayout(self.formLayout)
        self.scroll.setWidget(self.groupBox)
        self.scroll.setWidgetResizable(True)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.scroll)

        self.scroll.move(0, 150)
        self.scroll.resize(500, 650)

    def calculate_coefficient(self):
        layout.addWidget(self.scroll)
