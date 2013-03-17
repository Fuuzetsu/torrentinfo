#!/usr/bin/env python

# This file is part of torrentinfo.
#
# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with torrentinfo.  If not, see <http://www.gnu.org/licenses/>.
"""
Parses .torrent files and displays various summaries of the
information contained within.

Published under the GNU Public License: http://www.gnu.org/copyleft/gpl.html
"""

import sys
import argparse
import os.path
import re
import time

#  see pylint ticket #2481
from string import printable  # pylint: disable-msg=W0402

TAB_CHAR = '    '

class TextFormatter:
    """Class used to format strings before printing."""
    NONE = 0x000000
    NORMAL = 0x000001
    BRIGHT = 0x000002
    WHITE = 0x000004
    GREEN = 0x000008
    RED = 0x000010
    CYAN = 0x000020
    YELLOW = 0x000040
    MAGENTA = 0x000080
    DULL = 0x000100

    escape = chr(0x1b)

    mapping = [(NORMAL, '[0m'),
               (BRIGHT, '[1m'),
               (DULL, '[22m'),
               (WHITE, '[37m'),
               (GREEN, '[32m'),
               (CYAN, '[36m'),
               (YELLOW, '[33m'),
               (RED, '[31m'),
               (MAGENTA, '[35m'), ]

    def __init__(self, colour):
        self.colour = colour

    def string_format(self, format_spec, string='', out=sys.stdout):
        """Attaches colour codes to strings before outputting them.

        :param format_spec: value of the colour code
        :type format_spec: int
        :param string: string to colour
        :type string: str
        """
        if self.colour:
            codestring = ''
            for name, code in TextFormatter.mapping:
                if format_spec & name:
                    codestring += TextFormatter.escape + code
            out.write(codestring + string)
        else:
            out.write(string)


class Torrent(dict):
    """A class modelling a parsed torrent file."""

    def __init__(self, filename, string_buffer):
        tmp_dict = decode(string_buffer)

        if type(tmp_dict) != dict:
            raise UnexpectedType(self.__class__, dict)

        super(Torrent, self).__init__(tmp_dict)
        self.filename = filename


class UnexpectedType(Exception):
    """Thrown when the torrent file is not just a single dictionary"""
    pass

class UnknownTypeChar(Exception):
    """Thrown when Torrent.parse encounters unexpected character"""
    pass

def dump_as_date(number, formatter, out=sys.stdout):
    """Dumps out the Integer instance as a date.

    :param n: number to format
    :type n: int
    :param formatter: formatter to use for string formatting
    :type formatter: TextFormatter
    """
    formatter.string_format(TextFormatter.MAGENTA, time.strftime(
            '%Y/%m/%d %H:%M:%S %Z\n', time.gmtime(number)), out=out)

def dump_as_size(number, formatter, tabchar, depth, out=sys.stdout):
    """Dumps the string to the stdout as file size after formatting it.

    :param n: number to format
    :type n: int
    :param formatter: Text formatter to use to format the output
    :type formatter: TextFormatter
    :param tabchar: tab character to use for indentation
    :type tabchar: str
    :param depth: indentation depth
    :type depth: int
    """
    size = float(number)
    sizes = ['B', 'KB', 'MB', 'GB']
    while size >= 1024 and len(sizes) > 1:
        size /= 1024
        sizes = sizes[1:]
    formatter.string_format(TextFormatter.CYAN, '%s%.1f%s\n' % (
            tabchar * depth, size, sizes[0]),
                            out=out)


def dump(item, formatter, tabchar, depth, newline=True, out=sys.stdout):
    """Printing method.

    :param item: item to print
    :type item: dict or list or str or int
    :param formatter: Text formatter to use to format the output
    :type formatter: TextFormatter
    :param tabchar: tab character to use for indentation
    :type tabchar: str
    :param depth: indentation depth
    :type depth: int
    :param newline: indicates whether to insert a newline after certain strings
    :type newline: bool
    """
    def teq(comp_type):
        """Helper that checks for type equality."""
        return type(item) == comp_type

    if teq(dict):
        for key in item.keys().sort():
            formatter.string_format(TextFormatter.NORMAL | TextFormatter.GREEN,
                                    out=out)

            if depth < 2:
                formatter.string_format(TextFormatter.BRIGHT, out=out)

            dump(key, formatter, tabchar, depth, out=out)
            formatter.string_format(TextFormatter.NORMAL, out=out)
            dump(item[key], formatter, tabchar, depth + 1, out=out)
    elif teq(list):
        if len(item) == 1:
            dump(item[0], formatter, tabchar, depth, out=out)
        else:
            for index in range(len(item)):
                formatter.string_format(TextFormatter.BRIGHT |
                                        TextFormatter.YELLOW,
                                        '%s%d\n' % (tabchar * depth, index),
                                        out=out)
                formatter.string_format(TextFormatter.NORMAL, out=out)
                dump(item[index], formatter, tabchar, depth + 1, out=out)
    elif teq(str):
        if is_printable(item):
            str_output = '%s%s' % (
                tabchar * depth, item) + ('\n' if newline else '')
            formatter.string_format(TextFormatter.NONE, str_output, out=out)
        else:
            str_output = '%s[%d UTF-8 Bytes]' % (
                tabchar * depth, len(item)) + ('\n' if newline else '')
            formatter.string_format(
                TextFormatter.BRIGHT | TextFormatter.RED, str_output,
                out=out)
    elif teq(int):
        formatter.string_format(
            TextFormatter.CYAN, '%s%d\n' % (tabchar * depth, item),
            out=out)
    else:
        sys.exit("Don't know how to print %s" % str(item))

def decode(string_buffer):
    """Decodes a bencoded string.

    :param string_buffer: bencoded torrent file content buffer
    :type string_buffer: StringBuffer

    :returns: dict
    """
    content_type = string_buffer.peek()
    parser_map = [(re.compile('d'), dict_parse),
                  (re.compile('l'), list_parse),
                  (re.compile('[0-9]'), str_parse),
                  (re.compile('i'), int_parse)]
    for exp, parser in parser_map:
        if exp.match(content_type):
            return parser(string_buffer)
    raise UnknownTypeChar(content_type, string_buffer)


def pop_buffer(wrapped_func):
    """Decorator that pops a character before and after a function call.

    :param f: function to call between pops
    :type f: function

    :returns: function
    """
    def wrapper(string_buffer):
        """Wraps passed in func in StringBuffer get(1)s.

        :param string_buffer: StringBuffer to be used by the function
        :type string_buffer: StringBuffer

        :returns: wrapped_func(string_buffer)
        """
        string_buffer.get(1)
        parsed_struct = wrapped_func(string_buffer)
        string_buffer.get(1)
        return parsed_struct
    return wrapper

@pop_buffer
def dict_parse(string_buffer):
    """Parses a bencoded string into a dictionary.

    :param string_buffer: StringBuffer to use for parsing
    :type string_buffer: StringBuffer

    :returns: dict
    """
    tmp_dict = dict()
    while string_buffer.peek() != 'e':
        key = str_parse(string_buffer)
        tmp_dict[key] = decode(string_buffer)
    return tmp_dict

@pop_buffer
def list_parse(string_buffer):
    """Parses a bencoded string into a list.

    :param string_buffer: StringBuffer to use for parsing
    :type string_buffer: StringBuffer

    :returns: list
    """
    tmp_list = list()
    while string_buffer.peek() != 'e':
        tmp_list.append(decode(string_buffer))
    return tmp_list


def str_parse(string_buffer):
    """Parses a bencoded string into a string.

    :param string_buffer: StringBuffer to use for parsing
    :type string_buffer: StringBuffer

    :returns: str
    """
    return string_buffer.get(int(string_buffer.get_upto(':')))


def int_parse(string_buffer):
    """Parses a bencoded string into an integer.

    :param string_buffer: StringBuffer to use for parsing
    :type string_buffer: StringBuffer

    :returns: int
    """
    string_buffer.get(1)
    return int(string_buffer.get_upto('e'))


def load_torrent(filename):
    """Loads file contents from a torrent file

    :param filename: torrent file path
    :type filename: str:

    :returns: StringBuffer
    """
    handle = file(filename, 'rb')
    return StringBuffer(handle.read())

class StringBuffer:
    """String processing class."""
    def __init__(self, string):
        """Creates an instance of StringBuffer.

        :param string: string to use to create the StringBuffer
        :type string: str
        """
        self.string = string

    def is_eof(self):
        """Checks whether we're at the end of the string.

        :returns: bool -- true if this instance reached end of line
        """
        return len(self.string) == 0


    def peek(self):
        """Peeks at the next character in the string.

        :returns: str -- next character of this instance
        :raises: `BufferOverrun`
        """
        if self.is_eof():
            raise StringBuffer.BufferOverrun(1)
        return self.string[0]


    def get(self, length):
        """Gets certain amount of characters from the buffer.

        :param length: Number of characters to get from the buffer
        :type length: int

        :returns: str -- first `length` characters from the buffer
        :raises: BufferOverrun
        """
        if length > len(self.string):
            raise StringBuffer.BufferOverrun(length - len(self.string))
        segment, self.string = self.string[:length], self.string[length:]
        return segment

    def get_upto(self, character):
        """Gets all characters in a string until the specified one, exclusive.

        :param character: Character until which the string should be collected
        :type character: str

        :returns: str -- collected string from the buffer up to `character`
        :raises: CharacterExpected
        """
        string_buffer = ''
        while not self.is_eof():
            next_char = self.get(1)
            if next_char == character:
                return string_buffer
            string_buffer += next_char
        raise StringBuffer.CharacterExpected(character)

    class BufferOverrun (Exception):
        """Raised when the buffer goes past EOF."""
        pass

    class CharacterExpected (Exception):
        """Raised when the buffer doesn't find the expected character."""
        pass


def get_args():
    parser = argparse.ArgumentParser(description='Print information '
                                     + 'about torrent files')
    parser.add_argument('-b', '--basic', dest='basic', action='store_true',
                        help='Show basic file information (default)')
    parser.add_argument('-t', '--top', dest='top', action='store_true',
                        help='Only show top level file/directory')
    parser.add_argument('-f', '--files', dest='files', action='store_true',
                        help='Show files within the torrent')
    parser.add_argument('-d', '--dump', dest='dump', action='store_true',
                       help='Dump the whole file hierarchy')
    parser.add_argument('-a', '--ascii', dest='ascii', action='store_true',
                        help='Only print out ascii')
    parser.add_argument('-n', '--nocolour', dest='nocolour',
                        action='store_true', help='No ANSI colour')

    parser.add_argument('filename', type=str, metavar='filename',
                        nargs='+', help='Torrent files to process')

    return parser.parse_args()


def start_line(formatter, prefix, depth, postfix='',
               format_spec=TextFormatter.NORMAL, out=sys.stdout):
    """Print the first line during information output.

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param prefix: prefix to insert in front of the line
    :type prefix: str
    :param depth: indentation depth
    :type depth: int
    :param postfix: postfix to insert at the back of the line
    :type postfix: str
    :param format_spec: default colour to use for the text
    :type format_spec: int
    """
    formatter.string_format(TextFormatter.BRIGHT | TextFormatter.GREEN,
                            '%s%s' % (TAB_CHAR * depth, prefix), out=out)
    formatter.string_format(format_spec, '%s%s' % (TAB_CHAR, postfix), out=out)


def get_line(formatter, prefix, key, torrent, is_date=False, out=sys.stdout):
    """Print lines from a torrent instance.

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param prefix: prefix to insert in front of the line
    :type prefix: str
    :param key: key name in the torrent to print out
    :type key: str
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    :param depth: indentation depth
    :type depth: int
    :param is_date: indicates whether the line is a date
    :type is_date: bool
    :param format_spec: default colour to use for the text
    :type format_spec: int
    """
    start_line(formatter, prefix, 1, format_spec=TextFormatter.NORMAL, out=out)
    if key in torrent:
        if is_date:
            if type(torrent[key]) == int:
                dump_as_date(torrent[key], formatter, out=out)
            else:
                formatter.string_format(TextFormatter.BRIGHT |
                                        TextFormatter.RED, '[Not An Integer]',
                                        out=out)
        else:
            dump(torrent[key], formatter, '', 0, out=out)
    else:
        formatter.string_format(TextFormatter.NORMAL, '\n', out=out)

def is_ascii_only(string):
    """Checks whether a string is ascii only.

    :param string: string to check
    :type string: str

    :returns: bool
    """
    is_ascii = True
    for char in string:
        if char not in printable:
            is_ascii = False
            break
    return is_ascii


def is_printable(string):
    """Determines whether a string only contains printable characters.

    :param string: string to check for strictly printable characters
    :type string: str

    :returns: bool -- True if the string is fully printable
    """
    # Bit inefficient but ensures we can print ascii only
    is_ascii = is_ascii_only(string)

    # True if there are no Unicode escape characters in the string
    control_chars = ''.join([unichr(x) for x in
                             range(0, 32) + range(127, 160)])
    control_char_re = re.compile('[%s]' % re.escape(control_chars))
    is_unicode = control_char_re.match(string) is None

    return is_ascii or not is_unicode


def basic(formatter, torrent, out=sys.stdout):
    """Prints out basic information about a Torrent instance.

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        sys.exit('Missing "info" section in %s' % torrent.filename)
    get_line(formatter, 'name       ', 'name', torrent['info'], out=out)
    get_line(formatter, 'tracker url', 'announce', torrent, out=out)
    get_line(formatter, 'created by ', 'created by', torrent, out=out)
    get_line(formatter, 'created on ', 'creation date',
             torrent, is_date=True, out=out)


def top(formatter, torrent, out=sys.stdout):
    """Prints out the top file/directory name as well as torrent file name.

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        sys.exit('Missing "info" section in %s' % torrent.filename)
    dump(torrent['info']['name'], formatter, '', 1, newline=False, out=out)


def basic_files(formatter, torrent, out=sys.stdout):
    """Prints out basic file information of a Torrent instance.

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        sys.exit('Missing "info" section in %s' % torrent.filename)
    if not 'files' in torrent['info']:
        get_line(formatter, 'file name  ', 'name', torrent['info'], out=out)
        start_line(formatter, 'file size  ', 1, out=out)
        dump_as_size(torrent['info']['length'], formatter, '', 0, out=out)
    else:
        filestorrent = torrent['info']['files']
        numfiles = len(filestorrent)
        if numfiles > 1:
            start_line(formatter, 'num files  ', 1, '%d\n' % numfiles, out=out)
            lengths = [filetorrent['length']
                       for filetorrent in filestorrent]
            start_line(formatter, 'total size ', 1, out=out)
            dump_as_size(sum(lengths), formatter, '', 0, out=out)
        else:
            get_line(formatter, 'file name  ', 'path', filestorrent[0], out=out)
            start_line(formatter, 'file size  ', 1, out=out)
            dump_as_size(filestorrent[0]['length'], formatter, '', 0, out=out)


def list_files(formatter, torrent, detailed=False, out=sys.stdout):
    """Prints out a list of files using a Torrent instance

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        sys.exit('Missing "info" section in %s' % torrent.filename)
    start_line(formatter, 'files', 1, postfix='\n', out=out)
    if not 'files' in torrent['info']:
        formatter.string_format(TextFormatter.YELLOW |
                                TextFormatter.BRIGHT,
                                '%s%d' % (TAB_CHAR * 2, 0),
                                out=out)
        formatter.string_format(TextFormatter.NORMAL, '\n', out=out)
        dump(torrent['info']['name'], formatter, TAB_CHAR, 3, out=out)
        dump_as_size(torrent['info']['length'], formatter, TAB_CHAR, 3, out=out)
    else:
        filestorrent = torrent['info']['files']
        for index in range(len(filestorrent)):
            formatter.string_format(TextFormatter.YELLOW |
                                    TextFormatter.BRIGHT,
                                    '%s%d' % (TAB_CHAR * 2, index),
                                    out=out)

            formatter.string_format(TextFormatter.NORMAL, '\n', out=out)
            if detailed:
                for kwrd in filestorrent[index]:
                    start_line(formatter, kwrd, 3, postfix='\n', out=out)
                    dump(filestorrent[index][kwrd], formatter, TAB_CHAR, 4,
                         out=out)
            else:
                if type(filestorrent[index]['path']) == str:
                    dump(filestorrent[index]['path'], formatter, TAB_CHAR, 3,
                         out=out)
                else:
                    dump(os.path.join(*filestorrent[index]['path']),
                         formatter, TAB_CHAR, 3, out=out)
                    dump_as_size(filestorrent[index]['length'],
                                 formatter, TAB_CHAR, 3, out=out)

    if detailed:
        start_line(formatter, 'piece length', 1, postfix='\n', out=out)
        dump(torrent['info']['piece length'], formatter, TAB_CHAR, 3, out=out)
        start_line(formatter, 'pieces', 1, postfix='\n', out=out)
        dump(torrent['info']['pieces'], formatter, TAB_CHAR, 3, out=out)


def main():
    """Main control flow function used to encapsulate initialisation."""
    try:
        args = get_args()
        formatter = TextFormatter(not args.nocolour)

        for filename in args.filename:
            try:
                torrent = Torrent(filename, load_torrent(filename))
                formatter.string_format(TextFormatter.BRIGHT, '%s\n' %
                                        os.path.basename(torrent.filename))
                if not args.basic:
                    if args.dump:
                        list_files(formatter, torrent, detailed=True)
                    elif args.files:
                        basic(formatter, torrent)
                        list_files(formatter, torrent, detailed=False)
                    elif args.top:
                        top(formatter, torrent)
                else:
                    basic(formatter, torrent)
                    basic_files(formatter, torrent)
                formatter.string_format(TextFormatter.NORMAL, '\n')
            except UnknownTypeChar:
                sys.stderr.write(
                    'Could not parse %s as a valid torrent file.\n' % filename)
    except SystemExit, message:
        sys.exit(message)
    except KeyboardInterrupt:
        pass



if __name__ == "__main__":
    main()
