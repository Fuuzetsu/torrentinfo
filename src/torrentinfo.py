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
import getopt
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

    def string_format(self, format_spec, string=''):
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
            sys.stdout.write(codestring + string)
        else:
            sys.stdout.write(string)


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

def dump_as_date(number, formatter):
    """Dumps out the Integer instance as a date.

    :param n: number to format
    :type n: int
    :param formatter: formatter to use for string formatting
    :type formatter: TextFormatter
    """
    formatter.string_format(TextFormatter.MAGENTA, time.strftime(
            '%Y/%m/%d %H:%M:%S %Z\n', time.gmtime(number)))

def dump_as_size(number, formatter, tabchar, depth):
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
    while size > 1024 and len(sizes) > 1:
        size /= 1024
        sizes = sizes[1:]
    formatter.string_format(TextFormatter.CYAN, '%s%.1f%s\n' % (
            tabchar * depth, size + 0.05, sizes[0]))


def dump(item, formatter, tabchar, depth, newline=True):
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
            formatter.string_format(TextFormatter.NORMAL | TextFormatter.GREEN)

            if depth < 2:
                formatter.string_format(TextFormatter.BRIGHT)

            dump(key, formatter, tabchar, depth)
            formatter.string_format(TextFormatter.NORMAL)
            dump(item[key], formatter, tabchar, depth + 1)
    elif teq(list):
        if len(item) == 1:
            dump(item[0], formatter, tabchar, depth)
        else:
            for index in range(len(item)):
                formatter.string_format(TextFormatter.BRIGHT |
                                        TextFormatter.YELLOW,
                                        '%s%d\n' % (tabchar * depth, index))
                formatter.string_format(TextFormatter.NORMAL)
                dump(item[index], formatter, tabchar, depth + 1)
    elif teq(str):
        if is_printable(item):
            str_output = '%s%s' % (
                tabchar * depth, item) + ('\n' if newline else '')
            formatter.string_format(TextFormatter.NONE, str_output)
        else:
            str_output = '%s[%d UTF-8 Bytes]' % (
                tabchar * depth, len(item)) + ('\n' if newline else '')
            formatter.string_format(
                TextFormatter.BRIGHT | TextFormatter.RED, str_output)
    elif teq(int):
        formatter.string_format(
            TextFormatter.CYAN, '%s%d\n' % (tabchar * depth, item))
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
    print string_buffer.string
    raise UnknownTypeChar(content_type, string_buffer)


def pop_buffer(wrapped_func):
    """Decorator that pops a character before and after a function call.

    :param f: function to call between pops
    :type f: function

    :returns: f(*args)
    """
    def wrapper(string_buffer):
        """Wraps passed in func in StringBuffer get(1)s."""
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


class UnknownTypeChar(Exception):
   """Thrown when Torrent.parse encounters unexpected character"""
   pass


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
        self.index = 0

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


def get_commandline_arguments(appname, arguments):
    """Parses the commandline arguments using :mod:`getopt`.

    :param appname: name of the application
    :type appname: str
    :param arguments: list of arguments from the commandline
    :type arguments: list of str

    :returns: (dict, list) -- the list contains any trailing, unparsed args
    """
    try:
        options, arguments = getopt.gnu_getopt(
            arguments, 'hndbtfa', ['help', 'nocolour', 'dump',
                                   'basic', 'top', 'files', 'ascii'])
    except getopt.GetoptError:
        show_usage(appname)

    if not arguments:
        show_usage(appname)
    optionsmap = [(('-n', '--nocolour'), 'nocolour'),
                  (('-d', '--dump'), 'dump'),
                  (('-b', '--basic'), 'basic'),
                  (('-t', '--top'), 'top'),
                  (('-f', '--files'), 'files'),
                  (('-a', '--ascii'), 'ascii')]
    setoptions = {}
    for option, value in options:
        if option in ['-h', '--help']:
            show_usage(appname)
        for switches, key in optionsmap:
            if option in switches:
                setoptions[key] = value

    return setoptions, arguments


def show_usage(appname):
    """Exits the application while printing the help.

    :param appname: name of the application
    :type appname: str
    """
    sys.exit('%s [ -h -n ] filename1 [ ... filenameN ]\n\n' % appname +
             '    -h --help      Displays this message\n' +
             '    -b --basic     Shows basic file information (default)\n' +
             '    -t --top       Shows only the top level file/directory\n' +
             '    -f --files     Shows files within the torrent\n' +
             '    -d --dump      Dumps the whole file hierarchy\n' +
             '    -a --ascii     Only prints out ascii\n' +
             '    -n --nocolour  No ANSI colour\n')


def start_line(formatter, prefix, depth, postfix='',
               format_spec=TextFormatter.NORMAL):
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
                            '%s%s' % (TAB_CHAR * depth, prefix))
    formatter.string_format(format_spec, '%s%s' % (TAB_CHAR, postfix))


def get_line(formatter, prefix, key, torrent, depth=1, is_date=False,
             format_spec=TextFormatter.NORMAL):
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
    start_line(formatter, prefix, depth, format_spec=format_spec)
    if key in torrent:
        if is_date:
            if type(torrent[key]) == int:
                dump_as_date(torrent[key], formatter)
            else:
                formatter.string_format(TextFormatter.BRIGHT |
                                        TextFormatter.RED, '[Not An Integer]')
        else:
            dump(torrent[key], formatter, '', 0)
    else:
        formatter.string_format(TextFormatter.NORMAL, '\n')

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


def basic(formatter, torrent):
    """Prints out basic information about a Torrent instance.

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        sys.exit('Missing "info" section in %s' % torrent.filename)
    get_line(formatter, 'name       ', 'name', torrent['info'])
    get_line(formatter, 'tracker url', 'announce', torrent)
    get_line(formatter, 'created by ', 'created by', torrent)
    get_line(formatter, 'created on ', 'creation date',
             torrent, is_date=True)


def top(formatter, torrent):
    """Prints out the top file/directory name as well as torrent file name.

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        sys.exit('Missing "info" section in %s' % torrent.filename)
    torrent['info']['name'].dump(formatter, '', 1, newline=False)


def basic_files(formatter, torrent):
    """Prints out basic file information of a Torrent instance.

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        sys.exit('Missing "info" section in %s' % torrent.filename)
    if not 'files' in torrent['info']:
        get_line(formatter, 'file name  ', 'name', torrent['info'])
        start_line(formatter, 'file size  ', 1)
        dump_as_size(torrent['info']['length'], formatter, '', 0)
    else:
        filestorrent = torrent['info']['files']
        numfiles = len(filestorrent)
        if numfiles > 1:
            start_line(formatter, 'num files  ', 1, '%d\n' % numfiles)
            lengths = [filetorrent['length']
                       for filetorrent in filestorrent]
            start_line(formatter, 'total size ', 1)
            dump_as_size(sum(lengths), formatter, '', 0)
        else:
            get_line(formatter, 'file name  ', 'path', filestorrent[0])
            start_line(formatter, 'file size  ', 1)
            filestorrent[0]['length'].dump_as_size(formatter, '', 0)


def list_files(formatter, torrent):
    """Prints out a list of files using a Torrent instance

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        sys.exit('Missing "info" section in %s' % torrent.filename)
    start_line(formatter, 'files', 1, postfix='\n')
    if not 'files' in torrent['info']:
        formatter.string_format(TextFormatter.YELLOW |
                                TextFormatter.BRIGHT,
                                '%s%d' % (TAB_CHAR * 2, 0))
        formatter.string_format(TextFormatter.NORMAL, '\n')
        dump(torrent['info']['name'], formatter, TAB_CHAR, 3)
        dump_as_size(torrent['info']['length'], formatter, TAB_CHAR, 3)
    else:
        filestorrent = torrent['info']['files']
        for index in range(len(filestorrent)):
            formatter.string_format(TextFormatter.YELLOW |
                                    TextFormatter.BRIGHT,
                                    '%s%d' % (TAB_CHAR * 2, index))
            formatter.string_format(TextFormatter.NORMAL, '\n')
            if type(filestorrent[index]['path']) == str:
                dump(filestorrent[index]['path'], formatter, TAB_CHAR, 3)
            else:
                dump(os.path.join(*filestorrent[index]['path']),
                     formatter, TAB_CHAR, 3)
            dump_as_size(filestorrent[index]['length'],
                formatter, TAB_CHAR, 3)


def main():
    """Main control flow function used to encapsulate initialisation."""
    try:
        settings, filenames = get_commandline_arguments(
            os.path.basename(sys.argv[0]), sys.argv[1:])
        formatter = TextFormatter('nocolour' not in settings)
        if 'nocolour' in settings:
            del settings['nocolour']
        if 'ascii' in settings:
            del settings['ascii']

        for filename in filenames:
            try:
                torrent = Torrent(filename, load_torrent(filename))
                formatter.string_format(TextFormatter.BRIGHT, '%s\n' %
                                        os.path.basename(torrent.filename))
                if settings and not 'basic' in settings:
                    if 'dump' in settings:
                        dump(formatter, torrent)
                    elif 'files' in settings:
                        basic(formatter, torrent)
                        list_files(formatter, torrent)
                    elif 'top' in settings:
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
