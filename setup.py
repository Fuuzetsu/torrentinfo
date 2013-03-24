#!/usr/bin/env python
from distutils.core import setup
import os.path

setup(name="torrentinfo",
      version="1.6.0",
      description="Bittorrent .torrent file parser and summariser",
      author="Mateusz Kowalczyk",
      author_email="fuuzetsu@fuuzetsu.co.uk",
      url="https://github.com/ShanaTsunTsunLove/torrentinfo",
      license="GNU General Public License v2 (see LICENSE file)",
      scripts=[os.path.join("src", "torrentinfo.py")])
