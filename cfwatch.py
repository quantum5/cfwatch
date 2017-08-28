#!/usr/bin/env python
import logging
import os
from threading import Lock, Event, Thread

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import requests
from watchdog.events import FileSystemEventHandler, FileSystemMovedEvent
from watchdog.observers import Observer

log = logging.getLogger('cfwatch')


class CloudFlareMonitorHandler(FileSystemEventHandler):
    def __init__(self, email, token, zone, prefix, dir='.'):
        self.session = requests.Session()
        self.to_purge = set()
        self.queue_lock = Lock()
        self._trigger = Event()
        self._stop = False

        self.email = email
        self.token = token
        self.zone = self._get_zone(zone)
        self.prefix = prefix
        self.base = dir

    def on_any_event(self, event):
        if event.is_directory:
            return

        self.queue_purge(event.src_path)

        if isinstance(event, FileSystemMovedEvent):
            self.queue_purge(event.dest_path)

    def queue_purge(self, path):
        path = os.path.relpath(path, self.base)
        if os.sep == '\\':
            path = path.replace('\\', '/')
        url = urljoin(self.prefix, path)
        log.debug('Going to purge: %s', url)
        with self.queue_lock:
            self.to_purge.add(url)
        self._trigger.set()

    def _get_zone(self, name):
        resp = self.cf_request('GET', 'https://api.cloudflare.com/client/v4/zones?name=%s' % (name,)).json()
        try:
            if not resp['success']:
                raise ValueError('Failed to obtain zone info: %r' % (resp['errors'],))

            if not resp['result']:
                raise ValueError('No such zone: %s' % (name,))

            return resp['result'][0]['id']
        except KeyError:
            raise ValueError('Malformed response: %r' % (resp,))

    def cf_request(self, *args, **kwargs):
        headers = {
            'X-Auth-Email': self.email,
            'X-Auth-Key': self.token,
        }
        headers.update(kwargs.pop('headers', {}))
        kwargs['headers'] = headers
        return self.session.request(*args, **kwargs)

    def purge(self, urls):
        for chunk in zip_longest(*[iter(urls)] * 30):
            chunk = [url for url in chunk if url]
            try:
                resp = self.cf_request(
                    'DELETE',
                    'https://api.cloudflare.com/client/v4/zones/%s/purge_cache' % (self.zone,),
                    json={'files': chunk},
                ).json()

                if resp['success']:
                    for url in chunk:
                        log.info('Successfully purged: %s', url)
                else:
                    for url in chunk:
                        log.info('Failed to purged: %s', url)
                    log.error('Cloudflare responded with error: %r', resp['errors'])
            except (IOError, KeyError):
                for url in chunk:
                    log.exception('Failed to purge: %s', url)

    def run(self):
        observer = Observer()
        observer.schedule(self, self.base, recursive=True)
        observer.start()

        log.info('Started watching.')
        log.info('Local prefix: %s', self.base)
        log.info('Remote prefix: %s', self.prefix)
        try:
            while True:
                self._trigger.wait()
                self._trigger.clear()
                if self._stop:
                    break

                self._trigger.wait(1)
                if self._trigger.is_set():
                    continue

                with self.queue_lock:
                    current, self.to_purge = self.to_purge, set()

                if current:
                    self.purge(current)
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()

    def start(self):
        Thread(target=self.run).start()

    def stop(self):
        self._stop = True
        self._trigger.set()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Purges CloudFlare on local file change.')
    parser.add_argument('email', help='CloudFlare login email (e.g. user@example.com)')
    parser.add_argument('token', help='CloudFlare API key (e.g. c2547eb745079dac9320b638f5e225cf483cc5cfdda41)')
    parser.add_argument('zone', help='CloudFlare zone (e.g. example.com)')
    parser.add_argument('prefix', help='CloudFlare path prefix (e.g. http://example.com/)')
    parser.add_argument('dir', nargs='?', default='.',
                        help='directory to watch, i.e. file.txt this directory '
                             'is http://example.com/file.txt',
                        )
    parser.add_argument('-l', '--log', help='log file')
    args = parser.parse_args()

    logging.basicConfig(filename=args.log, format='%(asctime)-15s %(message)s', level=logging.INFO)

    monitor = CloudFlareMonitorHandler(args.email, args.token, args.zone, args.prefix, args.dir)
    monitor.run()


if __name__ == '__main__':
    main()
