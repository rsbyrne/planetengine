import os
import json
import shutil
import tarfile
import importlib
import traceback
import random
import underworld as uw
from underworld import function as fn

from . import utilities
from .utilities import message
from .functions import _basetypes
from . import paths

from . import mpi

def expose(name, outputPath = '.', archive = None, recursive = True):
    return _FileContextManager(name, outputPath, archive, recursive)

from . import _built

def disk_state(path):
    path = os.path.splitext(path)[0]
    tarpath = path + '.tar.gz'
    diskstate = ''
    if mpi.rank == 0:
        isfile = os.path.isfile(tarpath)
        isdir = os.path.isdir(path)
        assert not (isfile and isdir)
        if isfile:
            diskstate = 'tar'
        elif isdir:
            diskstate = 'dir'
        else:
            diskstate = 'clean'
    diskstate = mpi.comm.bcast(diskstate, root = 0)
    return diskstate

def save_json(jsonObj, name, path):
    if mpi.rank == 0:
        jsonFilename = os.path.join(path, name + '.json')
        with open(jsonFilename, 'w') as file:
             json.dump(jsonObj, file)
    # mpi.barrier()

def load_json(jsonName, path):
    filename = jsonName + '.json'
    jsonDict = {}
    if mpi.rank == 0:
        with open(os.path.join(path, filename)) as json_file:
            jsonDict = json.load(json_file)
    jsonDict = mpi.comm.bcast(jsonDict, root = 0)
    return jsonDict

def local_import(filepath):

    modname = os.path.basename(filepath)

    spec = importlib.util.spec_from_file_location(
        modname,
        filepath,
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def save_script(script, name = None, path = '.'):
    if name is None:
        name = os.path.splitext(
            os.path.basename(
                script
                )
            )[0]
    if mpi.rank == 0:
        tweakedPath = os.path.splitext(script)[0] + ".py"
        newPath = os.path.join(path, name + ".py")
        shutil.copyfile(tweakedPath, newPath)
    # mpi.barrier()

def load_script(name, path):
    scriptPath = os.path.join(path, name) + '.py'
    scriptModule = local_import(
        scriptPath
        )
    return scriptModule

def expose_tar(path, recursive = False, rmtar = True, outName = None):

    tarpath = path + '.tar.gz'
    if not outName is None:
        path = outName

    if mpi.rank == 0:
        if not os.path.isfile(tarpath):
            raise Exception("No tar by that name found.")
        if os.path.isdir(path):
            raise Exception("Output dir already exists.")

    message("Tar found - unarchiving...")
    if mpi.rank == 0:
        with tarfile.open(tarpath) as tar:
            tar.extractall(path)
        assert os.path.isdir(path), \
            "Archive contained the wrong model file somehow."
        if rmtar:
            os.remove(tarpath)
            assert not os.path.isfile(tarpath)

    message("Unarchived.")

    if recursive:
        was_tarred = expose_sub_tars(path)
        return was_tarred

def try_expose_tar(path, **kwargs):
    if disk_state(path) == 'tar':
        expose_tar(path)
        return True
    return False

def make_tar(
        path,
        was_tarred = [],
        rmdir = True,
        outName = None,
        compression = 'gz'
        ):

    if outName is None:
        tarpath = path + '.tar'
        if not compression is None:
            tarpath += '.' + compression

    else:
        tarpath = outName

    if mpi.rank == 0:
        if os.path.isfile(tarpath):
            raise Exception("Output tar already exists.")
        if not os.path.isdir(path):
            raise Exception("Input dir not found.")

    message("Archiving...")

    if len(was_tarred) > 0:
        un_expose_sub_tars(was_tarred)

    if mpi.rank == 0:
        mode = 'w'
        if not compression is None:
            mode += ':' + compression
        with tarfile.open(tarpath, mode) as tar:
            tar.add(path, arcname = '')
        assert os.path.isfile(tarpath), \
            "The archive should have been created, but it wasn't!"
        if rmdir:
            shutil.rmtree(path)
            assert not os.path.isdir(path), \
                "The directory should have been deleted, but it's still there!"

    message("Archived.")

def try_make_tar(path, **kwargs):
    if disk_state(path) == 'dir':
        make_tar(path)
        return True
    return False

def expose_sub_tars(path):
    subDirs = listdir(path)
    was_tarred = []
    for file in subDirs:
        filePath = os.path.join(path, file)
        if file[-7:] == '.tar.gz':
            dirName = os.path.splitext(
                os.path.splitext(
                    file
                    )[0]
                )[0]
            dirPath = os.path.join(path, dirName)
            expose_tar(dirPath)
            was_tarred.append(dirPath)
            was_tarred.extend(expose_sub_tars(dirPath))
        elif os.path.isdir(filePath):
            was_tarred.extend(expose_sub_tars(filePath))
    return was_tarred

def un_expose_sub_tars(was_tarred):
    if len(was_tarred) > 0:
        for path in was_tarred[::-1]:
            make_tar(path)
    else:
        pass

def make_dir(path, exist_ok = True):

    assert not disk_state(path) == 'tar'

    if mpi.rank == 0:
        if not os.path.isdir(path):
            os.makedirs(path)
        else:
            if not exist_ok:
                raise Exception("Dir already exists.")

    assert disk_state(path) == 'dir'

def listdir(path):
    dirs = []
    if mpi.rank == 0:
        dirs = os.listdir(path)
    dirs = mpi.comm.bcast(dirs, root = 0)
    return dirs

def makedirs(path, exist_ok = False):
    os.makedirs(path, exist_ok = exist_ok)

def explore_tree(path):
    directories = {}
    path = os.path.abspath(path)
    files = listdir(path)
    for file in files:
        if not file[:2] == '__':
            filePath = os.path.join(path, file)
            if os.path.isfile(filePath):
                directories[file] = '.'
            elif os.path.isdir(filePath):
                directories[file] = explore_tree(filePath)
    return directories

def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False

# def save_tree(objDict, path):

def load_tree(path):
    path = os.path.abspath(path)
    directories = explore_tree(path)
    loaded = {}
    for key, val in sorted(directories.items()):
        if type(val) == dict:
            subtree = os.path.join(path, key)
            loaded[key] = load_tree(subtree)
        else:
            name, ext = os.path.splitext(key)
            if ext == '.json':
                obj = load_json(name, path)
            elif ext == '.py' or ext == '.pyc':
                obj = load_script(name, path)
            else:
                obj = None
            loaded[name] = obj
    return loaded

def varsOnDisk(
        saveVars,
        checkpointDir,
        mode = 'save',
        blackhole = [0., 0.]
        ):

    substrates = []
    substrateNames = []
    substrateHandles = {}
    extension = '.h5'

    # assert disk_state(checkpointDir) == 'dir'

    for varName, var in sorted(saveVars.items()):

        if type(var) == fn.misc.constant:
            if mode == 'save':
                save_json(var.value, varName, checkpointDir)
            elif mode == 'load':
                var.value = load_json(varName, checkpointDir)
            break

        if type(var) == _basetypes.Variable:
            var.update()
            var = var.var

        if type(var) == uw.mesh._meshvariable.MeshVariable:
            substrate = var.mesh
            substrateName = 'mesh'
        elif type(var) == uw.swarm._swarmvariable.SwarmVariable:
            substrate = var.swarm
            substrateName = 'swarm'
        else:
            raise Exception('Variable type not recognised.')

        if not substrate in substrates:
            if substrateName in substrateNames:
                nameFound = False
                suffix = 0
                while not nameFound:
                    adjustedSubstrateName = substrateName + '_' + str(suffix)
                    if not adjustedSubstrateName in substrateNames:
                        substrateName = adjustedSubstrateName
                        nameFound = True
                    else:
                        suffix += 1
            substrateNames.append(substrateName)

            if mode == 'save':
                message("Saving substrate to disk: " + substrateName)
                handle = substrate.save(
                    os.path.join(
                        checkpointDir,
                        substrateName + extension
                        )
                    )
                # substrateHandles[substrateName] = handle
                substrateHandles[substrate] = handle
            elif mode == 'load':
                message("Loading substrate from disk: " + substrateName)
                if type(substrate) == uw.swarm.Swarm:
                    with substrate.deform_swarm():
                        substrate.particleCoordinates.data[:] = blackhole
                    assert substrate.particleGlobalCount == 0
                substrate.load(os.path.join(checkpointDir, substrateName + extension))
            else:
                raise Exception("Disk mode not recognised.")
            substrates.append(substrate)

        else:
            if mode == 'save':
                handle = substrateHandles[substrate]

        if mode == 'save':
            message("Saving var to disk: " + varName)
            var.save(os.path.join(checkpointDir, varName + extension), handle)
        elif mode == 'load':
            message("Loading var from disk: " + varName)
            var.load(os.path.join(checkpointDir, varName + extension))
        else:
            raise Exception("Disk mode not recognised.")

class _FileContextManager:

    def __init__(
            self,
            name,
            outputPath = '.',
            archive = True,
            recursive = True
            ):

        self.name = name
        self.outputPath = os.path.abspath(outputPath)
        self.path = os.path.join(outputPath, name)
        self.tarpath = self.path + '.tar.gz'
        self.archive = archive
        self.recursive = recursive
        self._initial_diskState = disk_state(self.path)

        _backupdir_found = False
        while not _backupdir_found:
            self._backupfile = os.path.join(
                self.outputPath,
                '.' + str(random.randint(1e18, 1e19 - 1)) + '.tar'
                )
            if mpi.rank == 0:
                if not os.path.isfile(self._backupfile):
                    _backupdir_found = True
            _backupdir_found = mpi.comm.bcast(_backupdir_found, root = 0)

    def _save_backup(self):
        if self._initial_diskState == 'clean':
            pass
        else:
            if self._initial_diskState == 'dir':
                path = self.path
            else:
                path = self.tarpath
            if mpi.rank == 0:
                assert not os.path.isfile(self._backupfile)
                with tarfile.open(self._backupfile, 'w') as tar:
                    tar.add(path, arcname = '')
                assert os.path.isfile(self._backupfile)

    def _load_backup(self):
        if self._initial_diskState == 'clean':
            pass
        else:
            if mpi.rank == 0:
                if os.path.isfile(self.tarpath):
                    os.remove(self.tarpath)
                if os.path.isdir(self.path):
                    shutil.rmtree(self.path)
                assert os.path.isfile(self._backupfile)
                if self._initial_diskState == 'dir':
                    extractPath = self.path
                else:
                    extractPath = self.tarpath
                with tarfile.open(self._backupfile) as tar:
                    tar.extractall(extractPath)
                if self._initial_diskState == 'dir':
                    assert os.path.isdir(self.path)
                else:
                    assert os.path.isfile(self.tarpath)

    def _remove_backup(self):
        if mpi.rank == 0:
            if os.path.isfile(self._backupfile):
                os.remove(self._backupfile)

    def _try_archive(self):
        archiveConditions = [
            (self.archive == True),
            (self.archive is None and self.was_archived)
            ]
        if any(archiveConditions):
            make_tar(self.path)
            assert disk_state(self.path) == 'tar'
        else:
            assert disk_state(self.path) == 'dir'

    def __enter__(self):
        self._save_backup()
        diskState = self._initial_diskState
        if diskState == 'clean':
            make_dir(self.path, exist_ok = False)
            was_archived = None
        elif diskState == 'dir':
            was_archived = False
        elif diskState == 'tar':
            expose_tar(self.path)
            was_archived = True
        if self.recursive:
            self.subtars = expose_sub_tars(self.path)
        self.was_archived = was_archived
        return FileManager(self.name, self.outputPath)

    def __exit__(self, *args):
        exc_type, exc_value, tb = args
        if exc_type is None:
            if self.recursive:
                if len(self.subtars) > 0:
                    un_expose_sub_tars(self.subtars)
            self._try_archive()
            self._remove_backup()
            return True
        else:
            message("Failed! Reverting to backup.")
            traceback.print_exception(exc_type, exc_value, tb)
            self._load_backup()
            if not self._initial_diskState == 'tar':
                self._try_archive()
            self._remove_backup()
            return False

class FileManager:

    def __init__(self, name, outputPath = '.'):
        self.name = name
        self.outputPath = os.path.abspath(outputPath)
        self.path = os.path.join(outputPath, name)
        self._update()

    def _get_path(self, subPath):
        path = os.path.join(self.path, subPath)
        make_dir(path, exist_ok = True)
        return path

    def _get_directories(self):
        self.directories = explore_tree(self.path)

    def _update(self):
        self._get_directories()

    def mkdir(self, subPath, **kwargs):
        if mpi.rank == 0:
            os.mkdir(
                os.path.join(self.path, subPath),
                **kwargs
                )
        self._update()

    def rmdir(self, subPath, **kwargs):
        if mpi.rank == 0:
            os.rmdir(
                os.path.join(self.path, subPath),
                **kwargs
                )
        self._update()

    def makedirs(self, subPath, **kwargs):
        if mpi.rank == 0:
            os.makedirs(
                os.path.join(self.path, subPath),
                **kwargs
                )
        self._update()

    def removedirs(self, subPath, **kwargs):
        if mpi.rank == 0:
            os.removedirs(
                os.path.join(self.path, subPath),
                **kwargs
                )
        self._update()

    def rmtree(self, subPath, **kwargs):
        if mpi.rank == 0:
            shutil.rmtree(
                os.path.join(self.path, subPath),
                **kwargs
                )
        self._update()

    def copytree(self, *args, **kwargs):
        if mpi.rank == 0:
            shutil.copytree(
                *args,
                **kwargs
                )
        self._update()

    def copyfrom(self, src, subPath = '', **kwargs):
        self.copytree(
            src,
            os.path.join(self.path, subPath),
            **kwargs
            )
        self._update()

    def copyto(self, dst, subPath = '', **kwargs):
        self.copytree(
            os.path.join(self.path, subPath),
            dst,
            **kwargs
            )
        self._update()

    def listdir(self, subPath = ''):
        path = os.path.join(self.path, subPath)
        return listdir(path)

    # def save_tree(self, saveDict):
    #     pass
    #
    # def load_tree(self):
    #     pass

    def save_json(self, object, objName, subPath = ''):
        save_json(
            object,
            objName,
            self._get_path(subPath)
            )
        self._update()

    def load_json(self, objName, subPath = ''):
        return load_json(
            objName,
            self._get_path(subPath)
            )

    def save_module(self, script, name = None, subPath = ''):
        save_script(
            script,
            name,
            self._get_path(subPath)
            )
        self._update()

    def load_module(self, name, subPath = ''):
        return load_script(
            name,
            self._get_path(subPath)
            )

    def save_vars(self, varDict, subPath = ''):
        varsOnDisk(
            varDict,
            self._get_path(subPath),
            mode = 'save'
            )
        self._update()

    def load_vars(self, varDict, subPath = ''):
        varsOnDisk(
            varDict,
            self._get_path(subPath),
            mode = 'load'
            )

    def save_built(self, built, name, subPath = ''):
        _built.save_built(
            built,
            name,
            self._get_path(subPath)
            )
        self._update()

    def load_built(self, name, subPath = ''):
        return _built.load_built(
            name,
            self._get_path(subPath)
            )

    def save_builtsDir(self, builts, subPath = ''):
        _built.save_builtsDir(
            builts,
            self.path,
            subPath
            )
        self._update()

    def load_builtsDir(self, subPath = ''):
        return _built.load_builtsDir(
            self.path,
            subPath
            )
