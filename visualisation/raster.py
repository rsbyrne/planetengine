import numpy as np
from scipy.interpolate import griddata
import os
from PIL import Image
import shutil
import subprocess
from subprocess import PIPE

from everest import disk
from everest import mpi

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

def rasterise(*datas):
    bands = []
    for data in datas:
        band = Image.fromarray(
            data,
            mode = 'L',
            )
        bands.append(band)
    mode, bands = get_mode(*bands)
    img = Image.merge(mode, bands)
    return img

def get_mode(*bands):
    '''
    Modes: 1, L, P, RGB, RGBA, CMYK, YCbCr, LAB, HSV, I, F, RGBa, LA, RGBX
    '''
    if len(bands) == 1:
        mode = 'L'
    elif len(bands) <= 3:
        if len(bands) == 2:
            bands = [*bands, bands[-1]]
        mode = 'RGB'
    elif len(bands) == 4:
        mode = 'CMYK'
    else:
        raise Exception("Too many bands!")
    return mode, bands

class Raster(fig.Fig):
    def __init__(self, *bands, size = (256, 256), **kwargs):
        mode, ignoreme = get_mode(*bands)
        self.dataObjs = [Data(band, size = size) for band in bands]
        self.shape = [*size[::-1], len(self.dataObjs)]
        self.data = np.zeros(self.shape, dtype = 'uint8')
        if mode == 'CMYK': ext = 'jpg'
        else: ext = 'png'
        super().__init__(ext = ext, **kwargs)
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
        self.img = rasterise(*[dataObj.data for dataObj in self.dataObjs])
    def _save(self, name, path, ext):
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

@mpi.dowrap
def animate(datas, name, outputPath = '.', overwrite = False):
    outputPath = os.path.abspath(outputPath)
    outputFilename = os.path.join(outputPath, name + '.mp4')
    if not overwrite:
        if os.path.exists(outputFilename):
            raise Exception("Output file already exists!")
    tempDir = os.path.join(outputPath, disk.tempname(_mpiignore_ = True))
    inputFilename = os.path.join(tempDir, '*.jpg')
    shutil.rmtree(tempDir, ignore_errors = True)
    os.makedirs(tempDir)
    try:
        for i, data in enumerate(datas):
            split = [data[:,:,i] for i in range(data.shape[-1])]
            im = rasterise(*split)
            im.save(os.path.join(tempDir, str(i).zfill(8)) + '.jpg')
        cmd = [
            'ffmpeg',
            '-y',
            '-pattern_type',
            'glob',
            '-i',
            '"' + inputFilename + '"',
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            '-movflags',
            '+faststart',
            outputFilename
            ]
        cmd = ' '.join(cmd)
        completed = subprocess.run(
            cmd,
            stdout = PIPE,
            stderr = PIPE,
            shell = True,
            check = True
            )
    finally:
        shutil.rmtree(tempDir, ignore_errors = True)
