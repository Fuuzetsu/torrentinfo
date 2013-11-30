#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of torrentinfo.
#
# torrentinfo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# torrentinfo is distributed in the hope that it will be useful,
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
import time

#  see pylint ticket #2481
from string import printable  # pylint: disable-msg=W0402

VERSION = '1.8.6'

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

    def string_format(self, format_spec, config, string=''):
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
            config.out.write(codestring + string)
        else:
            config.out.write(string)

class Config:
    """Class storing configuration propagated throughout the program."""

    def __init__(self, formatter, out=sys.stdout,
                 err=sys.stderr, tab_char='    '):
        """Initialises a config class.

        :param formatter: formatter to use when printing
        :type formatter: TextFormatter
        :param out: default output destination
        :type out: file
        :param err: default error destination
        :type err: file
        :param tab_char: character to use as a tab
        :type tab_char: str
        """
        self.formatter = formatter
        self.out = out
        self.err = err
        self.tab_char = tab_char


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

def dump_as_date(number, config):
    """Dumps out the Integer instance as a date.

    :param n: number to format
    :type n: int
    :param config: configuration object to use in this method
    :type config: Config
    """
    config.formatter.string_format(TextFormatter.MAGENTA, config,
                                   time.strftime(
                                       '%Y/%m/%d %H:%M:%S %Z\n',
                                       time.gmtime(number)))

def dump_as_size(number, config, depth):
    """Dumps the string to the stdout as file size after formatting it.

    :param n: number to format
    :type n: int
    :param config: configuration object to use in this method
    :type config: Config
    :param depth: indentation depth
    :type depth: int
    """
    size = float(number)
    sizes = ['B', 'KB', 'MB', 'GB']
    while size >= 1024 and len(sizes) > 1:
        size /= 1024
        sizes = sizes[1:]
    config.formatter.string_format(TextFormatter.CYAN, config,
                                   '%s%.1f%s\n' % (
                                       config.tab_char * depth,
                                       size, sizes[0]))



def dump(item, config, depth, newline=True, as_utf_repr=False):
    """Printing method.

    :param item: item to print
    :type item: dict or list or str or int
    :param config: configuration object to use in this method
    :type config: Config
    :param depth: indentation depth
    :type depth: int
    :param newline: indicates whether to insert a newline after certain strings
    :type newline: bool
    :param as_utf_repr: indicates whether only ASCII should be printed
    :type as_utf_repr: bool
    """
    def teq(comp_type):
        """Helper that checks for type equality."""
        return type(item) == comp_type

    if teq(dict) or teq(Torrent):
        for key in sorted(item):
            config.formatter.string_format(
                TextFormatter.NORMAL | TextFormatter.GREEN, config)

            if depth < 2:
                config.formatter.string_format(TextFormatter.BRIGHT, config)

            dump(key, config, depth, as_utf_repr=as_utf_repr)
            config.formatter.string_format(TextFormatter.NORMAL, config)
            if key == 'pieces':
                dump(item[key], config, depth + 1, as_utf_repr=True)
            else:
                dump(item[key], config, depth + 1, as_utf_repr=as_utf_repr)
    elif teq(list):
        if len(item) == 1:
            dump(item[0], config, depth, as_utf_repr=as_utf_repr)
        else:
            for index in range(len(item)):
                config.formatter.string_format(TextFormatter.BRIGHT |
                                               TextFormatter.YELLOW,
                                               config,
                                               '%s%d\n' % (config.tab_char
                                                           * depth, index))
                config.formatter.string_format(TextFormatter.NORMAL, config)
                dump(item[index], config, depth + 1, as_utf_repr=as_utf_repr)
    elif teq(str):
        if is_ascii_only(item) or not as_utf_repr:
            str_output = '%s%s' % (
                config.tab_char * depth, item) + ('\n' if newline else '')
            config.formatter.string_format(TextFormatter.NONE,
                                           config, str_output)
        else:
            str_output = '%s[%d UTF-8 Bytes]' % (
                config.tab_char * depth, len(item)) + ('\n' if newline else '')
            config.formatter.string_format(
                TextFormatter.BRIGHT | TextFormatter.RED, config, str_output)
    elif teq(int):
        config.formatter.string_format(
            TextFormatter.CYAN, config,
            '%s%d\n' % (config.tab_char * depth, item))

    else:
        config.err.write("Don't know how to print %s" % str(item))
        sys.exit(1)

def decode(string_buffer):
    """Decodes a bencoded string.

    :param string_buffer: bencoded torrent file content buffer
    :type string_buffer: StringBuffer

    :returns: dict
    """
    content_type = string_buffer.peek()

    if content_type == 'd':
        string_buffer.get(1)
        tmp_dict = dict()
        while string_buffer.peek() != 'e':
            key = string_buffer.get(int(string_buffer.get_upto(':')))
            tmp_dict[key] = decode(string_buffer)
        string_buffer.get(1)
        return tmp_dict
    elif content_type == 'l':
        string_buffer.get(1)
        tmp_list = list()
        while string_buffer.peek() != 'e':
            tmp_list.append(decode(string_buffer))
        string_buffer.get(1)
        return tmp_list
    elif content_type == 'i':
        string_buffer.get(1)
        return int(string_buffer.get_upto('e'))
    elif content_type in [str(x) for x in range(0, 10)]:
        return string_buffer.get(int(string_buffer.get_upto(':')))

    raise UnknownTypeChar(content_type, string_buffer)


def load_torrent(filename):
    """Loads file contents from a torrent file

    :param filename: torrent file path
    :type filename: str:

    :returns: StringBuffer
    """
    file_value = open(filename, 'rb').read()
    if len(file_value) == 0:
        raise UnknownTypeChar('', StringBuffer(''))

    return StringBuffer(file_value)

class StringBuffer:
    """String processing class."""
    def __init__(self, string):
        """Creates an instance of StringBuffer.

        :param string: string to use to create the StringBuffer
        :type string: str
        """
        self.string = string
        self.string_length = len(self.string)
        self.taken = 0

    def unicode_get(self, length, destructive=True, replacement='×'):
        """A get method called when bytes are encountered. Casts into unicode
        where at all possible or uses the replacement character otherwise.


        :param length: number of characters to get from the buffer
        :type length: int
        :param destructive: decides whether to progress the buffer
        :type destructive: bool
        :param replacement: Replacement to use character if unicode decode fails
        :type replacement: str

        :returns: str -- Unicode string from the string buffer
        """
        if self.is_eof():
            raise StringBuffer.BufferOverrun(1)
        if length > self.string_length - self.taken:
            raise StringBuffer.BufferOverrun(length - (self.string_length - self.taken))
        try:
            ret_val = self.string[self.taken : self.taken + length]
            if destructive:
                self.taken += length
            if type(ret_val) == str:
                return ret_val
            return ret_val.decode('utf-8')
        except UnicodeDecodeError:
            return replacement * length


    def is_eof(self):
        """Checks whether we're at the end of the string.

        :returns: bool -- true if this instance reached end of line
        """
        return self.taken >= self.string_length


    def peek(self):
        """Peeks at the next character in the string.

        :returns: str -- next character of this instance
        :raises: `BufferOverrun`
        """
        return self.unicode_get(1, destructive=False)

    def get(self, length):
        """Gets certain amount of characters from the buffer.

        :param length: Number of characters to get from the buffer
        :type length: int

        :returns: str -- first `length` characters from the buffer
        :raises: BufferOverrun
        """
        return self.unicode_get(length)

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


def get_arg_parser():
    """Parses command-line arguments.

    :returns: ArgumentParser
    """
    parser = argparse.ArgumentParser(description='Print information '
                                     + 'about torrent files')
    parser.add_argument('-v', '--version', action='version',
                        version='torrentinfo %s' % VERSION,
                        help='Print version and quit')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-t', '--top', dest='top', action='store_true',
                        help='Only show top level file/directory')
    group.add_argument('-f', '--files', dest='files', action='store_true',
                        help='Show files within the torrent')
    group.add_argument('-d', '--detailed', dest='detailed', action='store_true',
                       help='Print more information about the files')
    group.add_argument('-e', '--everything', dest='everything',
                       action='store_true',
                       help='Print everything we can about the torrent')
    parser.add_argument('-a', '--ascii', dest='ascii', action='store_true',
                        help='Only print out ascii')
    parser.add_argument('-n', '--nocolour', dest='nocolour',
                        action='store_true', help='No ANSI colour')
    parser.add_argument('filename', type=str, metavar='filename',
                        nargs='+', help='Torrent files to process')

    return parser


def start_line(config, prefix, depth, postfix='',
               format_spec=TextFormatter.NORMAL):
    """Print the first line during information output.

    :param config: configuration object to use in this method
    :type config: Config
    :param prefix: prefix to insert in front of the line
    :type prefix: str
    :param depth: indentation depth
    :type depth: int
    :param postfix: postfix to insert at the back of the line
    :type postfix: str
    :param format_spec: default colour to use for the text
    :type format_spec: int
    """
    config.formatter.string_format(TextFormatter.BRIGHT | TextFormatter.GREEN,
                                   config, '%s%s'
                                   % (config.tab_char * depth, prefix))
    config.formatter.string_format(format_spec, config, '%s%s'
                                   % (config.tab_char, postfix))


def get_line(config, prefix, key, torrent, is_date=False):
    """Print lines from a torrent instance.

    :param config: configuration object to use in this method
    :type config: Config
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
    start_line(config, prefix, 1, format_spec=TextFormatter.NORMAL)
    if key in torrent:
        if is_date:
            if type(torrent[key]) == int:
                dump_as_date(torrent[key], config)
            else:
                config.formatter.string_format(TextFormatter.BRIGHT |
                                               TextFormatter.RED, config,
                                               '[Not An Integer]')
        else:
            local_config = Config(config.formatter,
                                  out=config.out, err=config.err,
                                  tab_char = '')
            dump(torrent[key], local_config, 0)
    else:
        config.formatter.string_format(TextFormatter.NORMAL, config, '\n')

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


def basic(config, torrent):
    """Prints out basic information about a Torrent instance.

    :param config: configuration object to use in this method
    :type config: Config
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        config.err.write('Missing "info" section in %s' % torrent.filename)
        sys.exit(1)
    get_line(config, 'name       ', 'name', torrent['info'])
    get_line(config, 'comment    ', 'comment', torrent)
    get_line(config, 'tracker url', 'announce', torrent)
    get_line(config, 'created by ', 'created by', torrent)
    get_line(config, 'created on ', 'creation date',
             torrent, is_date=True)


def top(config, torrent):
    """Prints out the top file/directory name as well as torrent file name.

    :param config: configuration object to use in this method
    :type config: Config
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        config.err.write('Missing "info" section in %s' % torrent.filename)
        sys.exit(1)

    local_config = Config(config.formatter,
                          out=config.out, err=config.err,
                          tab_char = '')
    dump(torrent['info']['name'], local_config, 1, newline=False)


def basic_files(config, torrent):
    """Prints out basic file information of a Torrent instance.

    :param config: configuration object to use in this method
    :type config: Config
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    """
    if not 'info' in torrent:
        config.err.write('Missing "info" section in %s' % torrent.filename)
        sys.exit(1)

    local_config = Config(config.formatter,
                          out=config.out, err=config.err,
                          tab_char = '')
    if not 'files' in torrent['info']:
        get_line(config, 'file name  ', 'name', torrent['info'])
        start_line(config, 'file size  ', 1)
        dump_as_size(torrent['info']['length'], local_config, 0)
    else:
        filestorrent = torrent['info']['files']
        numfiles = len(filestorrent)
        if numfiles > 1:
            start_line(config, 'num files  ', 1, '%d\n' % numfiles)
            lengths = [filetorrent['length']
                       for filetorrent in filestorrent]
            start_line(config, 'total size ', 1)
            dump_as_size(sum(lengths), local_config, 0)
        else:
            get_line(config, 'file name  ', 'path', filestorrent[0])
            start_line(config, 'file size  ', 1)
            dump_as_size(filestorrent[0]['length'], local_config, 0)


def list_files(config, torrent, detailed=False):
    """Prints out a list of files using a Torrent instance

    :param config: configuration object to use in this method
    :type config: Config
    :param torrent: torrent instance to use for information
    :type torrent: Torrent
    :param detailed: indicates whether to print more information about files
    :param detailed: bool
    """
    if not 'info' in torrent:
        config.err.write('Missing "info" section in %s' % torrent.filename)
        sys.exit(1)
    start_line(config, 'files', 1, postfix='\n')
    if not 'files' in torrent['info']:
        config.formatter.string_format(TextFormatter.YELLOW |
                                TextFormatter.BRIGHT, config,
                                '%s%d' % (config.tab_char * 2, 0))
        config.formatter.string_format(TextFormatter.NORMAL, config, '\n')
        dump(torrent['info']['name'], config, 3)
        dump_as_size(torrent['info']['length'], config, 3)
    else:
        filestorrent = torrent['info']['files']
        for index in range(len(filestorrent)):
            config.formatter.string_format(TextFormatter.YELLOW |
                                           TextFormatter.BRIGHT,
                                           config,
                                           '%s%d' % (config.tab_char * 2,
                                                     index))


            config.formatter.string_format(TextFormatter.NORMAL, config, '\n')
            if detailed:
                for kwrd in filestorrent[index]:
                    start_line(config, kwrd, 3, postfix='\n')
                    dump(filestorrent[index][kwrd], config, 4)
            else:
                if type(filestorrent[index]['path']) == str:
                    dump(filestorrent[index]['path'], config, 3)

                else:
                    dump(os.path.join(*filestorrent[index]['path']),
                         config, 3)
                    dump_as_size(filestorrent[index]['length'],
                                 config, 3)

    if detailed:
        start_line(config, 'piece length', 1, postfix='\n')
        dump(torrent['info']['piece length'], config, 3)
        start_line(config, 'pieces', 1, postfix='\n')
        dump(torrent['info']['pieces'], config, 3, as_utf_repr=True)


def main(alt_args=None, out=sys.stdout, err=sys.stderr):
    """Main control flow function used to encapsulate initialisation."""
    try:
        args = get_arg_parser().parse_args() if alt_args is None else alt_args
        formatter = TextFormatter(not args.nocolour)
        config = Config(formatter, out=out, err=err, tab_char='    ')
        for filename in args.filename:
            try:
                torrent = Torrent(filename, load_torrent(filename))
                config.formatter.string_format(TextFormatter.BRIGHT, config,
                                               '%s\n' % os.path.basename(
                                                   torrent.filename))

                if args.everything:
                    dump(torrent, config, 1)
                elif args.detailed:
                    list_files(config, torrent, detailed=True)
                elif args.files:
                    basic(config, torrent)
                    list_files(config, torrent, detailed=False)
                elif args.top:
                    top(config, torrent)
                else:
                    basic(config, torrent)
                    basic_files(config, torrent)
                config.formatter.string_format(TextFormatter.NORMAL,
                                               config, '\n')
            except UnknownTypeChar:
                err.write(
                    'Could not parse %s as a valid torrent file.\n' % filename)
                sys.exit(1)
    except KeyboardInterrupt:
        pass



if __name__ == "__main__":
    main()
