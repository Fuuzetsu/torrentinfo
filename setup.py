#!/usr/bin/env python
from distutils.core import setup
import os
import os.path

install_file = 'torrentinfo.py'
if os.name is 'posix':
    src_path = os.path.abspath('src')
    file_path = os.path.join(src_path, 'torrentinfo')
    if os.path.exists(file_path):
        os.remove(file_path)

    os.symlink(os.path.join(src_path, 'torrentinfo.py'), file_path)

    install_file = 'torrentinfo'


setup(name="torrentinfo",
      version="1.8.6",
      description="Bittorrent .torrent file parser and summariser",
      author="Mateusz Kowalczyk",
      author_email="fuuzetsu@fuuzetsu.co.uk",
      url="https://github.com/Fuuzetsu/torrentinfo",
      license="GNU General Public License v2 (see LICENSE file)",
      scripts=[os.path.join("src", install_file)])
