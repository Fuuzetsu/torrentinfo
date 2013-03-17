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
import argparse
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
        result = '2013/03/17 17:41:06 UTC\n'
        torrentinfo.dump_as_date(date_number, formatter, out=self.out)
        output = self.out.getvalue()
        self.assertEqual(output[:-5], result[:-5])

    def test_date_fail(self):
        formatter = torrentinfo.TextFormatter(False)
        date_number = 1363542066
        result = '2099/03/17 17:41:06 UTC\n'
        torrentinfo.dump_as_date(date_number, formatter, out=self.out)
        output = self.out.getvalue()
        self.assertNotEqual(output[:-5], result[:-5])

    def test_size_success(self):
        formatter = torrentinfo.TextFormatter(False)
        size = 1024 * 1024
        torrentinfo.dump_as_size(size, formatter, '    ', 0,
                                 out=self.out)
        output = self.out.getvalue()
        self.assertEqual(output, '1.0MB\n')

    def test_size_fail(self):
        formatter = torrentinfo.TextFormatter(False)
        size = 1024
        torrentinfo.dump_as_size(size, formatter, '    ', 0,
                                 out=self.out)
        output = self.out.getvalue()
        self.assertNotEqual(output, '1.0GB')


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

class MissingInfoTest(unittest.TestCase):

    def setUp(self):
        self.tf = torrentinfo.TextFormatter(False)
        path = os.path.join('test', 'files', 'missing_info.torrent')
        self.torrent = torrentinfo.Torrent(path,
                                           torrentinfo.load_torrent(path))
        self.msg = 'Missing "info" section in %s' % self.torrent.filename

    def generic_exit_trigger(self, f):
        out = StringIO()
        try:
            out = f(self.tf, self.torrent, err=out)
        except SystemExit:
            return out.getvalue()

    def test_top_exit_value_on_fail(self):
        self.assertRaises(SystemExit, torrentinfo.top, *(self.tf, self.torrent))

    def test_top_msg(self):
        errmsg = self.generic_exit_trigger(torrentinfo.top)
        self.assertEqual(errmsg, self.msg)

    def test_basic_files_exit_value_on_fail(self):
        self.assertRaises(SystemExit, torrentinfo.basic_files,
                          *(self.tf, self.torrent))

    def test_basic_files_msg(self):
        errmsg = self.generic_exit_trigger(torrentinfo.basic_files)
        self.assertEqual(errmsg, self.msg)

    def test_basic_exit_value_on_fail(self):
        self.assertRaises(SystemExit, torrentinfo.basic,
                          *(self.tf, self.torrent))

    def test_basic_msg(self):
        errmsg = self.generic_exit_trigger(torrentinfo.basic)
        self.assertEqual(errmsg, self.msg)

    def test_list_files_exit_value_on_fail(self):
        self.assertRaises(SystemExit, torrentinfo.list_files,
                          *(self.tf, self.torrent))

    def test_list_files_msg(self):
        errmsg = self.generic_exit_trigger(torrentinfo.list_files)
        self.assertEqual(errmsg, self.msg)

    def tearDown(self):
        self.torrent = None

class CommandLineOutputTest(unittest.TestCase):

    def setUp(self):
        self.parser = torrentinfo.get_arg_parser()
        self.out = StringIO()
        self.err = StringIO()

    def torrent_path(self, name):
        return os.path.join('test', 'files', name)

    def arg_namespace(self, arg_string):
        return self.parser.parse_args(arg_string.split(' '))


    def test_basic_single(self):
        tname = 'regular.torrent'
        tp = self.torrent_path(tname)
        ns = self.arg_namespace('-n %s' % tp)

        return_string = '\n'.join([tname,
                                   '    name           torrentinfo.py',
                                   '    tracker url    fake.com/announce',
                                   '    created by     mktorrent 1.0',
                                   '    created on     2013/03/17 14:32:36 GMT',
                                   '    file name      torrentinfo.py',
                                   '    file size      22.1KB\n\n'])

        torrentinfo.main(alt_args=ns, out=self.out, err=self.err)
        assert self.err.getvalue() == ''
        self.assertEqual(self.out.getvalue(), return_string)

    def test_basic_multi(self):
        tname = 'multi_bytes.torrent'
        tp = self.torrent_path(tname)
        ns = self.arg_namespace('-n %s' % tp)

        return_string = '\n'.join([tname,
                                   '    name           multibyte',
                                   '    tracker url    fake.com/announce',
                                   '    created by     mktorrent 1.0',
                                   '    created on     2013/03/17 13:52:41 GMT',
                                   '    num files      2',
                                   '    total size     3.0MB\n\n'])

        torrentinfo.main(alt_args=ns, out=self.out, err=self.err)
        assert self.err.getvalue() == ''
        self.assertEqual(self.out.getvalue(), return_string)

    def test_top_single(self):
        tname = 'regular.torrent'
        tp = self.torrent_path(tname)
        ns = self.arg_namespace('-n -t %s' % tp)

        return_string = '\n'.join([tname,
                                   'torrentinfo.py\n'])

        torrentinfo.main(alt_args=ns, out=self.out, err=self.err)
        assert self.err.getvalue() == ''
        self.assertEqual(self.out.getvalue(), return_string)

    def test_top_multi(self):
        tname = 'multi_bytes.torrent'
        tp = self.torrent_path(tname)
        ns = self.arg_namespace('-n -t %s' % tp)

        return_string = '\n'.join([tname,
                                   'multibyte\n'])

        torrentinfo.main(alt_args=ns, out=self.out, err=self.err)
        assert self.err.getvalue() == ''
        self.assertEqual(self.out.getvalue(), return_string)


    def test_basic_files_single(self):
        tname = 'regular.torrent'
        tp = self.torrent_path(tname)
        ns = self.arg_namespace('-n -f %s' % tp)

        return_string = '\n'.join([tname,
                                   '    name           torrentinfo.py',
                                   '    tracker url    fake.com/announce',
                                   '    created by     mktorrent 1.0',
                                   '    created on     2013/03/17 14:32:36 GMT',
                                   '    files    ',
                                   '        0',
                                   '            torrentinfo.py',
                                   '            22.1KB\n\n'])

        torrentinfo.main(alt_args=ns, out=self.out, err=self.err)
        assert self.err.getvalue() == ''
        self.assertEqual(self.out.getvalue(), return_string)

    def test_basic_files_multi(self):
        tname = 'multi_bytes.torrent'
        tp = self.torrent_path(tname)
        ns = self.arg_namespace('-n -f %s' % tp)

        return_string = '\n'.join([tname,
                                   '    name           multibyte',
                                   '    tracker url    fake.com/announce',
                                   '    created by     mktorrent 1.0',
                                   '    created on     2013/03/17 13:52:41 GMT',
                                   '    files    ',
                                   '        0',
                                   '            megabyte',
                                   '            1.0MB',
                                   '        1',
                                   '            two_megabytes',
                                   '            2.0MB\n\n'])

        torrentinfo.main(alt_args=ns, out=self.out, err=self.err)
        assert self.err.getvalue() == ''
        self.assertEqual(self.out.getvalue(), return_string)


    def test_list_files_single(self):
        tname = 'regular.torrent'
        tp = self.torrent_path(tname)
        ns = self.arg_namespace('-n -d %s' % tp)

        return_string = '\n'.join([tname,
                                   '    files    ',
                                   '        0',
                                   '            torrentinfo.py',
                                   '            22.1KB',
                                   '    piece length    ',
                                   '            262144',
                                   '    pieces    ',
                                   '            \x9c\xf8\xe3\xe0qo\xfd>'
                                   + '\xda\xbd\xd5a\x04\xfa\x96\x1a\x9e\r7a\n\n'])

        torrentinfo.main(alt_args=ns, out=self.out, err=self.err)
        assert self.err.getvalue() == ''
        self.assertEqual(self.out.getvalue(), return_string)


    def test_list_files_multi(self):
        tname = 'multi_bytes.torrent'
        tp = self.torrent_path(tname)
        ns = self.arg_namespace('-n -d %s' % tp)

        return_string = '\n'.join([tname,
                                   '    files    ',
                                   '        0',
                                   '            path    ',
                                   '                megabyte',
                                   '            length    ',
                                   '                1048576',
                                   '        1',
                                   '            path    ',
                                   '                two_megabytes',
                                   '            length    ',
                                   '                2097152',
                                   '    piece length    ',
                                   '            262144',
                                   '    pieces    ',
                                   '            [240 UTF-8 Bytes]\n\n'])

        torrentinfo.main(alt_args=ns, out=self.out, err=self.err)
        assert self.err.getvalue() == ''
        self.assertEqual(self.out.getvalue(), return_string)


    def tearDown(self):
        self.parser = None
        self.out = None
        self.err = None


if __name__ == '__main__':
    nose.main(buffer=True)
