import underworld as uw
import numpy as np
import os
from PIL import Image

from .. import mpi
from .. import fieldops
from ..utilities import message
from .. import functions as pfn
from . import fig

class Data:
    def __init__(self, inVar, size = (16, 16)):
        mesh = uw.mesh.FeMesh_Cartesian(
            elementRes = size
            )
        self.var = mesh.add_variable(1)
        self.var.scales = [[-128., 127.]]
        self.inVar = pfn.projection.get_meshVar(inVar)
        self.size = size
        self.update()
    def update(self):
        tolerance = fieldops.copyField(
            self.inVar,
            self.var
            )
        data = self.var.evaluate_global(self.var.mesh.subMesh.data)
        if mpi.rank == 0:
            data = data.flatten()
            data = data.reshape(self.size[::-1])
            data = np.flip(data, axis = 0) # makes it top-bottom
            data = data.astype('int8')
        data = mpi.comm.bcast(data, root = 0)
        self.data = data

class Raster(fig.Fig):
    '''
    Modes: 1, L, P, RGB, RGBA, CMYK, YCbCr, LAB, HSV, I, F, RGBa, LA, RGBX
    '''
    def __init__(self, *bands, size = (16, 16), mode = None, **kwargs):
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
        self.dataObjs = [Data(band, size = size) for band in bands]
        self.shape = [*size, len(self.dataObjs)]
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
        self.img = img
    def _save(self, path, name, ext):
        self.img.save(os.path.join(path, name + '.' + ext))
    def _show(self):
        self.update()
    def evaluate(self):
        self.update()
        return self.data
