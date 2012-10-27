#!/usr/bin/env python

##############################################################################
# T O R R E N T I N F O - Setup file
# version 1.0.2
#
# Vrai Stacey <vrai@acherondevelopment.com>
##############################################################################

from distutils.core import setup;

setup ( name         = "torrentinfo",
		version      = "1.0.2",
		description  = "Bittorrent .torrent file parser and summariser",
		author       = "Vrai Stacey",
		author_email = "vrai@acherondevelopment.com",
		url          = "http://vrai.net/project.php?project=torrentinfo",
		license      = "GNU General Public License (see LICENSE file)",
		scripts      = [ "torrentinfo" ] );
