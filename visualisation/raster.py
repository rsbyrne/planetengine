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
    def __init__(self, var, size, normInterval = [0.0001, 254.9999]):
        self.var = pfn.convert(var)
        if self.var.varDim > 1:
            raise Exception
        self.grid = np.vstack(
            np.dstack(
                np.meshgrid(
                    np.linspace(0., 1., size[0]),
                    np.linspace(1., 0., size[1])
                    )
                )
            )
        self.size = size
        self.normInterval = normInterval
        self.update()
    def update(self):
        data = fieldops.safe_box_evaluate(
            self.var,
            self.grid
            )
        data = mapping.rescale_array(
            data,
            self.var.scaleFn(),
            [self.normInterval for dim in range(data.shape[-1])]
            )
        data = np.round(data).astype('uint8')
        data = np.reshape(data, self.size[::-1])
        self.data = data

def split_imgArr(imgArr):
    outArrs = [
        np.reshape(arr, arr.shape[:2]) \
            for arr in np.split(
                imgArr,
                imgArr.shape[-1],
                axis = -1
                )
        ]
    return outArrs

def rasterise(*datas, mode = 'RGB'):
    bands = []
    for data in datas:
        band = Image.fromarray(
            data,
            mode = 'L',
            )
        bands.append(band)
    img = Image.merge(mode, bands)
    return img

class Raster(fig.Fig):
    '''
    Modes: 1, L, P, RGB, RGBA, CMYK, YCbCr, LAB, HSV, I, F, RGBa, LA, RGBX
    '''
    def __init__(self, *bands, mode = None, size = (256, 256), **kwargs):
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
        self.dataObjs = [
            Data(band, size = size) \
                for band in bands
            ]
        self.shape = [*size[::-1], len(self.dataObjs)]
        self.data = np.zeros(self.shape, dtype = 'uint8')
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
        self.img = rasterise(
            *[dataObj.data for dataObj in self.dataObjs],
            mode = self.mode
            )
    def _save(self, path, name, ext):
        self.img.save(os.path.join(path, name + '.' + ext))
    def _show(self):
        self.update()
        return self.img
    def evaluate(self):
        self.update()
        return self.data.copy()
    def enlarge(self, factor = 4):
        return self.img.resize(
            factor * np.array(self.shape[:2])[::-1]
            )
    def resize(self, size = (256, 256)):
        return self.img.resize(size)
