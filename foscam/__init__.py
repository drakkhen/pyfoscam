import base64
import httplib
import urllib

# move method commands
UP = 0
HALT_UP = 1
DOWN = 2
HALT_DOWN = 3
RIGHT = 4
HALT_RIGHT = 5
LEFT = 6
HALT_LEFT = 7
CENTER = 25
VERTICAL_PATROL = 26
HALT_VERTICAL_PATROL = 27
HORIZONTAL_PATROL = 28
HALT_HORIZONTAL_PATROL = 29

# resolution method values
RES_320_240 = 8
RES_640_480 = 32

# mode method values
MODE_50HZ = 0
MODE_60HZ = 1
MODE_OUTDOOR = 2

# transform method values
RESET = 0
FLIP = 1
MIRROR = 2
FLIP_MIRROR = 3

def params_to_hash(s):
    """
    Converts a string like:

    '''var foo = 'hello';
    var bar = 2;
    var baz = 3.14;'''

    to a Dictionary like: {'foo': 'hello', 'bar': 2, 'baz': 3.14}
    """
    res = {}

    for line in s.split("\n"):
        line = line[4:-1]
        k,v = line.split('=', 1)

        try:
            v = int(v)
        except:
            try:
                v = float(v)
            except:
                if v.startswith("'") and v.endswith("'"):
                    v = v[1:-1]
                else:
                    raise Exception("Unexpected value format: %s" % repr(v))

        res[k] = v

    return res


class Foscam:
    def __init__(self, username='admin', password='', host='camera', port=80):
        """
        Initizlize a new Foscam instance.
        """
        self.host = host
        self.port = port
        auth_val = base64.b64encode(b"%s:%s" % (username, password)).decode("ascii")
        self.headers = { 'Authorization' : 'Basic %s' % auth_val }

    def _send(self, path, **params):
        """
        Sends a command to the web service and returns the response.
        """
        full_path = "/%s?%s" % (path, urllib.urlencode(params))

        conn = httplib.HTTPConnection(self.host, self.port)
        conn.request("GET", full_path, headers=self.headers)
        resp = conn.getresponse()

        if resp.status != 200:
            raise Exception("HTTP response was %d: %s" % (resp.status, resp.reason))

        data = resp.read().strip()

        return data

    def status(self):
        """
        Returns the status of the camera as a Dictionary.
        """
        res = params_to_hash(self._send('get_status.cgi'))

        if res.has_key('alarm_status'):
            res['alarm_status_string'] = [
                'no alarm',
                'motion alarm',
                'input alarm'
            ][res['alarm_status']]

        if res.has_key('ddns_status'):
            res['ddns_status_string'] = [
                'No Action',
                "It's connecting...",
                "Can't connect to the Server",
                'Dyndns Succeed',
                'DynDns Failed: Dyndns.org Server Error',
                'DynDns Failed: Incorrect User or Password',
                'DynDns Failed: Need Credited User',
                'DynDns Failed: Illegal Host Format',
                'DynDns Failed: The Host Does not Exist',
                'DynDns Failed: The Host Does not Belong to You',
                'DynDns Failed: Too Many or Too Few Hosts',
                'DynDns Failed: The Host is Blocked for Abusing',
                'DynDns Failed: Bad Reply from Server',
                'DynDns Failed: Bad Reply from Server',
                'Oray Failed: Bad Reply from Server',
                'Oray Failed: Incorrect User or Password',
                'Oray Failed: Incorrect Hostname',
                'Oray Succeed',
                'Reserved',
                'Reserved',
                'Reserved',
                'Reserved'
            ][res['ddns_status']]

        if res.has_key('upnp_status'):
            res['upnp_status_string'] = [
                'No Action',
                'Succeed',
                'Device System Error',
                'Errors in Network Communication',
                'Errors in Chat with UPnP Device',
                'Rejected by UPnP Device, Maybe Port Conflict',
            ][res['upnp_status']]

        return res

    def reboot(self):
        """
        Reboots the camera.
        """
        return self._send('reboot.cgi')

    def restore_factory_defaults(self):
        """
        Restores camera's default factory settings.
        """
        return self._send('restore_factory.cgi')

    def get_params(self):
        """
        Gets general parameters from the camera.  Warning: this includes
        secrets like the WPA PSK and other passwords.
        """
        return params_to_hash(self._send('get_params.cgi'))

    def get_camera_params(self):
        """
        Gets camera parameters like brightness, contrast, resolution,
        FPS, and mode.
        """
        return params_to_hash(self._send('get_camera_params.cgi'))

    def set_preset(self, x):
        """
        Sets a preset to the current camera location.
        """
        if val not in range(0,16):
            raise ValueError("%s is out of range; use 0-16." % repr(val))

        cmd = [30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60][int(x)]
        return self._send('decoder_control.cgi', command=cmd)

    def goto_preset(self, x):
        """
        Restores camera's position to the given preset.
        """
        if val not in range(0,16):
            raise ValueError("%s is out of range; use 0-16." % repr(val))

        cmd = [31,33,35,37,39,41,43,45,47,49,51,53,55,57,59,61][int(x)]
        return self._send('decoder_control.cgi', command=cmd)

    def nightvision(self, v):
        """
        Turns IR on (if param is True) or off (if param is False).
        """
        if v not in (True, False):
            raise ValueError("%s not valid for this action; use True or False." % repr(v))

        cmd = v and 95 or 94
        return self._send('decoder_control.cgi', command=cmd)

    def move(self, cmd):
        """
        Tell the camera to start or stop moving.
        """
        valid = (UP, HALT_UP, DOWN, HALT_DOWN, LEFT, HALT_LEFT, RIGHT,
            HALT_RIGHT, CENTER, VERTICAL_PATROL, HALT_VERTICAL_PATROL,
            HORIZONTAL_PATROL, HALT_HORIZONTAL_PATROL)

        if cmd not in valid:
            raise ValueError("%s not valid for this action. Use one of: UP, HALT_UP, DOWN, HALT_DOWN, LEFT, HALT_LEFT, RIGHT, HALT_RIGHT, CENTER, VERTICAL_PATROL, HALT_VERTICAL_PATROL, HORIZONTAL_PATROL, HALT_HORIZONTAL_PATROL." % repr(cmd))

        return self._send('decoder_control.cgi', command=cmd)

    def resolution(self, res):
        """
        Set camera resolution.
        """
        if cmd not in (RES_320_240, RES_640_480):
            raise ValueError("%s not valid for this action. Use one of: RES_320_240, RES_640_480." % repr(cmd))

        return self._send('camera_control.cgi', param=0, value=res)

    def brightness(self, val):
        """
        Set camera brightness.
        """
        if val not in range(0,255):
            raise ValueError("%s is out of range; use 0-255." % repr(val))

        return self._send('camera_control.cgi', param=1, value=val)

    def contrast(self, val):
        """
        Set camera contrast.
        """
        if val not in range(0,255):
            raise ValueError("%s is out of range; use 0-255." % repr(val))

        return self._send('camera_control.cgi', param=2, value=val)

    def mode(self, val):
        if val not in (MODE_50HZ, MODE_60HZ, MODE_OUTDOOR):
            raise ValueError("%s not valid for this action. Use one of: MODE_50HZ, MODE_60HZ, MODE_OUTDOOR." % repr(val))

        return self._send('camera_control.cgi', param=3, value=val)

    def transform(self, val):
        if val not in (RESET, FLIP, MIRROR, FLIP_MIRROR):
            raise ValueError("%s not valid for this action. Use one of: RESET, FLIP, MIRROR, FLIP_MIRROR." % repr(val))

        return self._send('camera_control.cgi', param=5, value=val)

    def snapshot(self):
        return self._send('snapshot.cgi')

    def snapshot_to_file(self, path):
        fh = open(path, 'wb')
        data = self.snapshot()
        fh.write(data)
        fh.close()
        return len(data)

    def set_alias(self, alias):
        return self._send('set_alias.cgi', alias=alias)

    def set_datetime(self, datetime):
        return self._send('set_datetime.cgi', datetime)
