import sys
sys.path.append('../src')

import unittest
import nose
import torrentinfo
import os.path
import os

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
        self.torrent = torrentinfo.Torrent.load_torrent(self.file)

    def test_load_torrent_succeed(self):
        self.assertNotEqual(self.torrent, None, "Loaded %s is None" % self.file)

    def test_load_torrent_fail(self):
        self.assertRaises(IOError, torrentinfo.Torrent.load_torrent,
                          'fakefoobar.fake')

    def test_load_torrent_unexpected_type(self):
        data = torrentinfo.StringBuffer('4:fake')
        self.assertRaises(torrentinfo.Torrent.UnexpectedType,
                          torrentinfo.Torrent, *('foo', data))

    def test_filename_succeed(self):
        self.assertEqual(self.torrent.filename, self.file)

    def test_filename_fail(self):
        self.assertNotEqual(self.torrent.filename, 'fakefilename.xyz')

    def test_parse_unknown_type_char(self):
        bogus_data = torrentinfo.StringBuffer("d8:announcex7:invalid")
        self.assertRaises(torrentinfo.Torrent.UnknownTypeChar,
                          self.torrent.parse, bogus_data)

    def test_parse_buffer_overrun(self):
        bogus_data = torrentinfo.StringBuffer("d20:announce")
        self.assertRaises(torrentinfo.StringBuffer.BufferOverrun,
                          self.torrent.parse, bogus_data)

    def test_tracker_succeed(self):
        self.assertEqual(self.torrent['announce'].value,
                         'faketracker.com/announce')

    def test_tracker_fail(self):
        self.assertNotEqual(self.torrent['announce'].value,
                            'different_tracker.fake')

if __name__ == '__main__':
    nose.main()
