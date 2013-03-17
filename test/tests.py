#!/usr/bin/env/python
# -*- coding: utf-8 -*-

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

import sys
import os.path
import os
sys.path.append(os.path.join('..', 'src'))

from StringIO import StringIO
import unittest
import nose
import torrentinfo


class TextFormatterTest(unittest.TestCase):

    def setUp(self):
        self.out = StringIO()
        self.colour_codes = dict(torrentinfo.TextFormatter.mapping)

    def test_no_colour_simple_succeed(self):
        formatter = torrentinfo.TextFormatter(False)
        norm_col = torrentinfo.TextFormatter.NORMAL
        test_string = 'oaeuAOEU:<>%75'
        formatter.string_format(norm_col, string=test_string, out=self.out)
        output = self.out.getvalue()
        self.assertEqual(output, test_string)

    def test_no_colour_simple_fail(self):
        formatter = torrentinfo.TextFormatter(False)
        norm_col = torrentinfo.TextFormatter.NORMAL
        test_string = 'oaeuAOEU:<>%75'
        trash_output = 'trash_output'
        formatter.string_format(norm_col, string=test_string, out=self.out)
        output = self.out.getvalue()
        assert trash_output != test_string
        self.assertNotEqual(output, trash_output)

    def test_colour_simple_succeed(self):
        formatter = torrentinfo.TextFormatter(True)
        red_code = self.colour_codes[torrentinfo.TextFormatter.RED]
        norm_string = 'oaeuAOEU:<>%75'
        test_string = '%s%s%s' % (torrentinfo.TextFormatter.escape,
                                  red_code, norm_string)
        formatter.string_format(torrentinfo.TextFormatter.RED,
                                string=norm_string, out=self.out)
        output = self.out.getvalue()
        self.assertEqual(output, test_string)

    def test_colour_simple_fail(self):
        formatter = torrentinfo.TextFormatter(True)
        red_code = self.colour_codes[torrentinfo.TextFormatter.RED]
        norm_string = 'oaeuAOEU:<>%75'
        test_string = '%s%s%s' % (torrentinfo.TextFormatter.escape,
                                  red_code, norm_string)
        formatter.string_format(torrentinfo.TextFormatter.GREEN,
                                string=norm_string, out=self.out)
        output = self.out.getvalue()
        self.assertNotEqual(output, test_string)

    def test_no_colour_unicode_succeed(self):
        formatter = torrentinfo.TextFormatter(False)
        norm_col = torrentinfo.TextFormatter.NORMAL
        test_string = 'oaeuAOEU灼眼のシャナ:<>%75'
        formatter.string_format(norm_col, string=test_string, out=self.out)
        output = self.out.getvalue()
        self.assertEqual(output, test_string)

    def test_no_colour_unicode_fail(self):
        formatter = torrentinfo.TextFormatter(False)
        norm_col = torrentinfo.TextFormatter.NORMAL
        test_string = 'oaeuAOEU灼眼のシャナ:<>%75'
        trash_output = 'oaeuAOEU封絶:<>%75'
        formatter.string_format(norm_col, string=test_string, out=self.out)
        output = self.out.getvalue()
        assert trash_output != test_string
        self.assertNotEqual(output, trash_output)

    def test_colour_unicode_succeed(self):
        formatter = torrentinfo.TextFormatter(True)
        green_code = self.colour_codes[torrentinfo.TextFormatter.GREEN]
        norm_string = 'oaeuAOEU灼眼のシャナ:<>%75'

        test_string = '%s%s%s' % (torrentinfo.TextFormatter.escape,
                                  green_code, norm_string)

        formatter.string_format(torrentinfo.TextFormatter.GREEN,
                                string=norm_string, out=self.out)

        output = self.out.getvalue()
        self.assertEqual(output, test_string)

    def test_colour_unicode_fail(self):
        formatter = torrentinfo.TextFormatter(True)
        green_code = self.colour_codes[torrentinfo.TextFormatter.GREEN]
        norm_string = 'oaeuAOEU灼眼のシャナ:<>%75'

        test_string = '%s%s%s' % (torrentinfo.TextFormatter.escape,
                                  green_code, norm_string)

        formatter.string_format(torrentinfo.TextFormatter.YELLOW,
                                string=norm_string, out=self.out)

        output = self.out.getvalue()
        self.assertNotEqual(output, test_string)

    def test_date_succees(self):
        formatter = torrentinfo.TextFormatter(False)
        date_number = 1363542066
        result = '2013/03/17 17:41:06 GMT\n'
        torrentinfo.dump_as_date(date_number, formatter, out=self.out)
        output = self.out.getvalue()
        self.assertEqual(output, result)

    def test_date_fail(self):
        formatter = torrentinfo.TextFormatter(False)
        date_number = 1363542066
        result = '2099/03/17 17:41:06 GMT\n'
        torrentinfo.dump_as_date(date_number, formatter, out=self.out)
        output = self.out.getvalue()
        self.assertNotEqual(output, result)


    def tearDown(self):
        self.out = sys.stdout


class StringBufferTest(unittest.TestCase):

    def test_is_eof_true(self):
        s = torrentinfo.StringBuffer('')
        self.assertTrue(s.is_eof(), 'Did not catch eof with empty string')

    def test_is_eof_false(self):
        s = torrentinfo.StringBuffer('foo')
        self.assertFalse(s.is_eof(), 'Caught eof with `foo\'')

    def test_peek_succeed(self):
        s = torrentinfo.StringBuffer('foo')
        self.assertEqual(s.peek(), 'f',
                         "Did not peek a correct letter with `foo'")

    def test_peek_fail(self):
        s = torrentinfo.StringBuffer('bar')
        self.assertNotEqual(s.peek(), 'f', "Peeked an `f'  letter with `bar'")

    def test_peek_overrun(self):
        s = torrentinfo.StringBuffer('')
        self.assertRaises(torrentinfo.StringBuffer.BufferOverrun, s.peek)

    def test_get_succeed(self):
        s = torrentinfo.StringBuffer('foo')
        self.assertEqual(s.get(2), 'fo',
                         "get(2) got incorrect characters with `foo'")

    def test_get_multi(self):
        s = torrentinfo.StringBuffer('foobarbaz')
        s.get(3)
        s.get(3)
        self.assertEqual(s.get(3), 'baz',
                         "Multiple get(3) didn't produce final result `baz'")

    def test_get_fail(self):
        s = torrentinfo.StringBuffer('bar')
        self.assertNotEqual(s.get(2), 'fo',
                         "get(2) got `fo'' characters with `bar'")

    def test_get_overrun(self):
        s = torrentinfo.StringBuffer('foo')
        self.assertRaises(torrentinfo.StringBuffer.BufferOverrun, s.get, 10)

    def test_get_upto_succeed(self):
        s = torrentinfo.StringBuffer('abcdef')
        self.assertEqual(s.get_upto('d'), 'abc',
                         "get_upto('d') failed to get `abc' with `abcdef'")

    def test_get_upto_character_expected(self):
        s = torrentinfo.StringBuffer('abcdef')
        self.assertRaises(torrentinfo.StringBuffer.CharacterExpected,
                          s.get_upto, 'x')


class GenericTorrentTest(unittest.TestCase):
    __test__ = False

    def test_load_torrent_succeed(self):
        self.assertNotEqual(self.torrent, None,
                            "Loaded %s is None" % self.file['path'])

    def test_load_torrent_fail(self):
        self.assertRaises(IOError, torrentinfo.load_torrent,
                          'fakefoobar.fake')

    def test_load_torrent_unexpected_type(self):
        data = torrentinfo.StringBuffer('4:fake')
        self.assertRaises(torrentinfo.UnexpectedType,
                          torrentinfo.Torrent, *('foo', data))

    def test_filename_succeed(self):
        self.assertEqual(self.torrent.filename, self.file['path'])

    def test_filename_fail(self):
        self.assertNotEqual(self.torrent.filename, 'fakefilename.xyz')

    def test_parse_unknown_type_char(self):
        bogus_data = torrentinfo.StringBuffer("d8:announcex7:invalid")
        self.assertRaises(torrentinfo.UnknownTypeChar,
                          torrentinfo.decode, bogus_data)

    def test_parse_buffer_overrun(self):
        bogus_data = torrentinfo.StringBuffer("d20:announce")
        self.assertRaises(torrentinfo.StringBuffer.BufferOverrun,
                          torrentinfo.decode, bogus_data)

    def test_tracker_succeed(self):
        self.assertEqual(self.torrent['announce'],
                         'fake.com/announce')

    def test_tracker_fail(self):
        self.assertNotEqual(self.torrent['announce'],
                            'different_tracker.fake')


class GenericOutputTest(unittest.TestCase):
    __test__ = False

    def setUp(self):
        self.out = StringIO()

    def test_top_succeed(self):
        formatter = torrentinfo.TextFormatter(False)
        torrentinfo.top(formatter, self.torrent, out=self.out)
        output = self.out.getvalue()
        self.assertEqual(self.file['top'], output)

    def tearDown(self):
        self.out = sys.stdout


class RegularTorrentTest(GenericTorrentTest, GenericOutputTest):
    __test__ = True

    def setUp(self):
        super(RegularTorrentTest, self).setUp()
        self.torrent = None
        self.file = dict()
        self.file['name'] = 'regular.torrent'
        self.file['top'] = 'torrentinfo.py'
        self.file['path'] = os.path.join('test', 'files', self.file['name'])
        self.torrent = torrentinfo.Torrent(self.file['path'],
                                           torrentinfo.load_torrent(self.file['path']))

class MegabyteTorrentTest(GenericTorrentTest, GenericOutputTest):
    __test__ = True

    def setUp(self):
        super(MegabyteTorrentTest, self).setUp()
        self.torrent = None
        self.file = dict()
        self.file['name'] = 'megabyte.torrent'
        self.file['top'] = 'megabyte'
        self.file['path'] = os.path.join('test', 'files', self.file['name'])
        self.torrent = torrentinfo.Torrent(self.file['path'],
                                           torrentinfo.load_torrent(self.file['path']))

class TwoMegabyteTorrentTest(GenericTorrentTest, GenericOutputTest):
    __test__ = True

    def setUp(self):
        super(TwoMegabyteTorrentTest, self).setUp()
        self.torrent = None
        self.file = dict()
        self.file['name'] = 'two_megabytes.torrent'
        self.file['top'] = 'two_megabytes'
        self.file['path'] = os.path.join('test', 'files', self.file['name'])
        self.torrent = torrentinfo.Torrent(self.file['path'],
                                           torrentinfo.load_torrent(self.file['path']))

class MultiMegabyteTorrentTest(GenericTorrentTest, GenericOutputTest):
    __test__ = True

    def setUp(self):
        super(MultiMegabyteTorrentTest, self).setUp()
        self.torrent = None
        self.file = dict()
        self.file['name'] = 'multi_bytes.torrent'
        self.file['top'] = 'multibyte'
        self.file['path'] = os.path.join('test', 'files', self.file['name'])
        self.torrent = torrentinfo.Torrent(self.file['path'],
                                           torrentinfo.load_torrent(self.file['path']))



if __name__ == '__main__':
    nose.main(buffer=True)
