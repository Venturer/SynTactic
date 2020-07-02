"""SynTactic utilities.

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

import os
import webbrowser
from keyword import kwlist, iskeyword
from pprint import pprint
from tokenize import tokenize, untokenize, NUMBER, STRING, NAME, OP, COMMENT
from io import BytesIO

PRINT_LINE_NUMBERS = True

built_in_functions = '''__import__, abs, ascii, bytes, 
call, chr, classmethod, compile, complex, divmod, eval, 
exec, float, hash, help, id ,int, len, max,min,object, 
open, ord pow, print ,range, repr, round, slice, staticmethod,
tuple, type'''

built_in_list = [s.strip() for s in built_in_functions.split(',')]

template_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>%title%</title>
<style>

@page {
    margin-top: 1cm;
    margin-bottom: 1cm;
    margin-left: 0.5cm;
    margin-right: 0.5cm;
}

pre {
    counter-reset: text;
    white-space: pre-wrap;       /* Since CSS 2.1 */
    white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
    white-space: -pre-wrap;      /* Opera 4-6 */
    white-space: -o-pre-wrap;    /* Opera 7 */
    word-wrap: break-word;       /* Internet Explorer 5.5+ */
}

code {
    counter-increment: text;
    padding-left: 1em;    
}
code:before {
    color: gray;
    content: counter(text);
    padding-right: 0.5em;
    margin-right: 0.5em;
    border-right: solid gray 1px;
    display: inline-block;
    text-align: right;
    width: 2em;
    font-style: italic;
    -webkit-user-select: none;
}

.keyword {
    font-weight: bold;
    color: darkblue;
}

.builtin {
    color: #7f0055
}

.number {
    color: DarkCyan;
}

.definition {
    font-weight: bold;
    color: darkcyan;
}

.local_name {
    font-style: italic;
}

.comment {
    color: green;
}

.string, .string3, .open_string, .open_string3 {
    color: DarkMagenta;
}

.string3 {
    color: DarkRed;
}

.open_string, .open_string3 {
    background-color: #c3f9d3;
}

.unclosed_expression {
    background-color: LightGray;
}
</style>
</head>

<body>
<pre>
%script%
</pre>
<script>window.print()</script>
</body>
</html>
"""


def span(line, text, s_class):
    return line.replace(f'{text} ', f'<span class={s_class}>{text} </span>')


added_chars=0
current_line = 0


def span_lines(text_lines, start, end, html_class):
    global added_chars, current_line

    if current_line != start[0] - 1:
        added_chars = 0
        current_line = start[0] - 1

    start_line = text_lines[start[0] - 1]
    start_column = start[1]
    span_s = f'<span class={html_class}>'
    text_lines[start[0] - 1] = start_line[:start_column + added_chars] + span_s + start_line[start_column+added_chars:]

    end_line = text_lines[end[0] - 1]
    end_column = end[1] + len(span_s) + added_chars
    text_lines[end[0] - 1] = end_line[:end_column] + '</span>' + end_line[end_column:]
    added_chars += len(span_s+'</span>')

    return text_lines


def highlight(line: str, key_list, s_class) -> str:
    for k in key_list:
        line = span(line, f'{k} ', s_class)

    return line


def print_tokens(s):

    g = tokenize(BytesIO(s.encode('utf-8')).readline)  # tokenize the string
    for toknum, tokval, tok_start, tok_end, tok_line in g:
        print(toknum, tokval, tok_start, tok_end, tok_line)


def token_text(text):

    text_lines = text.splitlines()

    g = tokenize(BytesIO(text.encode('utf-8')).readline)  # generator to tokenize the string

    for toknum, tokval, tok_start, tok_end, tok_line in g:

        # surround tokens with colours
        if toknum == STRING:
            if "'''" in tok_line or '"""' in tok_line:
                span_lines(text_lines, tok_start, tok_end, 'string3')
            else:
                span_lines(text_lines, tok_start, tok_end, 'string')

        elif toknum == COMMENT:
            span_lines(text_lines, tok_start, tok_end, 'comment')

        elif toknum == NUMBER:
            span_lines(text_lines, tok_start, tok_end, 'number')

        elif toknum == NAME:
            if iskeyword(tokval) or tokval in built_in_list:
                span_lines(text_lines, tok_start, tok_end, 'keyword')

    if PRINT_LINE_NUMBERS:
        text_lines = [f'<code>{line}</code>' for line in text_lines]

    highlighted_text = '\n'.join(text_lines)

    return highlighted_text


def print_via_browser(file_text: str, filename: str):
    """Launch a web browser. Use the browser to print the file contents.

    :param file_text: The file contents in plain text.
    :param filename: This is used as the page title.

    Line numbers are shown to the left of each text.
    """

    script_html = token_text(file_text)

    title_html = escape_html(filename)

    full_html = template_html.replace("%title%", title_html).replace("%script%", script_html)

    import tempfile

    temp_handle, temp_fn = tempfile.mkstemp(suffix=".html", prefix="syntactic_")
    with os.fdopen(temp_handle, "w", encoding="utf-8") as f:
        f.write(full_html)


    webbrowser.open(temp_fn)


def escape_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    print('Main')
