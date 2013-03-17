#!/usr/bin/env/python

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

import unittest
import nose
import torrentinfo


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

class TorrentTest(unittest.TestCase):

    def setUp(self):
        self.torrent = None
        self.file = os.path.join('test', 'files', 'regular.torrent')
        self.torrent = torrentinfo.Torrent(self.file,
                                           torrentinfo.load_torrent(self.file))

    def test_load_torrent_succeed(self):
        self.assertNotEqual(self.torrent, None, "Loaded %s is None" % self.file)

    def test_load_torrent_fail(self):
        self.assertRaises(IOError, torrentinfo.load_torrent,
                          'fakefoobar.fake')

    def test_load_torrent_unexpected_type(self):
        data = torrentinfo.StringBuffer('4:fake')
        self.assertRaises(torrentinfo.UnexpectedType,
                          torrentinfo.Torrent, *('foo', data))

    def test_filename_succeed(self):
        self.assertEqual(self.torrent.filename, self.file)

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
                         'faketracker.com/announce')

    def test_tracker_fail(self):
        self.assertNotEqual(self.torrent['announce'],
                            'different_tracker.fake')

if __name__ == '__main__':
    nose.main()
