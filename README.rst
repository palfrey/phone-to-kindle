Phone to Kindle
===============

Requirements
------------
- Calibre
- pyinotify
- BeautifulSoup
- urlgrab (but this should be installed by the git submodule support anyway)

HOWTO
-----
- Copy settings.py.example to settings.py and change values as appropriate for your system.
- Run converter.py. It will process all existing unprocessed links, then wait for changes
  to the list of links until you press CTRL+C.
