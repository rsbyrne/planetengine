import sys
workPath = '/home/jovyan/workspace'
if not workPath in sys.path:
    sys.path.append(workPath)

import os

import planetengine
from planetengine import quickShow
from planetengine import functions as pfn
from planetengine import disk
from planetengine import mpi

system = planetengine.tests.testsystems.arrhenius()

with planetengine.paths.TestDir() as testPath:

    with disk.Archiver('test', testPath) as diskmate:
        diskmate.save_module(system.script)
        diskmate.save_json({'Hello': 'World'}, 'info')
        diskmate.save_vars(system.varsOfState, 'vars')
        if mpi.rank == 0:
            os.mkdir(os.path.join(diskmate.path, 'testtar1'))
        disk.make_tar(os.path.join(diskmate.path, 'testtar1'))
        if mpi.rank == 0:
            os.mkdir(os.path.join(diskmate.path, 'testdir1'))
            os.mkdir(os.path.join(os.path.join(diskmate.path, 'testdir1'), 'testtar2'))
        disk.make_tar(os.path.join(os.path.join(diskmate.path, 'testdir1'), 'testtar2'))
        if mpi.rank == 0:
            os.mkdir(os.path.join(diskmate.path, 'testdir2'))
            os.mkdir(os.path.join(os.path.join(diskmate.path, 'testdir2'), 'testtar3'))
        diskmate.save_json({'Foo': 'Bar'}, 'subinfo', subPath = os.path.join('testdir2', 'testtar3'))
        disk.make_tar(os.path.join(os.path.join(diskmate.path, 'testdir2'), 'testtar3'))
        disk.make_tar(os.path.join(diskmate.path, 'testdir2'))

    was_tarred = disk.expose_tar(os.path.join(testPath, 'test'), recursive = True)

    disk.make_tar(os.path.join(testPath, 'test'), was_tarred)

    with disk.Archiver('test', testPath) as diskmate:
        mymodule = diskmate.load_module('arrhenius')
        myjson = diskmate.load_json('info')
        myjson2 = diskmate.load_json('subinfo', subPath = os.path.join('testdir2', 'testtar3'))
        if mpi.rank == 0:
            os.mkdir(os.path.join(diskmate.path, 'newdir'))
        myjson3 = diskmate.save_json([0, 1, 2, 3], 'newjson', subPath = os.path.join(diskmate.path, 'newdir'))
        diskmate.load_vars(system.varsOfState, 'vars')

    with disk.Archiver('test', testPath) as diskmate:
        diskmate.load_json('newjson', subPath = os.path.join(diskmate.path, 'newdir'))
