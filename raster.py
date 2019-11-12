import underworld as uw
import numpy as np
import os
from . import mpi
from . import fieldops
from .utilities import message
from . import functions as pfn
from PIL import Image

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
        data = None
        if mpi.rank == 0:
            data = self.var.evaluate_global(self.var.mesh.subMesh.data)
            data = data.flatten()
            data = data.reshape(self.size[::-1])
            data = np.flip(data, axis = 0) # makes it top-bottom
            data = data.astype('int8')
        data = mpi.comm.bcast(data, root = 0)
        self.data = data

class Raster:
    '''
    Modes: 1, L, P, RGB, RGBA, CMYK, YCbCr, LAB, HSV, I, F, RGBa, LA, RGBX
    '''
    def __init__(self, *args, size = (16, 16), mode = 'L', name = 'anon', add = None):
        self.name = name
        self.mode = mode
        self.add = add
        self.dataObjs = [Data(arg, size = size) for arg in args]
        self.update()
    def update(self):
        self._update_data()
        self._update_img()
    def _update_data(self):
        for dataObj in self.dataObjs:
            dataObj.update()
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
    def save(self, path = '', name = None, add = None, ext = 'png'):
        self.update()
        if name is None:
            name = self.name
        if add is None:
            if not self.add is None:
                add = self.add
            else:
                add = ''
        if callable(add):
            add = add()
        if type(add) == int:
            add = '_' + str(add).zfill(8)
        elif len(add) > 0:
            add = '_' + str(add)
        name += add
        if mpi.rank == 0:
            if not os.path.isdir(path):
                os.makedirs(path)
            assert os.path.isdir(path)
        # mpi.barrier()
        self.img.save(os.path.join(path, name + '.' + ext))
