import os
import json
import logging
import traceback
from urlparse import urljoin
from urllib import urlencode
from urllib2 import urlopen, URLError
from contextlib import closing

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger('cfwatch')

class CloudFlareMonitorHandler(FileSystemEventHandler):
    def __init__(self, email, token, zone, prefix, dir='.'):
        self.email = email
        self.token = token
        self.zone = zone
        self.prefix = prefix
        self.base = dir

    def purge_event(self, event):
        if not event.is_directory:
            path = os.path.relpath(event.src_path, self.base)
            if os.sep == '\\':
                path = path.replace('\\', '/')
            url = urljoin(self.prefix, path)
            logger.debug('Going to purge: %s', url)
            try:
                with closing(urlopen('https://www.cloudflare.com/api_json.html', urlencode({
                    'a': 'zone_file_purge', 'tkn': self.token,
                    'email': self.email, 'z': self.zone, 'url': url
                }))) as f:
                    result = json.load(f)
                    logger.info('Successfully purged: %s' if result.get('result') == 'success'
                           else 'Failed to purge: %s', url)
            except (ValueError, URLError) as e:
                logger.exception('Failed to purge: %s', url)
    on_modified = purge_event
    on_moved = purge_event

def main():
    import argparse
    import time

    parser = argparse.ArgumentParser(description='Purges CloudFlare on file change.')
    parser.add_argument('email', help='CloudFlare login email')
    parser.add_argument('token', help='CloudFlare API key')
    parser.add_argument('zone', help='CloudFlare zone')
    parser.add_argument('prefix', help='CloudFlare path prefix')
    parser.add_argument('dir', help='directory to watch', nargs='?', default='.')
    parser.add_argument('-l', '--log', help='log file')
    args = parser.parse_args()

    logging.basicConfig(filename=args.log, format='%(asctime)-15s %(message)s',
                        level=logging.INFO)

    observer = Observer()
    observer.schedule(CloudFlareMonitorHandler(args.email, args.token, args.zone, args.prefix, args.dir), args.dir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

if __name__ == '__main__':
    main()
