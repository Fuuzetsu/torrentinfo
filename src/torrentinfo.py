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
    """Class used to provide hex colour codes."""
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

    def string_format(self, format_spec, string=''):
        """Sends a string to output.

        :param format_spec: format parameter used by extending classes
        :type format_spec: int
        :param string: string to output
        :type string: str
        """
        self.output(string)

    def output(self, string):
        """Outputs a string to stdout.

        :param string: string to output
        :type string: str
        """
        sys.stdout.write(string)


class ANSIColour (TextFormatter):
    """Provides a map from colour values to terminal escape codes."""
    escape = chr(0x1b)
    mapping = [(TextFormatter.NORMAL, '[0m'),
               (TextFormatter.BRIGHT, '[1m'),
               (TextFormatter.DULL, '[22m'),
               (TextFormatter.WHITE, '[37m'),
               (TextFormatter.GREEN, '[32m'),
               (TextFormatter.CYAN, '[36m'),
               (TextFormatter.YELLOW, '[33m'),
               (TextFormatter.RED, '[31m'),
               (TextFormatter.MAGENTA, '[35m'), ]

    def string_format(self, format_spec, string=''):
        """Attaches colour codes to strings before outputting them.

        :param format_spec: value of the colour code
        :type format_spec: int
        :param string: string to colour
        :type string: str
        """
        codestring = ''
        for name, code in ANSIColour.mapping:
            if format_spec & name:
                codestring += ANSIColour.escape + code
        self.output(codestring + string)


def decode(string_buffer):
    """Returns a de-bencoded dictionary.

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


def dict_parse(string_buffer):
    string_buffer.get(1)
    d = dict()
    while string_buffer.peek() != 'e':
        key = str_parse(string_buffer)
        d[key] = decode(string_buffer)
    string_buffer.get(1)
    return d


def list_parse(string_buffer):
    string_buffer.get(1)
    l = ''.join([decode(string_buffer) for x in string_buffer.peek() if x != 'e'])
    string_buffer.get(1)
    return l


def str_parse(string_buffer):
    length = int(string_buffer.get_upto(':'))
    return string_buffer.get(length)


def int_parse(string_buffer):
    string_buffer.get(1)
    return int(string_buffer.get_upto('e'))



class UnknownTypeChar(Exception):
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

    # def is_eof(self):
    #     """Checks whether we're at the end of the string.

    #     :returns: bool -- true if this instance reached end of line
    #     """
    #     return self.index >= len(self.string)

    def is_eof(self):
        """Checks whether we're at the end of the string.

        :returns: bool -- true if this instance reached end of line
        """
        return len(self.string) == 0

    # def peek(self):
    #     """Peeks at the next character in the string.

    #     :returns: str -- next character of this instance
    #     :raises: `BufferOverrun`
    #     """
    #     if self.is_eof():
    #         raise StringBuffer.BufferOverrun(1)
    #     return self.string[self.index]
    def peek(self):
        """Peeks at the next character in the string.

        :returns: str -- next character of this instance
        :raises: `BufferOverrun`
        """
        if self.is_eof():
            raise StringBuffer.BufferOverrun(1)
        return self.string[0]

    # def get(self, length):
    #     """Gets certain amount of characters from the buffer.

    #     :param length: Number of characters to get from the buffer
    #     :type length: int

    #     :returns: str -- first `length` characters from the buffer
    #     :raises: BufferOverrun
    #     """
    #     last = self.index + length
    #     if last > len(self.string):
    #         raise StringBuffer.BufferOverrun(last - len(self.string))
    #     segment = self.string[self.index: last]
    #     self.index = last
    #     return segment

    def get(self, length): # destructive
        """Gets certain amount of characters from the buffer.

        :param length: Number of characters to get from the buffer
        :type length: int

        :returns: str -- first `length` characters from the buffer
        :raises: BufferOverrun
        """
        if length > len(self.string):
            raise StringBuffer.BufferOverrun(length - len(self.string))
        segment = self.string[:length]
        self.string = self.string[length:]
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


def get_formatter(nocolour):
    """Chooses a text formatter to use throughout the application.

    :param nocolour: determines whether we want the formatter to colour text
    :type nocolour: bool

    :returns: TextFormatter
    """
    return {True: TextFormatter, False: ANSIColour}[nocolour]()


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
            if torrent[key].__class__ is Integer:
                torrent[key].dump_as_date(formatter)
            else:
                formatter.string_format(TextFormatter.BRIGHT |
                                        TextFormatter.RED, '[Not An Integer]')
        else:
            torrent[key].dump(formatter, '', 0)
    else:
        formatter.string_format(TextFormatter.NORMAL, '\n')


def dump(formatter, torrent):
    """Prints out Torrent instance data using `Torrent.dump`.

    :param formatter: text formatter to use
    :type formatter: TextFormatter
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    torrent.dump(formatter, TAB_CHAR, 1)


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
    get_line(
        formatter, 'created on ', 'creation date', torrent, is_date=True)


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
        torrent['info']['length'].dump_as_size(formatter, '', 0)
    else:
        filestorrent = torrent['info']['files']
        numfiles = len(filestorrent)
        if numfiles > 1:
            start_line(formatter, 'num files  ', 1, '%d\n' % numfiles)
            lengths = [filetorrent['length']
                       for filetorrent in filestorrent]
            start_line(formatter, 'total size ', 1)
            reduce(
                lambda x, y: x + y, lengths).dump_as_size(formatter, '', 0)
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
        torrent['info']['name'].dump(formatter, TAB_CHAR, 3)
        torrent['info']['length'].dump_as_size(formatter, TAB_CHAR, 3)
    else:
        filestorrent = torrent['info']['files']
        for index in range(len(filestorrent)):
            formatter.string_format(TextFormatter.YELLOW |
                                    TextFormatter.BRIGHT,
                                    '%s%d' % (TAB_CHAR * 2, index))
            formatter.string_format(TextFormatter.NORMAL, '\n')
            if filestorrent[index]['path'].__class__ is String:
                filestorrent[index]['path'].dump(formatter, TAB_CHAR, 3)
            else:
                filestorrent[index]['path'].join(
                    os.path.sep).dump(formatter, TAB_CHAR, 3)
            filestorrent[index]['length'].dump_as_size(
                formatter, TAB_CHAR, 3)

def main():
    """Main control flow function used to encapsulate initialisation."""
    try:
        settings, filenames = get_commandline_arguments(
            os.path.basename(sys.argv[0]), sys.argv[1:])
        formatter = get_formatter('nocolour' in settings)
        if 'nocolour' in settings:
            del settings['nocolour']
        if 'ascii' in settings:
            String.asciionly = True
            del settings['ascii']

        for filename in filenames:
            # try:
            torrent = load_torrent(filename)
            print decode(torrent)
            sys.exit(0)
            #     formatter.string_format(TextFormatter.BRIGHT, '%s\n' %
            #                             os.path.basename(torrent.filename))
            #     if settings and not 'basic' in settings:
            #         if 'dump' in settings:
            #             dump(formatter, torrent)
            #         elif 'files' in settings:
            #             basic(formatter, torrent)
            #             list_files(formatter, torrent)
            #         elif 'top' in settings:
            #             top(formatter, torrent)
            #     else:
            #         basic(formatter, torrent)
            #         basic_files(formatter, torrent)
            #     formatter.string_format(TextFormatter.NORMAL, '\n')
            # except Torrent.UnknownTypeChar:
            #     sys.stderr.write(
            #         'Could not parse %s as a valid torrent file.\n' % filename)
    except SystemExit, message:
        sys.exit(message)
    except KeyboardInterrupt:
        pass



if __name__ == "__main__":
    main()
