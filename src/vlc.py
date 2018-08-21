import logging, time, subprocess

import requests
from urllib.parse import urljoin


class VLCConnectionError(Exception):
    pass


class VLCLauncher:
    def __init__(self, config):
        self.config = config
        self.base_url = 'http://' + config['host'] + ':' + str(config['port'])
    
    def check_connection(self, retries=0):
        for i in range(retries, -1, -1):
            try:
                resp = requests.get(self.base_url, timeout=5)
            except requests.exceptions.ConnectionError:
                if i > 0:
                    logging.debug('Connection attempt failed. Will retry in 3 seconds.')
                    time.sleep(3)
                    continue
            else:
                if 'VideoLAN' in resp.text:
                    return True
        
        raise VLCConnectionError('Failed to connect to the VLC web server.')
    
    def launch(self):
        try:
            self.check_connection()
        except VLCConnectionError:
            pass
        else:
            logging.info('VLC is already running.')
            return
        
        logging.info('Launching VLC with HTTP server at %s' % self.config['path'])
        
        self.instance = subprocess.Popen(
            [
                self.config['path'],
                '--extraintf', 'http',
                '--http-host', self.config['host'],
                '--http-port', str(self.config['port']),
                '--http-password', str(self.config['password'])
            ]
        )
        
        self.check_connection(3)


class VLCHTTPClient:
    def __init__(self, config):
        self.session = requests.session()
        self.base_url = 'http://' + config['host'] + ':' + str(config['port'])
        self.session.auth = ('', config['password'])
        
        logging.info('Trying to connect to the VLC web server.')
        try:
            self._request('requests/status.xml')
        except Exception as e:
            raise VLCConnectionError(
                'Cannot connect to the VLC web server. '
                'Is it running at %s?' % self.base_url
            ) from e
        logging.info('Connection to the VLC web server succeeded.')
    
    def _request(self, path, **kwargs):
        resp = self.session.get(urljoin(self.base_url, path), **kwargs)
        
        if resp.status_code != requests.codes.ok:
            resp.raise_for_status()
        
        self.session.close()  # VLC doesn't support keep-alive
        
        return resp
    
    def _command(self, command, params={}):
        # VLC doesn't support urlencoded parameters
        # https://forum.videolan.org/viewtopic.php?f=16&t=145695
        params = ('command=' + command + '&' +
                  '&'.join('%s=%s' % (k, v) for k, v in params.items()))
        return self._request('requests/status.xml', params=params)
    
    def add(self, uri):
        return self._command('in_play', {'input': uri})
    
    def enqueue(self, uri):
        return self._command('in_enqueue', {'input': uri})
    
    def play(self, uid=None):
        if uid:
            return self._command('pl_play', {'id': uid})
        else:
            return self._command('pl_play')
    
    def pause(self):
        return self._command('pl_pause')
    
    def stop(self):
        return self._command('pl_stop')
    
    def next(self):
        return self._command('pl_next')
    
    def previous(self):
        return self._command('pl_previous')
    
    def empty(self):
        return self._command('pl_empty')
