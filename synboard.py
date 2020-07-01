"""SynTactic board utilities.

    An IDE for MicroPython.

    A Qt5 based program for Python >= 3.8
    QScintilla is used for editing.

    The MIT License (MIT)

    Copyright (c) 2020 Steve Baugh

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

    """

from __future__ import annotations

import sys
import time

from ampy.pyboard import Pyboard, PyboardError
from ampy import pyboard
from ampy.files import Files, BUFFER_SIZE, DirectoryExistsError

_rawdelay = None


class BoardLink(Pyboard):
    """Subclass the ampy Pyboard class so that the SynTactic serial
        port can be used."""

    def __init__(self, serial_port, wait=0, rawdelay=0):
        global _rawdelay
        _rawdelay = rawdelay
        pyboard._rawdelay = rawdelay

        self.serial = serial_port


if __name__ == "__main__":
    print('Main')
