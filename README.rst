``cfwatch`` |pypi|
==================

Automagically purges CloudFlare's cache when local files are updated.

This is useful for exporting a directory of files via CloudFlare. If
your files are updated, ``cfwatch`` will automatically purge the
corresponding URL on CloudFlare.

With ``cfwatch``, you will no longer need to add cache busting query
strings, and the direct link will always work.

Usage
-----

::

  $ pip install cfwatch
  $ cfwatch --help
  usage: cfwatch.py [-h] [-l LOG] zone prefix [dir]
  
  Purges CloudFlare on local file change.
  
  positional arguments:
    zone               CloudFlare zone (e.g. example.com)
    prefix             CloudFlare path prefix (e.g. http://example.com/)
    dir                directory to watch, i.e. file.txt this directory is
                       http://example.com/file.txt
  
  optional arguments:
    -h, --help         show this help message and exit
    -l LOG, --log LOG  log file

When running ``cfwatch``, you must set the following environment variables:

* ``CFWATCH_TOKEN`` to your CloudFlare API token (not the legacy API key)

.. |pypi| image:: https://img.shields.io/pypi/v/cfwatch.svg
   :target: https://pypi.python.org/pypi/cfwatch
