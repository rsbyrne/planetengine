import underworld as uw
import numpy as np
import os
from PIL import Image

from .. import mpi
from .. import fieldops
from .. import mapping
from ..utilities import message
from .. import functions as pfn
from . import fig

STANDARD_SIZE = (256, 256)

class Data:
    def __init__(self, inVar):
        self.var = pfn.normalise.default(inVar, [-128., 127.])
        self.update()
    def update(self):
        # grid = np.vstack(
        #     np.dstack(
        #         np.meshgrid(
        #             np.linspace(0., 1., 256),
        #             np.linspace(0., 1., 256)
        #             )
        #         )
        #     )
        # data, tolerance = mapping.safe_local_box_evaluate(
        #     self.var,
        #     grid
        #     )
        # data = data.flatten().reshape((256, 256))
        # raise Exception(data)
        data = fieldops.get_global_var_data(self.var, subMesh = True)
        data = data.reshape(self.var.mesh.elementRes[::-1])
        data = np.flip(data, axis = 0) # makes it top-bottom
        data = np.flip(data, axis = 1) # makes it top-bottom
        data = data.T
        data = data.astype('int8')
        self.data = data

class Raster(fig.Fig):
    '''
    Modes: 1, L, P, RGB, RGBA, CMYK, YCbCr, LAB, HSV, I, F, RGBa, LA, RGBX
    '''
    def __init__(self, *bands, mode = None, **kwargs):
        if mode is None:
            if len(bands) == 1:
                mode = 'L'
            elif len(bands) <= 3:
                if len(bands) == 2:
                    bands = [*bands, bands[-1]]
                mode = 'RGB'
            else:
                raise Exception("Too many bands!")
        self.mode = mode
        self.dataObjs = [Data(band) for band in bands]
        self.shape = [*self.dataObjs[0].data.shape, len(self.dataObjs)]
        self.data = np.zeros(self.shape, dtype = 'int8')
        super().__init__(**kwargs)
        self.update()
    def _update(self):
        self._update_data()
        self._update_img()
    def _update_data(self):
        for dataObj in self.dataObjs:
            dataObj.update()
        self.data[...] = np.dstack(
            [dataObj.data for dataObj in self.dataObjs]
            )
    def _update_img(self):
        bands = []
        for dataObj in self.dataObjs:
            band = Image.fromarray(
                dataObj.data + 127,
                mode = 'L',
                )
            bands.append(band)
        img = Image.merge(self.mode, bands)
        self.bands = bands
        # self.img = img.resize(STANDARD_SIZE)
        self.img = img
    def _save(self, path, name, ext):
        self.img.save(os.path.join(path, name + '.' + ext))
    def _show(self):
        self.update()
    def evaluate(self):
        self.update()
        return self.data
    def enlarge(self, factor = 4):
        return self.img.resize(
            factor * np.array(self.shape[:2])[::-1]
            )
