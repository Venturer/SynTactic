# -*- coding: utf-8 -*-

"""SynTactic.

    An IDE for MicroPython.

    A Qt5 based program for Python >= 3.8
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

# Version 0.1, May 2020

# standard imports
from __future__ import annotations

import os.path
import sys
from typing import *
from time import sleep

from PyQt5.QtCore import *
from PyQt5.QtGui import *
# PyQt interface imports, Qt5
from PyQt5.QtWidgets import *

# project imports
from pythoneditor import PythonEditor
from terminal import TerminalWidget, serial_ports, hexdump

TITLE = 'SynTactic'


class MainApp(QMainWindow):
    """Main Qt5 Window."""

    callback = None
    captured_text = ''
    ending = ''
    downloaded_filename = ''

    def __init__(self):
        """MainApp Constructor."""

        # ToDo: add SaveAs to menu
        # ToDo: sort out auto-indent in editor

        # call inherited init
        super().__init__()

        # Load the GUI definition
        self.init_ui()

        self.terminal.text_update.connect(self.receive_characters_from_target)

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

        last_port = self.settings.value('com_port', 'COM3')
        if (index := self.port_combo.findText(last_port)) != -1:
            self.port_combo.setCurrentIndex(index)

    # noinspection PyAttributeOutsideInit
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
        run_icon = QIcon('Run_blue_64x.png')
        upload_icon = QIcon('UploadFile_64x.png')
        exit_icon = QIcon('Exit_64x.png')

        self.micropython_icon = QIcon('MicroPython_64x.png')
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

        get_target_files_button = QPushButton(get_icon, 'List Files')
        get_target_files_button.clicked.connect(self.on_get_target_files_button_clicked)
        side_layout.addWidget(get_target_files_button)

        self.target_files = QListWidget()
        self.target_files.setMinimumWidth(100)
        self.target_files.itemDoubleClicked.connect(self.on_target_files_itemDoubleClicked)
        side_layout.addWidget(self.target_files)

        run_target_button = QPushButton(run_icon, 'Run File')
        run_target_button.clicked.connect(self.on_run_target_button_clicked)
        side_layout.addWidget(run_target_button)

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
        top_button_layout = QHBoxLayout()
        main_layout.addLayout(top_button_layout)

        # Place Action buttons
        new_button = QPushButton(new_icon, "New")
        new_button.clicked.connect(self.on_new_clicked)
        top_button_layout.addWidget(new_button)

        self.open_button = QPushButton(open_icon, "Open")
        self.open_button.clicked.connect(self.on_open_clicked)
        top_button_layout.addWidget(self.open_button)

        self.save_button = QPushButton(save_icon, "Save")
        self.save_button.clicked.connect(self.on_save_clicked)
        top_button_layout.addWidget(self.save_button)

        top_button_layout.addSpacing(16)

        run_button = QPushButton(run_icon, "Run")
        run_button.clicked.connect(self.on_run_button_clicked)
        top_button_layout.addWidget(run_button)

        upload_button = QPushButton(upload_icon, "Upload")
        upload_button.clicked.connect(self.on_upload_button_clicked)
        top_button_layout.addWidget(upload_button)

        top_button_layout.addStretch()

        exit_button = QPushButton(exit_icon, "Exit")
        exit_button.clicked.connect(QApplication.instance().quit)
        top_button_layout.addWidget(exit_button)

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

        file_menu = QMenu("&File", self)
        self.menuBar().addMenu(file_menu)

        file_menu.addAction("&New...", self.on_new_clicked, "Ctrl+N")
        file_menu.addAction("&Open...", self.on_open_clicked, "Ctrl+O")
        file_menu.addAction("&Save...", self.on_save_clicked, "Ctrl+S")
        file_menu.addAction("E&xit", QApplication.instance().quit, "Ctrl+Q")

    def setup_help_menu(self):

        help_menu = QMenu("&Help", self)
        self.menuBar().addMenu(help_menu)

        help_menu.addAction("&About", self.about)
        help_menu.addAction("About &Qt", QApplication.instance().aboutQt)

    def about(self):
        QMessageBox.about(self, "About SynTactic",
                          "<p>A <b>Python Editor with Syntax Highlighting</b> for <b>MicroPython</b> by G4AUC.")

    def callback_with_text_from_target(self, callback: Optional(Any) = None, ending: str = '\n'):
        """Sets self.callback and self.ending which are then used by the slot method attached to
            the signal which emits the line text. The current captured text is cleared.

            That method sends the text on to the callback method/function when available.
            """

        self.captured_text = ''
        self.callback, self.ending = callback, ending

    def receive_characters_from_target(self, text):
        """Slot to receive characters from the target via the terminal up to
            but not including the contents of `self.ending`.

            The callback (in `self.callback`) is called with the `text`,
            when available.
            """

        s = str(text)
        self.captured_text += s

        if self.callback:
            joined = ''.join(self.captured_text.splitlines(keepends=True))
            if (inx := joined.find(self.ending)) != -1:
                self.callback(j := joined[:inx])

                # callback should probably do this as well to avoid being
                # potentially called with next line as well
                self.callback = None

    @pyqtSlot(QListWidgetItem)
    def on_target_files_itemDoubleClicked(self, item: QListWidgetItem):
        """Slot triggered when the list item is double clicked.
            """
        if item:
            self.callback_with_text_from_target(self.target_files_itemDoubleClicked_callback,
                                                ending='&end')
            self.downloaded_filename = item.text()

            send_command = f"exec(\"with open('./{item.text()}','r') as f:" \
                           f" [print(l) for l in f.read().splitlines()]; print(' &''end')\", globals())"

            self.terminal.send_text(f"{send_command}\r")

    def target_files_itemDoubleClicked_callback(self, text):
        """"""
        self.callback = None

        lines = [line for line in text.splitlines()]

        editor = self.on_new_clicked()
        editor.filename = f"[{self.downloaded_filename}]"
        inx = self.tab_widget.indexOf(self.tab_widget.currentWidget())
        self.tab_widget.setTabText(inx, editor.filename)
        self.tab_widget.setTabIcon(inx, self.micropython_icon)
        editor.append(chr(10).join(lines[1:]))

    @pyqtSlot()
    def on_run_target_button_clicked(self):
        """Slot triggered when button clicked.
            """

        item = self.target_files.currentItem()

        if item:
            send_command = f"exec(open('./{item.text()}').read(),globals())\r"
            self.terminal.send_text(send_command)

    @pyqtSlot()
    def on_upload_button_clicked(self):
        """Slot triggered when the button is clicked.
            """

        if editor := self.tab_widget.currentWidget():
            content = editor.text()
            dir, filename = os.path.split(editor.filename)

            cont_lines = content.splitlines(keepends=True)
            for i, c_line in enumerate(cont_lines):
                if i==0:
                    send_command = f"__c_ =  '''{c_line}'''\r\n"
                    self.terminal.send_text(f"\x05{send_command}\x04")
                    sleep(0.02)
                else:
                    send_command = f"__c_ +=  '''{c_line}'''\r\n"
                    self.terminal.send_text(f"\x05{send_command}\x04")
                    sleep(0.02)

            send_command = f"exec(\"with open('./{filename}', 'w') as f: " \
                           f"[f.write(c) for c in __c_.splitlines(keepends=True)]\", globals())\r"
            self.terminal.send_text(f"\x05{send_command}\x04")
            sleep(0.02)

    @pyqtSlot()
    def on_get_target_files_button_clicked(self):
        """Slot triggered when the button is clicked.
            """

        if self.terminal.is_connected():
            self.callback_with_text_from_target(self.get_target_files_callback, ending='>>> ')
            self.terminal.send_text('import os; os.listdir()\r')
        else:
            print('Disconnected!')

    def get_target_files_callback(self, text):
        """Called back when the terminal text resulting from
            the on_get_target_files_button_clicked method
            is available."""

        self.callback = None

        text_lines = text.splitlines()  # split into lines
        files_line = text_lines[1]  # the files list is on this line

        # Convert text in files_line to a list of file names
        target_files: List[str] = [f.strip("[]'") for f in files_line.split("', '")]

        self.target_files.clear()
        self.target_files.addItems(target_files)

    @pyqtSlot()
    def on_run_button_clicked(self):
        """Slot triggered when the button is clicked.

            Runs the script in the current editor page on the target MCU.
            The script is not uploaded to the target file system.
            """

        editor = self.tab_widget.currentWidget()
        if editor:
            self.save_file(editor)

            # Use paste REPL
            self.terminal.send_text(f'\x05{editor.text()}\x04\r')

    @pyqtSlot()
    def on_port_connect_button_clicked(self):
        """Slot triggered when the button is clicked.
            """

        self.terminal.close_serial_port_and_wait()

        if self.port_combo.count():  # Make sure there is at least one port name

            try:
                port = self.port_combo.currentText()
                self.settings.setValue('com_port', port)
                self.terminal.connect(port, 115200)
                self.terminal.send_text('\r')
            except Exception as e:
                print('Could not connect to: ', port, '!', sep='')
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

        return editor

    @pyqtSlot()
    def on_open_clicked(self):
        """Slot triggered when the button is clicked.
            """

        dir = self.settings.value('open_file_dir', '.')
        filename, _ = QFileDialog.getOpenFileName(self,
                                                  "Open File", dir, "Python Files (*.py *.pyw *.pyi )")

        if filename:
            editor = PythonEditor()
            editor.filename = filename

            dir, name = os.path.split(filename)
            self.tab_widget.addTab(editor, self.py_icon, name)
            self.settings.setValue('open_file_dir', dir)

            self.tab_widget.setCurrentWidget(editor)

            # Load py file into the editor
            with open(filename, 'r') as infile:
                editor.setText(r := infile.read())

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

        if editor:
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
