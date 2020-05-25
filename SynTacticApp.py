# -*- coding: utf-8 -*-

"""SynTactic.

    An IDE for MicroPython.

    A Qt5 based program template for Python3.
    QScintilla is used for editing.

    """

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

# Version 1.0, June 2018

# standard imports
from __future__ import annotations

import sys
import os.path

# PyQt interface imports, Qt5
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# project imports
from pythoneditor import PythonEditor
from terminal import TerminalWidget, serial_ports

TITLE = 'SynTactic'


def waiting_cursor(func):
    """Decorator to set waiting cursor while method is running."""

    def new_function(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.repaint()
        try:
            func(self)
        except Exception as e:
            raise e
        finally:
            QApplication.restoreOverrideCursor()
            self.repaint()

    return new_function


class MainApp(QMainWindow):
    """Main Qt5 Window."""

    def __init__(self):
        """MainApp Constructor."""

        # ToDo: Save As untitled.py files

        # call inherited init
        super().__init__()

        # Load the GUI definition
        self.init_ui()

        # Create an object to save and restore settings
        self.settings = QSettings('G4AUC', 'SynTactic')
        # self.settings.clear()

        # Restore window position etc. from saved settings
        self.restoreGeometry(self.settings.value('geometry', type=QByteArray))

        # Show the Application
        self.show()

        # restore the splitter positions after the app is showing
        self.splitter_main_pos = self.settings.value('splitter_main_pos', 300)
        self.splitter_main.moveSplitter(int(self.splitter_main_pos), 1)
        self.splitter_side_pos = self.settings.value('splitter_side_pos', 300)
        self.splitter_side.moveSplitter(int(self.splitter_side_pos), 1)

    def init_ui(self):
        """Initialises the user interface."""

        # Define the default geometry of the main window
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle(TITLE)

        # Icons
        open_icon = QIcon('OpenFile_64x.png')
        get_icon = QIcon('Open_blue_64x.png')
        new_icon = QIcon('NewFile_64x.png')
        save_icon = QIcon('Save_64x.png')
        usb_icon = QIcon('USB_64x.png')
        connect_icon = QIcon('ConnectPlugged_64x.png')
        disconnect_icon = QIcon('ConnectUnplugged_64x.png')
        exit_icon = QIcon('Exit_64x.png')
        self.py_icon = QIcon('py.ico')  # Icon to add to tabs

        # Create frame and layout
        self.frame = QFrame(self)
        self.frame_layout = QHBoxLayout()
        self.frame.setLayout(self.frame_layout)
        self.setCentralWidget(self.frame)

        # Splitter
        self.splitter_side = QSplitter()
        self.splitter_side.splitterMoved.connect(self.on_splitter_side_splitterMoved)
        self.frame_layout.addWidget(self.splitter_side)

        # Target side panel

        side_frame = QFrame()
        side_layout = QVBoxLayout()
        side_frame.setLayout(side_layout)

        target_label = QLabel('Target MCU')
        target_label.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(target_label)

        port_label = QLabel('Port:')
        port_label.setAlignment(Qt.AlignLeft)
        side_layout.addWidget(QLabel('COM Port:'))

        self.port_combo = QComboBox()
        self.port_combo.addItems(serial_ports())
        side_layout.addWidget(self.port_combo)

        port_scan_button = QPushButton(usb_icon, 'Scan Ports')
        port_scan_button.clicked.connect(self.on_port_scan_button_clicked)
        side_layout.addWidget(port_scan_button)

        port_connect_button = QPushButton(connect_icon, 'Connect')
        port_connect_button.clicked.connect(self.on_port_connect_button_clicked)
        side_layout.addWidget(port_connect_button)

        port_disconnect_button = QPushButton(disconnect_icon, 'Disconnect')
        port_disconnect_button.clicked.connect(self.on_port_disconnect_button_clicked)
        side_layout.addWidget(port_disconnect_button)

        side_layout.addWidget(QLabel('Target Files:'))

        get_target_files_button = QPushButton(get_icon, 'Get Files')
        get_target_files_button.clicked.connect(self.on_get_target_files_button_clicked)
        side_layout.addWidget(get_target_files_button)

        self.target_files = QListWidget()
        self.target_files.setMinimumWidth(100)
        side_layout.addWidget(self.target_files)

        self.splitter_side.addWidget(side_frame)

        # Main frame

        main_frame = QFrame(self)
        main_layout = QVBoxLayout()
        main_frame.setLayout(main_layout)

        self.splitter_main = QSplitter()
        self.splitter_main.splitterMoved.connect(self.on_splitter_main_splitterMoved)
        self.splitter_main.setOrientation(Qt.Vertical)

        self.splitter_side.addWidget(self.splitter_main)
        self.splitter_main.addWidget(main_frame)

        # Top Button layout
        self.topButtonLayout = QHBoxLayout()
        main_layout.addLayout(self.topButtonLayout)

        # Place Action buttons
        new_button = QPushButton(new_icon, "New")
        new_button.clicked.connect(self.on_new_clicked)
        self.topButtonLayout.addWidget(new_button)

        self.open_button = QPushButton(open_icon, "Open")
        self.open_button.clicked.connect(self.on_open_clicked)
        self.topButtonLayout.addWidget(self.open_button)

        self.save_button = QPushButton(save_icon, "Save")
        self.save_button.clicked.connect(self.on_save_clicked)
        self.topButtonLayout.addWidget(self.save_button)

        self.topButtonLayout.addStretch()

        exit_button = QPushButton(exit_icon, "Exit")
        exit_button.clicked.connect(QApplication.instance().quit)
        self.topButtonLayout.addWidget(exit_button)

        # Edit layout
        self.edit_layout = QVBoxLayout()
        main_layout.addLayout(self.edit_layout)

        # Tab Widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.on_tab_close_request)
        self.edit_layout.addWidget(self.tab_widget)

        # Terminal
        self.terminal = TerminalWidget()
        self.terminal.setMinimumHeight(100)
        self.splitter_main.addWidget(self.terminal)

        # Menus
        self.setup_file_menu()
        self.setup_help_menu()

    def setup_file_menu(self):

        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

        fileMenu.addAction("&New...", self.on_new_clicked, "Ctrl+N")
        fileMenu.addAction("&Open...", self.on_open_clicked, "Ctrl+O")
        fileMenu.addAction("&Save...", self.on_save_clicked, "Ctrl+S")
        fileMenu.addAction("E&xit", QApplication.instance().quit, "Ctrl+Q")

    def setup_help_menu(self):

        helpMenu = QMenu("&Help", self)
        self.menuBar().addMenu(helpMenu)

        helpMenu.addAction("&About", self.about)
        helpMenu.addAction("About &Qt", QApplication.instance().aboutQt)

    def about(self):
        QMessageBox.about(self, "About SynTactic",
                "<p>A <b>Python Editor with Syntax Highlighting</b> for <b>MicroPython</b> by G4AUC.")

    @pyqtSlot()
    def on_get_target_files_button_clicked(self):
        """Slot triggered when the button is clicked.
            """
        self.terminal.captured_text = ''
        self.terminal.send_text('import os; os.listdir()\r')

        print('Cap:', self.terminal.captured_text)


    @pyqtSlot()
    def on_port_connect_button_clicked(self):
        """Slot triggered when the button is clicked.
            """

        self.terminal.close_serial_port_and_wait()

        if self.port_combo.count():  # Make sure there is at least one port name

            try:
                port = self.port_combo.currentText()
                self.terminal.connect(port, 115200)
            except Exception as e:
                print('Could not connect to:', port, '!')
                print(e)

    @pyqtSlot()
    def on_port_disconnect_button_clicked(self):
        """Slot triggered when the button is clicked.
            """

        try:
            self.terminal.close_serial_port_and_wait()
        except Exception as e:
            print('Could not disconnect!')
            print(e)

    @pyqtSlot()
    def on_port_scan_button_clicked(self):
        """Slot triggered when the button is clicked.
            """

        self.port_combo.clear()
        self.port_combo.addItems(serial_ports())

    @pyqtSlot(int, int)
    def on_splitter_side_splitterMoved(self, pos, index):
        """Slot triggered when the splitter is moved.

            Saves the new position."""

        self.settings.setValue('splitter_side_pos', pos)

    @pyqtSlot(int, int)
    def on_splitter_main_splitterMoved(self, pos, index):
        """Slot triggered when the splitter is moved.

            Saves the new positions."""


        self.settings.setValue('splitter_main_pos', pos)

    @pyqtSlot()
    def on_new_clicked(self):
        """Slot triggered when the button is clicked.
            """

        editor = PythonEditor()
        self.tab_widget.addTab(editor, self.py_icon, editor.filename)

        self.tab_widget.setCurrentWidget(editor)

    @pyqtSlot()
    def on_open_clicked(self):
        """Slot triggered when the button is clicked.
            """

        filename, _ = QFileDialog.getOpenFileName(self,
                        "Open File", ".", "Python Files (*.py *.pyw *.pyi )")

        if filename:
            editor = PythonEditor()
            editor.filename = filename

            _, name = os.path.split(filename)
            self.tab_widget.addTab(editor, self.py_icon, name)

            self.tab_widget.setCurrentWidget(editor)

            # Load py file into the editor
            with open(filename, 'r') as infile:
                editor.setText(infile.read())

            editor.setModified(False)

    @pyqtSlot()
    def on_save_clicked(self):
        """Slot triggered when the button is clicked.
            """

        editor = self.tab_widget.currentWidget()
        self.save_file(editor)

    @pyqtSlot(int)
    def on_tab_close_request(self, tab_index: int):
        """Action when the close button on a tab is clicked."""

        editor = self.tab_widget.widget(tab_index)
        self.try_to_close_editor(editor, tab_index)

    def try_to_close_editor(self, editor: PythonEditor, tab_index: int) -> bool:
        """Try to close the `editor` in tab `tab_index`."""

        if editor is None:
            return True

        closed = False

        if editor.isModified():
            reply = QMessageBox.question(self, "Save File",
                                         'File has been modified. Do you wish to save it?',
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                file_name, _ = QFileDialog.getSaveFileName(self,
                                          "Save Source File",
                                          editor.filename,
                                          "Python Files (*.py *.pyw, *.pyi)")
                if file_name:
                    editor.filename = file_name
                    self.save_file(editor)
                    editor.close()
                    self.tab_widget.removeTab(tab_index)
                    closed = True

            elif reply == QMessageBox.No:
                editor.close()
                self.tab_widget.removeTab(tab_index)
                closed = True

        else:
            editor.close()
            self.tab_widget.removeTab(tab_index)
            closed = True

        return closed

    @staticmethod
    def save_file(editor: PythonEditor):
        """Save file from the `editor` as `editor`.filename."""

        # Save file
        with open(editor.filename, 'w') as outfile:
            outfile.write(editor.text())

        editor.setModified(False)

    def closeEvent(self, event):
        """Override inherited QMainWindow closeEvent.

            Do any cleanup actions before the application closes:
                Try to save any modified editor pages.
                Saves the application geometry.

            Accepts the event if all editor pages have closed
            which closes the application and ignores the event
            if any of the editor pages does not close.
            """

        all_closed = True
        editor_widgets = [self.tab_widget.widget(i) for i in range(self.tab_widget.count())]

        for editor in editor_widgets:
            tab_index = self.tab_widget.indexOf(editor)
            closed = self.try_to_close_editor(editor, tab_index)
            if not closed:
                all_closed = False

        self.settings.setValue("geometry", self.saveGeometry())

        if all_closed:
            event.accept()
        else:
            event.ignore()

    # --- Methods not normally modified:

    def resizeEvent(self, event):
        """Extends inherited QMainWindow resize event.

            Saves the window geometry."""

        self.settings.setValue("geometry", self.saveGeometry())

        super().resizeEvent(event)

    def moveEvent(self, event):
        """Extends inherited QMainWindow move event.

            Saves the window geometry."""

        self.settings.setValue("geometry", self.saveGeometry())

        super().moveEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainApp()
    sys.exit(app.exec_())


