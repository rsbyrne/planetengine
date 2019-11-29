import underworld as uw
import numpy as np
from scipy.interpolate import griddata
import os
from PIL import Image

from .. import fieldops
from .. import mapping
from .. import utilities
from .. import functions as pfn
from . import fig

STANDARD_SIZE = (256, 256)

class Data:
    def __init__(self, inVar, size = (256, 256)):
        self.var = pfn.normalise.default(inVar, [-128., 127.])
        self.grid = np.vstack(
            np.dstack(
                np.meshgrid(
                    np.linspace(0., 1., size[0]),
                    np.linspace(0., 1., size[1])
                    )
                )
            )
        self.fromMesh = utilities.get_mesh(self.var)
        self.size = size
        self.update()
    def update(self):
        data = fieldops.safe_box_evaluate(
            self.var,
            self.grid
            )
        data = data.reshape(self.size)
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
