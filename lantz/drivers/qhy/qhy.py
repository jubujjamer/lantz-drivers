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

from lantz import Driver, Feat, Action, Q_
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

    @Feat(limits=(50, 3600E6))
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


    @Feat(limits=(0, 55)) # Units are ADU's
    def gain(self):
        # Implement the getter
        return 0

    @gain.setter
    def gain(self, gain=5):
        self.lib.set_gain.argtypes = [ct.c_void_p, ct.c_int]
        ret_value = self.lib.set_gain(self.handler, gain)
        if ret_value not in _OK.keys():
            raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value

    @Feat(limits=(0, 4096)) # Units are ADU's
    def offset(self):
        # Implement the getter
        return 0

    @offset.setter
    def offset(self, offset=10):
        self.lib.set_offset.argtypes = [ct.c_void_p, ct.c_int]
        ret_value = self.lib.set_offset(self.handler, offset)
        if ret_value not in _OK.keys():
            raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value

    @Feat(limits=(1, 250)) #
    def usb_traffic(self):
        # Implement the getter
        return 0

    @usb_traffic.setter
    def usb_traffic(self, usb_traffic=10):
        self.lib.set_usb_traffic.argtypes = [ct.c_void_p, ct.c_int]
        ret_value = self.lib.set_usb_traffic(self.handler, usb_traffic)
        if ret_value not in _OK.keys():
            raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value


    @Feat(values={'12MHz': 0, '24MHz': 1, '48MHz': 2})
    def control_speed(self):
        return 0

    @control_speed.setter
    def control_speed(self, cmos_speed='12MHz'):
        """Open camera self.open_camera.

        Not supported by the QHY183.

        Parameters
        ----------
        mode        int
                    0 for single frame mode and 1 for video mode.
        """
        cmos_speed = ct.c_int(cmos_speed)
        self.lib.set_control_speed.argtypes = [ct.c_void_p, ct.c_int]
        ret_value = self.lib.set_control_speed(self.handler, cmos_speed)
        return ret_value


    def roi(self, start_x=0, start_y=0, size_x=5544, size_y=3684):
        self.lib.set_resolution.argtypes = [ct.c_void_p, ct.c_int, ct.c_int,
                                            ct.c_int, ct.c_int]
        ret_value = self.lib.set_resolution(self.handler, start_x, start_y,
                                            size_x, size_y)
        if ret_value not in _OK.keys():
            raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value

    @property
    def bin_mode(self):
        return 0

    @bin_mode.setter
    def bin_mode(self, vals):
        bin_x, bin_y = vals
        self.lib.set_bin_mode.argtypes = [ct.c_void_p, ct.c_int, ct.c_int]
        ret_value = self.lib.set_bin_mode(self.handler, bin_x, bin_y)
        if ret_value not in _OK.keys():
            raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value

    @Feat(limits=(8, 16, 8))
    def bits_mode(self):
        return 0

    @bits_mode.setter
    def bits_mode(self, bits=16):
        self.lib.set_bits_mode.argtypes = [ct.c_void_p, ct.c_int]
        ret_value = self.lib.set_bits_mode(self.handler, bits)
        if ret_value not in _OK.keys():
            raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value

    @property
    def _memory_length(self):
        self.lib.get_memory_length.argtypes = [ct.c_void_p]
        length = self.lib.get_memory_length(self.handler)
        # if ret_value not in _OK.keys():
        #     raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return length

    # def _memory_length(self):
    #     self.lib.get_memory_length.argtypes = [ct.c_void_p]
    #     ret_value = self.lib.get_memory_length(self.handler)
    #     if ret_value not in _OK.keys():
    #         raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
    #     return ret_value

    def get_ccd_info(self):
        # int_array = ct.c_int_p
        # ia = IntArray5(5, 1, 7, 33, 99)
        int_array = ct.c_double*7
        # array_pointer = ctypes.cast(output, ct.POINTER(int_array))
        self.lib.get_ccd_info.argtypes = [ct.c_void_p]
        self.lib.get_ccd_info.restype = ct.POINTER(int_array) #ct.c_void_p #ct.POINTER(ct.c_int)
        ccd_info = self.lib.get_ccd_info(self.handler)
        chip_info = np.frombuffer(ccd_info.contents)
        width_mm, height_mm, width_px, height_px, max_x, max_y, bpp = chip_info
        width_px, height_px = int(width_px), int(height_px)
        mm = Q_(1, 'mm')
        px = Q_(1, 'pixel')
        self.width_mm = width_mm * mm
        self.height_mm = height_mm * mm
        self.width_px = width_px * px
        self.height_px = height_px * px
        self.max_x = int(max_x)
        self.max_y = int(max_y)
        return chip_info

    def is_color(self):
        self.lib.is_color.argtypes = [ct.c_void_p]
        ret_value = self.lib.is_color(self.handler)
        # if ret_value not in _OK.keys():
        #     raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value

    @Action()
    def _expose(self):
        self.lib.get_single_frame.argtypes = [ct.c_void_p]
        ret_value = self.lib.get_single_frame(self.handler)
        # if ret_value not in _OK.keys():
        #     raise errors.InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value

    @Action()
    def get_frame(self, roi_x, roi_y):
        length = self._memory_length
        char_array = ct.c_int16*(length)
        self.lib.get_single_frame.argtypes = [ct.c_void_p, ct.c_int, ct.c_int, ct.c_int]
        self.lib.get_single_frame.restype = ct.POINTER(char_array)
        print('length', length)
        p_img_data = self.lib.get_single_frame(self.handler, roi_x, roi_y, length)
        img = np.copy(np.frombuffer(p_img_data.contents))
        print(len(img))
        print(img.resize(5544, 3684))
        return p_img_data

    @Action()
    def cancel_exposure(self):
        self.lib.cancel_exposure.argtypes = [ct.c_void_p]
        ret_value = self.lib.cancel_exposure(self.handler)
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
        qhy.exposure = 100000
        qhy.gain = 30
        qhy.offset = 100
        qhy.usb_traffic = 10
        qhy.control_speed = '12MHz'
        qhy.roi(0, 0, 500, 500)
        qhy.bin_mode = (1, 1)
        qhy.bits_mode = 16
        qhy.get_ccd_info()
        qhy.is_color()
        qhy._expose()
        img = qhy.get_frame(roi_x=qhy.max_x, roi_y=qhy.max_x)
        qhy.close()
        qhy.finalize()
