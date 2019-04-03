# -*- coding: utf-8 -*-
"""
    lantz.drivers.qhy.qhy
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Low level driver wrapping atcore andor library.


    Sources::

        - QHY SDK

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import ctypes as ct

from lantz import Driver, Feat, Action
from lantz import errors
from lantz.core.foreign import LibraryDriver

_OK = {
    7: 'QHYCCD_QGIGAE',
    6: 'QHYCCD_USBSYNC',
    5: 'QHYCCD_USBASYNC',
    4: 'QHYCCD_COLOR',
    3: 'QHYCCD_MONO',
    2: 'QHYCCD_COOL', # Supports cooling
    1: 'QHYCCD_NOTCOOL', # Doesn't support cooling
    0: 'SUCCESS',
}

_ERRORS = {
    -1: 'QHYCCD_ERROR',
    -2: 'QHYCCD_ERROR_NO_DEVICE',
    -3: 'QHYCCD_ERROR_UNSUPPORTED',
    -4 : 'QHYCCD_ERROR_SETPARAMS',
    -5: 'QHYCCD_ERROR_GETPARAMS',
    -6: 'QHYCCD_ERROR_EXPOSING',# The camera is exposing
    -7: 'QHYCCD_ERROR_EXPFAILED',
    -8: 'QHYCCD_ERROR_GETTINGDATA', # There is another instance getting data
    -9: 'QHYCCD_ERROR_GETTINGFAILED',
    -10: 'QHYCCD_ERROR_INITCAMERA',
    -11: 'QHYCCD_ERROR_RELEASERESOURCE',
    -12: 'QHYCCD_ERROR_INITRESOURCE',
    -13: 'QHYCCD_ERROR_NO_MATCH' ,
    -14: 'QHYCCD_ERROR_OPENCAM' ,
    -15: 'QHYCCD_ERROR_INITCLASS',
    -16: 'QHYCCD_ERROR_RESOLUTION',
    -17: 'QHYCCD_ERROR_USB_TRAFFIC',
    -18: 'QHYCCD_ERROR_USB_SPEED' ,
    -19: 'QHYCCD_ERROR_SETEXPOSE',
    -20: 'QHYCCD_ERROR_SETGAIN' ,
    -21: 'QHYCCD_ERROR_SETRED'  ,
    -22: 'QHYCCD_ERROR_SETBLUE' ,
    -23: 'QHYCCD_ERROR_EVTCMOS' ,
    -24: 'QHYCCD_ERROR_EVTUSB'  ,
    -25: 'QHYCCD_ERROR' ,
}

class QHY(LibraryDriver):

    LIBRARY_NAME = 'qhy.so'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cam_idx = 0
        self.cam_id = None
    # def _return_handler(self, func_name, ret_value):
    #     if ret_value != 0:
    #         raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
    #     return ret_value

    def initialize(self, stream_mode='single'):
        """Initialize Library.
        """
        self.lib.init_resource()
        self.scan_cameras()
        self.cam_id = self.camera_id(self.cam_idx)
        self.handler = self.open(self.cam_id)
        self.stream_mode = stream_mode
        self.init_camera()

    @Action()
    def scan_cameras(self):
        """ Scan available cameras.

        Returns
        -------
        cam_count      int
                       Number of available cameras
        """
        cam_count = self.lib.scan_cameras()
        return cam_count

    @Action()
    def camera_id(self, cam_idx):
        """ Get camera ID.

        Parameters
        ----------
        cam_idx     int
                    camera index (0, 1, ...)

        Returns
        -------
        cam_id      str
                    Camera ID (b'QHY183Mxxxxxxxxxxxxx')
        """
        idx = ct.c_int(cam_idx)
        self.lib.get_camera_id.restype = ct.c_char_p
        cam_id = self.lib.get_camera_id(idx)
        if cam_id.decode('ascii')=='':
            raise  errors.InstrumentError('No QHY cameras found.')
        else:
            self.cam_id = cam_id
        return cam_id


    @Action()
    def open(self, cam_id):
        """Open camera self.open_camera.

        Parameters
        ----------
        cam_id         int
                       Camera ID (b'QHY183Mxxxxxxxxxxxxx')

        Returns
        -------
        handler         qhyccd_handle (qhydevice.h typedef)
                        Camera handler
        """
        # if not self.cam_id:
        #     id = cam_id
        # else:
        #     id = self.cam_id
        self.lib.open_camera.restype = ct.c_void_p
        handler = self.lib.open_camera(cam_id)
        return handler

    @Action()
    def init_camera(self):
        self.lib.init_camera.argtypes = [ct.c_void_p]
        ret_value = self.lib.init_camera(self.handler)
        if ret_value not in _OK.keys():
            raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))

    @Feat(values={'single': 0, 'live': 1})
    def stream_mode(self):
        return self.stream_mode

    @stream_mode.setter
    def stream_mode(self, value='single'):
        """Open camera self.open_camera.

        Parameters
        ----------
        mode        int
                    0 for single frame mode and 1 for video mode.
        """
        cam_mode = ct.c_int(value)
        self.lib.set_stream_mode.argtypes = [ct.c_void_p, ct.c_int]
        ret_value = self.lib.set_stream_mode(self.handler, cam_mode)
        return ret_value

    @Feat(limits(50, 3600E6))
    def exposure(self):
        # Implement the getter
        return 0

    @exposure.setter
    def exposure(self, exp_time):
        self.lib.set_exposure.argtypes = [ct.c_void_p, ct.c_uint32]
        ret_value = self.lib.set_exposure(self.handler, exp_time)
        if ret_value not in _OK.keys():
            raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value


    @Action()
    def close(self):
        """Close camera self.initialize.
        """
        self.lib.close_camera(self.handler)

    def finalize(self):
        """Finalize Library. Concluding function.
        """
        self.close()
        self.lib.release()

if __name__ == '__main__':
    import numpy as np
    # import ct as ct
    from matplotlib import pyplot as plt

    with QHY() as qhy:
        qhy.initialize(stream_mode='single')
