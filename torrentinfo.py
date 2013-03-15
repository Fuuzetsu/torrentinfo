#!/usr/bin/env python
"""
TORRENTINFO - Parses .torrent files and displays various summaries of the
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

    def __init__(self):
        pass

    def string_format(self, format_spec, string=''):
        self.output(string)

    def output(self, string):
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
        codestring = ''
        for name, code in ANSIColour.mapping:
            if format_spec & name:
                codestring += ANSIColour.escape + code
        self.output(codestring + string)


class StringBuffer:
    """String processing class."""
    def __init__(self, string):
        self.string = string
        self.index = 0

    def is_eof(self):
        return self.index >= len(self.string)

    def peek(self):
        if self.is_eof():
            raise StringBuffer.BufferOverrun(1)
        return self.string[self.index]

    def get(self, length):
        last = self.index + length
        if last > len(self.string):
            raise StringBuffer.BufferOverrun(last - len(self.string))
        segment = self.string[self.index: last]
        self.index = last
        return segment

    def get_upto(self, character):
        string_buffer = ''
        while not self.is_eof():
            next_char = self.get(1)
            if next_char == character:
                return string_buffer
            string_buffer += next_char
        raise StringBuffer.CharacterExpected(character)

    class BufferOverrun (Exception):
        pass

    class CharacterExpected (Exception):
        pass


class Torrent:
    """Class modelling a torrent file."""
    def __init__(self, filename, string):
        # Should contain only one object, a dictionary
        self.filename = filename
        self.value = Torrent.parse(string)
        if not self.value.__class__ is Dictionary:
            raise UnexpectedType(self.value__class__, Dictionary)

    def dump(self, formatter, tabchar, depth=0):
        self.value.dump(formatter, tabchar, depth)

    def __getitem__(self, key):
        return self.value[key]

    def __contains__(self, key):
        return key in self.value

    def parse(string):
        content_type = string.peek()
        for exp, parser in TYPE_MAP:
            if exp.match(content_type):
                return parser(string)
        raise Torrent.UnknownTypeChar(content_type, string)

    def load_torrent(filename):
        handle = file(filename, 'rb')
        return Torrent(filename, StringBuffer(handle.read()))

    parse = staticmethod(parse)
    load_torrent = staticmethod(load_torrent)

    class UnknownTypeChar (Exception):
        pass

    class UnexpectedType (Exception):
        pass


class String:
    """Class representing a string in a torrent file."""
    # A static variable is really the easiest way to implement this without
    # large changes
    asciionly = False

    def __init__(self, string):
        # Length, colon and then content
        self.length = int(string.get_upto(':'))
        self.value = string.get(self.length)
        self.isprintable = String.is_printable(self)

    def dump(self, formatter, tabchar, depth, newline=True):
        if self.isprintable:
            output = '%s%s' % (
                tabchar * depth, self.value) + ('\n' if newline else '')
            formatter.string_format(TextFormatter.NONE, output)
        else:
            output = '%s[%d UTF-8 Bytes]' % (
                tabchar * depth, self.length) + ('\n' if newline else '')
            formatter.string_format(
                TextFormatter.BRIGHT | TextFormatter.RED, output)

    def __cmp__(self, other):
        return cmp(self.value, other.value)

    def __hash__(self):
        return hash(self.value)

    def __add__(self, value):
        string = self.value + value.value
        return String(StringBuffer('%d:%s' % (len(string), string)))

    def is_printable(string):
        # Bit inefficient but ensures we can print ascii only
        isascii = True
        for char in string.value:
            if char not in printable:
                isascii = False
                break

        # True if there are no Unicode escape characters in the string
        control_chars = ''.join([unichr(x) for x in
                                 range(0, 32) + range(127, 160)])
        control_char_re = re.compile('[%s]' % re.escape(control_chars))
        isunicode = True if control_char_re.match(
            string.value) is None else False

        return isascii if String.asciionly else isunicode

    is_printable = staticmethod(is_printable)


class Integer:
    """Class representing an integer in a torrent file."""
    def __init__(self, string):
        # Prefix char, then base 10 integers until e is hit
        string.get(1)
        self.value = int(string.get_upto('e'))

    def dump(self, formatter, tabchar, depth):
        formatter.string_format(
            TextFormatter.CYAN, '%s%d\n' % (tabchar * depth, self.value))

    def dump_as_date(self, formatter):
        formatter.string_format(TextFormatter.MAGENTA, time.strftime(
            '%Y/%m/%d %H:%M:%S %Z\n', time.gmtime(self.value)))

    def dump_as_size(self, formatter, tabchar, depth):
        size = float(self.value)
        sizes = ['B', 'KB', 'MB', 'GB']
        while size > 1024 and len(sizes) > 1:
            size /= 1024
            sizes = sizes[1:]
        formatter.string_format(TextFormatter.CYAN, '%s%.1f%s\n' % (
            tabchar * depth, size + 0.05, sizes[0]))

    def __add__(self, value):
        return Integer(StringBuffer('i%de' % (self.value + value.value)))


class Dictionary:
    """Class representing a dictionary in a torrent file."""
    def __init__(self, string):
        # Prefix char, then list of alternation string, object pairs until an
        # 'e' is hit
        string.get(1)
        self.value = {}
        while string.peek() != 'e':
            key = String(string)
            self.value[key] = Torrent.parse(string)
        string.get(1)

    def dump(self, formatter, tabchar, depth):
        keys = self.value.keys()
        keys.sort()
        for key in keys:
            formatter.string_format(TextFormatter.NORMAL | TextFormatter.GREEN)
            if depth < 2:
                formatter.string_format(TextFormatter.BRIGHT)
            key.dump(formatter, tabchar, depth)
            formatter.string_format(TextFormatter.NORMAL)
            self.value[key].dump(formatter, tabchar, depth + 1)

    def __getitem__(self, key):
        for name, value in self.value.iteritems():
            if name.value == key:
                return value
        raise KeyError(key)

    def __contains__(self, key):
        for name in self.value:
            if name.value == key:
                return True
        return False


class List:
    def __init__(self, string):
        # Prefix char, then list of values until an 'e' is hit
        string.get(1)
        self.value = []
        while string.peek() != 'e':
            self.value.append(Torrent.parse(string))
        string.get(1)

    def dump(self, formatter, tabchar, depth):
        if len(self.value) == 1:
            self.value[0].dump(formatter, tabchar, depth)
        else:
            for index in range(len(self.value)):
                formatter.string_format(TextFormatter.BRIGHT |
                                        TextFormatter.YELLOW,
                                        '%s%d\n' % (tabchar * depth, index))
                formatter.string_format(TextFormatter.NORMAL)
                self.value[index].dump(formatter, tabchar, depth + 1)

    def join(self, separator):
        separator = String(
            StringBuffer('%d:%s' % (len(separator), separator)))
        return reduce(lambda x, y: x + separator + y, self.value)

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        return self.value.__iter__()

    def __getitem__(self, index):
        return self.value[index]


TYPE_MAP = [(re.compile('d'), Dictionary),
            (re.compile('l'), List),
            (re.compile('[0-9]'), String),
            (re.compile('i'), Integer)]

TAB_CHAR = '    '


def get_commandline_arguments(appname, arguments):
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
    sys.exit('%s [ -h -n ] filename1 [ ... filenameN ]\n\n' % appname +
             '    -h --help      Displays this message\n' +
             '    -b --basic     Shows basic file information (default)\n' +
             '    -t --top       Shows only the top level file/directory\n' +
             '    -f --files     Shows files within the torrent\n' +
             '    -d --dump      Dumps the whole file hierarchy\n' +
             '    -a --ascii     Only prints out ascii\n' +
             '    -n --nocolour  No ANSI colour\n')


def get_formatter(nocolour):
    return {True: TextFormatter, False: ANSIColour}[nocolour]()


def start_line(formatter, prefix, depth, postfix='',
               format_spec=TextFormatter.NORMAL):
    formatter.string_format(TextFormatter.BRIGHT | TextFormatter.GREEN,
                            '%s%s' % (TAB_CHAR * depth, prefix))
    formatter.string_format(format_spec, '%s%s' % (TAB_CHAR, postfix))


def get_line(formatter, prefix, key, torrent, depth=1, is_date=False,
             format_spec=TextFormatter.NORMAL):
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
    torrent.dump(formatter, TAB_CHAR, 1)


def basic(formatter, torrent):
    if not 'info' in torrent:
        sys.exit('Missing "info" section in %s' % torrent.filename)
    get_line(formatter, 'name       ', 'name', torrent['info'])
    get_line(formatter, 'tracker url', 'announce', torrent)
    get_line(formatter, 'created by ', 'created by', torrent)
    get_line(
        formatter, 'created on ', 'creation date', torrent, is_date=True)


def top(formatter, torrent):
    if not 'info' in torrent:
        sys.exit('Missing "info" section in %s' % torrent.filename)
    torrent['info']['name'].dump(formatter, '', 1, newline=False)


def basic_files(formatter, torrent):
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
            try:
                torrent = Torrent.load_torrent(filename)
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
            except Torrent.UnknownTypeChar:
                sys.stderr.write(
                    'Could not parse %s as a valid torrent file.\n' % filename)
    except SystemExit, message:
        sys.exit(message)
    except KeyboardInterrupt:
        pass



if __name__ == "__main__":
    main()
