import sys
workPath = '/home/jovyan/workspace'
if not workPath in sys.path:
    sys.path.append(workPath)

import os

import planetengine
from planetengine import disk

def testfn():

    system = planetengine.tests.testsystems.arrhenius()

    with planetengine.paths.TestDir() as testPath:

        with disk.expose('test', testPath, archive = True) as filemanager:
            filemanager.save_module(system.script)
            filemanager.save_json({'Hello': 'World'}, 'info')
            filemanager.save_vars(system.varsOfState, 'vars')
            filemanager.mkdir('testtar1')
            disk.make_tar(os.path.join(filemanager.path, 'testtar1'))
            filemanager.mkdir('testdir1')
            filemanager.mkdir(os.path.join('testdir1', 'testtar2'))
            disk.make_tar(os.path.join(os.path.join(filemanager.path, 'testdir1'), 'testtar2'))
            filemanager.mkdir('testdir2')
            filemanager.mkdir(os.path.join('testdir2', 'testtar3'))
            filemanager.save_json({'Foo': 'Bar'}, 'subinfo', subPath = os.path.join('testdir2', 'testtar3'))
            disk.make_tar(os.path.join(os.path.join(filemanager.path, 'testdir2'), 'testtar3'))
            disk.make_tar(os.path.join(filemanager.path, 'testdir2'))

        with disk.expose('test', testPath) as filemanager:
            mymodule = filemanager.load_module('arrhenius')
            myjson = filemanager.load_json('info')
            myjson2 = filemanager.load_json('subinfo', subPath = os.path.join('testdir2', 'testtar3'))
            filemanager.mkdir('newdir')
            myjson3 = filemanager.save_json([0, 1, 2, 3], 'newjson', subPath = os.path.join(filemanager.path, 'newdir'))
            filemanager.load_vars(system.varsOfState, 'vars')

        with disk.expose('test', testPath) as filemanager:
            filemanager.load_json('newjson', subPath = os.path.join(filemanager.path, 'newdir'))
