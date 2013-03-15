               _                            _   _        __
              | |_ ___  _ __ _ __ ___ _ __ | |_(_)_ __  / _| ___
              | __/ _ \| '__| '__/ _ \ '_ \| __| | '_ \| |_ / _ \
              | || (_) | |  | | |  __/ | | | |_| | | | |  _| (_) |
               \__\___/|_|  |_|  \___|_| |_|\__|_|_| |_|_|  \___/



About
-----

TorrentInfo parses .torrent files and displays information about the torrent
and the files that it references. On the default basic setting it shows:

 - Torrent name
 - Tracker URL
 - The creator of the torrent
 - The torrent's creation date
 - The number of files (if a multi-file torrent)
 - The name of the file (if a single-file torrent)
 - The total size of the file/files

If asked to display file information the path and size of each file is
listed.

Additionally the entire torrent can be shown in hierachical form.

Why fork?
-----
I forked the original project simply because it was missing functionality I
desired, namely what the `-t` flag does now. It turned out that the code
was an undocummented mess but it worked so no one bothered. It was no longer
listed on the creators website and the original creator was surprised that
anyone even found it useful. For this reason I decided to the dust off the
project, clean it up, document it and provide a few tests along the way.

I'm keeping the original name of the project in case someone (like me) finds
themself in a similar position and does a Google search for "torrentinfo".

Usage
-----

torrentinfo.py [ -h -n ] filename1 [ ... filenameN ]

    -h --help      Displays this message
    -b --basic     Shows basic file information (default)
    -t --top       Shows only the top level file/directory
    -f --files     Shows files within the torrent
    -d --dump      Dumps the whole file hierarchy
    -a --ascii     Only prints out ascii
    -n --nocolour  No ANSI colour


If no settings are specified the script will default to showing the basic
information on each file.

Install
------

TorrentInfo uses the standard Python distribution utilities. So it should just
be a case of uncompressing the archive and running:

    ./setup.py install

Obviously the user running this must have sufficient permissions to create a
file in the install directory.

Bugs
----

Any bugs or fixes should be submitted to
https://github.com/ShanaTsunTsunLove/torrentinfo

Original creator (no longer maintains):
Vrai Stacey <vrai@acherondevelopment.com>
http://vrai.net/
