"""Simple PyQT serial terminal v0.09 from iosoft.blog."""


from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QTextEdit, QWidget, QApplication, QVBoxLayout

try:
    import Queue
except ImportError:
    import queue as Queue

import sys, time
import serial
import glob

VERSION = '0.1'

WIN_WIDTH, WIN_HEIGHT = 684, 400    # Window size
SER_TIMEOUT = 0.1                   # Timeout for serial Rx
RETURN_CHAR = "\r"                  # Char to be sent when Enter key pressed
PASTE_CHAR = "\x16"                 # Ctrl code for clipboard paste
baudrate = 115200                   # Default baud rate
portname = "COM15"                  # Default port name
hexmode = False                     # Flag to enable hex display
captured_text = ''


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]

    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')

    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass

    return result


# Convert a string to bytes
def str_to_bytes(s):
    return s.encode('latin-1')


# Convert bytes to string
def bytes_to_str(d):
    return d if type(d) is str else "".join([chr(b) for b in d])


# Return hexadecimal values of data
def hexdump(data):
    return " ".join(["%02X" % ord(b) for b in data])


# Return a string with high-bit chars replaced by hex values
def textdump(data):
    return "".join(["[%02X]" % ord(b) if b > '\x7e' else b for b in data])


# Display incoming serial data
def display(s):
    if not hexmode:
        sys.stdout.write(textdump(str(s)))
    else:
        sys.stdout.write(hexdump(s) + ' ')


# Custom text box, catching keystrokes
class TextBox(QTextEdit):
    def __init__(self, *args):
        QTextEdit.__init__(self, *args)

    def keyPressEvent(self, event):  # Send keypress to parent's handler
        self.parent().keypress_handler(event)


class TerminalWidget(QTextEdit):
    """Main widget"""

    text_update = QtCore.pyqtSignal(str)

    def __init__(self, *args):

        QWidget.__init__(self, *args)

        self.setContentsMargins(1, 1, 1, 1)

        # Create custom text box
        self.textbox = TextBox()

        font = QtGui.QFont()
        font.setFamily("Source Code Pro")  # Monospaced font
        font.setPointSize(10)
        self.textbox.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(self.textbox)
        self.setLayout(layout)

        self.resize(WIN_WIDTH, WIN_HEIGHT)  # Set window size

        # Connect text update to handler
        self.text_update.connect(self.append_text)

        sys.stdout = self  # Redirect sys.stdout to self

    def connect(self, port, baud):
        global portname, baudrate

        portname, baudrate = port, baud

        self.serial_thread = SerialThread(portname, baudrate)  # Start serial thread
        self.serial_thread.start()

    def write(self, text):  # Handle sys.stdout.write: update display
        self.text_update.emit(text)  # Send signal to synchronise call with main thread

    def flush(self):  # Handle sys.stdout.flush: do nothing
        pass

    def append_text(self, text):  # Text display update handler
        cur = self.textbox.textCursor()
        cur.movePosition(QtGui.QTextCursor.End)  # Move cursor to end of text

        s = str(text)
        while s:
            head, sep, s = s.partition("\r\n")  # Split line at LF
            cur.insertText(head)  # Insert text at cursor
            if sep:  # New line
                cur.insertBlock()

        self.textbox.setTextCursor(cur)  # Update visible cursor

    def keypress_handler(self, event):
        """Handle keypress from text box"""

        k = event.key()

        s = RETURN_CHAR if k == QtCore.Qt.Key_Return else event.text()

        if len(s) > 0 and s[0] == PASTE_CHAR:  # Detect ctrl-V paste
            cb = QApplication.clipboard()
            self.serial_thread.ser_out(cb.text())  # Send paste string to serial driver

        else:
            self.serial_thread.ser_out(s)  # ..or send keystroke

    def send_text(self, text):

        if self.is_connected():
            self.serial_thread.ser_out(text)
        else:
            print('Disconnected!')

    def is_connected(self):

        try:
            running = self.serial_thread.isRunning()
            return True if running else False
        except AttributeError:
            return False

    def closeEvent(self, event):  # Window closing
        self.close_serial_port_and_wait()

    def close_serial_port_and_wait(self):
        """Close the serial port and wait for the serial thread to terminate.

            No action if thread does not exist.
            """

        try:
            self.serial_thread.running = False  # Wait until serial thread terminates
            self.serial_thread.wait()

        except AttributeError:
            # Pass quietly if thread does not exist
            pass


class SerialThread(QtCore.QThread):
    """Thread to handle incoming and outgoing serial data."""

    def __init__(self, portname, baudrate):
        """Initialise with default serial port details"""

        QtCore.QThread.__init__(self)
        self.portname, self.baudrate = portname, baudrate
        self.txq = Queue.Queue()
        self.running = True

    def ser_out(self, s):
        """Write outgoing data to serial port if open"""

        self.txq.put(s)  # ..using a queue to sync with reader thread

    def ser_in(self, s):
        """Write incoming serial data to screen"""

        display(s)

    def run(self):
        """Run serial reader thread."""

        print("Opening %s at %u baud %s" % (self.portname, self.baudrate,
                                            "(hex display)" if hexmode else ""))
        try:
            self.ser = serial.Serial(self.portname, self.baudrate, timeout=SER_TIMEOUT)
            time.sleep(SER_TIMEOUT * 1.2)
            self.ser.flushInput()
        except:
            self.ser = None

        if not self.ser:
            print("Can't open port")
            self.running = False

        while self.running:
            s = self.ser.read(self.ser.in_waiting or 1)

            if s:  # Get data from serial port
                self.ser_in(bytes_to_str(s))  # ..and convert to string

            if not self.txq.empty():
                txd = str(self.txq.get())  # If Tx data in queue, write to serial port
                self.ser.write(str_to_bytes(txd))

        if self.ser:  # Close serial port when thread finished
            self.ser.close()
            self.ser = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    opt = err = None
    for arg in sys.argv[1:]:  # Process command-line options
        if len(arg) == 2 and arg[0] == "-":
            opt = arg.lower()
            if opt == '-x':  # -X: display incoming data in hex
                hexmode = True
                opt = None
        else:
            if opt == '-b':  # -B num: baud rate, e.g. '9600'
                try:
                    baudrate = int(arg)
                except:
                    err = "Invalid baudrate '%s'" % arg
            elif opt == '-c':  # -C port: serial port name, e.g. 'COM1'
                portname = arg
    if err:
        print(err)
        sys.exit(1)
    w = TerminalWidget()
    w.setWindowTitle('PyQT Serial Terminal ' + VERSION)
    w.show()
    sys.exit(app.exec_())

# EOF