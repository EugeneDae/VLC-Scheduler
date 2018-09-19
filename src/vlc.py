import logging, time, asyncio

import requests
from urllib.parse import urljoin


class VLCError(Exception):
    pass


class VLCConnectionError(VLCError):
    pass


class VLCExitError(VLCError):
    pass


class VLCLauncher:
    def __init__(self, config, debug=False):
        self.config = config
        self.debug = debug
        self.base_url = 'http://' + config['host'] + ':' + str(config['port'])
        self.process = None
    
    def check_connection(self, retries=0):
        for i in range(retries, -1, -1):
            try:
                resp = requests.get(self.base_url, timeout=5)
            except requests.exceptions.RequestException as e:
                if i > 0:
                    logging.warning(
                        'Connection attempt failed because of: %s. Retry in 3 seconds.' % str(e)
                    )
                    time.sleep(3)
                    continue
            else:
                if 'VideoLAN' in resp.text:
                    return True
        
        raise VLCConnectionError('Failed to connect to the VLC web server.')
    
    async def launch(self):
        try:
            self.check_connection()
        except VLCConnectionError:
            pass
        else:
            logging.warning('Found existing VLC instance.')
            return
        
        logging.info('Launching VLC with HTTP server at %s.' % self.config['path'])
        
        command = [
            self.config['path'],
            '--extraintf', self.config['extraintf'],
            '--http-host', self.config['host'],
            '--http-port', str(self.config['port']),
            '--http-password', str(self.config['password']),
            '--repeat', '--image-duration', '-1'
        ] + self.config['options']
        
        kwargs = {}
        
        if self.debug:
            command.extend(('--log-verbose', '3'))
        else:
            kwargs['stderr'] = asyncio.subprocess.DEVNULL
            kwargs['stdout'] = asyncio.subprocess.DEVNULL
        
        self.process = await asyncio.create_subprocess_exec(*command, **kwargs)
        time.sleep(1)
        self.check_connection(3)
        return self.process
    
    async def watch_exit(self):
        if not self.process:
            return
        
        await self.process.wait()
        raise VLCExitError('VLC was closed.')


class VLCHTTPClient:
    def __init__(self, config):
        self.session = requests.session()
        self.base_url = 'http://' + config['host'] + ':' + str(config['port'])
        self.session.auth = ('', config['password'])
    
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
    
    def _format_uri(self, uri):
        # VLC only understands urlencoded =
        return uri.replace('=', '%3D')
    
    def status(self):
        return self._request('requests/status.json').json()
    
    def add(self, uri):
        return self._command('in_play', {'input': self._format_uri(uri)})
    
    def enqueue(self, uri):
        return self._command('in_enqueue', {'input': self._format_uri(uri)})
    
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
    
    def toggle_repeat(self):
        return self._command('pl_repeat')
    
    def repeat(self, value=None):
        if value is None:
            return self._command('pl_repeat')
        
        if self.status()['repeat'] != value:
            return self._command('pl_repeat')
