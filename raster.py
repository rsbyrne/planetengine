import underworld as uw
import numpy as np
from . import mpi
from . import fieldops
from .utilities import message
from . import functions as pfn
from PIL import Image

class Data:
    def __init__(self, inVar, size = 16):
        mesh = uw.mesh.FeMesh_Cartesian(
            elementRes = (size, size)
            )
        self.var = mesh.add_variable(1)
        self.var.scales = [[-128., 127.]]
        self.inVar = pfn.projection.get_meshVar(inVar)
        self.size = size
        self.data = np.zeros((size, size)).astype('int8')
        self.update()
    def update(self):
        tolerance = fieldops.copyField(
            self.inVar,
            self.var
            )
        data = None
        if mpi.rank == 0:
            data = self.var.evaluate_global(self.var.mesh.subMesh.data)
            data = data.reshape([self.size, self.size])
            data = np.flip(data, axis = 0)
            data = data.astype('int8')
        data = mpi.comm.bcast(data, root = 0)
        self.data[...] = data

class Raster:
    def __init__(self, *args, size = 16):
        if len(args) == 1:
            dim = 1
            mode = 'L'
        elif len(args) == 2:
            dim = 2
            mode = 'RGB'
        elif len(args) == 3:
            dim = 3
            mode = 'RGB'
        else:
            raise Exception
        self.dataObjs = [Data(arg, size = size) for arg in args]
        self.dataArrays = [dataObj.data for dataObj in self.dataObjs]
        if dim == 2:
            zerodata = np.zeros((size, size)).astype('int8')
            self.dataArrays.append(zerodata)
        self.img = Image.new(
            mode,
            (size, size),
            "black"
            )
        self.update()
    def update(self):
        self._update_data()
        self._update_img()
    def _update_data(self):
        for dataObj in self.dataObjs:
            dataObj.update()
    def _update_img(self):
        pixels = self.img.load()
        for i in range(self.img.size[0]):
            for j in range(self.img.size[1]):
                pixels[i, j] = tuple([
                    dataArray[j, i] + 128 \
                        for dataArray in self.dataArrays
                    ])
