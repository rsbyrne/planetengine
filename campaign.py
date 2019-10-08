import sys
import os
import shutil
import subprocess
import random

from . import wordhash
from . import mpi
from . import disk
from . import utilities
from . import planetengineDir
from . import _built

JOBPREFIX = 'pejob_'

_campaignStructure = (
    ('jobs', (
        ('completed', ()),
        ('running', ()),
        ('failed', ())
        )),
    ('out', (
        ('completed', ()),
        ('running', ()),
        ('failed', ())
        )),
    ('logs', (
        ('completed', ()),
        ('running', ()),
        ('failed', ())
        )),
    )

def load_job():
    JOBFILENAME = str(sys.argv[1])
    job = disk.load_json(JOBFILENAME)
    return job

class Campaign(_built.Built):

    name = 'campaign'

    def __init__(
            self,
            args,
            kwargs,
            inputs,
            script,
            _run,
            name = None,
            path = None,
            _pre_update = None,
            _post_update = None,
            ):

        if name is None:
            name = self.name
        if path is None:
            path = os.path.abspath(
                os.path.dirname(
                    script
                    )
                )
        del inputs['name']
        del inputs['path']

        self.fm = disk.FileManager(self.name, path)

        self._make_directory_structure()

        runshPath = os.path.join(self.fm.path, 'run.sh')
        if mpi.rank == 0:
            if not os.path.isfile(runshPath):
                shutil.copyfile(
                    os.path.join(planetengineDir, 'linux', 'run.sh'),
                    runshPath
                    )
                self.fm.liberate_path('run.sh')
        self.runsh = runshPath

        runpy = script
        runpyPath = os.path.join(self.fm.path, 'run.py')
        if mpi.rank == 0:
            if not os.path.isfile(runpyPath):
                shutil.copyfile(
                    runpy,
                    runpyPath
                    )
                self.fm.liberate_path('run.py')
        self.runpy = runpyPath

        planetenginePath = os.path.join(self.fm.path, 'planetengine')
        if mpi.rank == 0:
            if not os.path.isdir(planetenginePath):
                shutil.copytree(
                    planetengineDir,
                    planetenginePath
                    )
        self.planetengine = planetenginePath

        self._systemoutfile = os.path.join(self.fm.path, 'logs', 'system.out')
        self._systemerrorfile = os.path.join(self.fm.path, 'logs', 'system.error')
        if mpi.rank == 0:
            if not os.path.isfile(self._systemoutfile):
                os.mknod(self._systemoutfile)
            if not os.path.isfile(self._systemerrorfile):
                os.mknod(self._systemerrorfile)

        if not _pre_update is None:
            self._pre_update = _pre_update
        if not _post_update is None:
            self._post_update = _post_update
        if not _run is None:
            self._run = _run

        self.update()

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = script
            )

    def _pre_update(self):
        pass
    def _post_update(self):
        pass

    def update(self):
        self._pre_update()
        self.fm.update()
        self.jobs_available = {
            key[6:-5] for key in self.fm.directories['jobs'] \
                if key[:6] == 'pejob_'
            }
        self.jobs_running = {
            key[6:-5] for key in self.fm.directories['jobs']['running'] \
                if key[:6] == 'pejob_'
            }
        self.jobs_completed = {
            key[6:-5] for key in self.fm.directories['jobs']['completed'] \
                if key[:6] == 'pejob_'
            }
        self.jobs_failed = {
            key[6:-5] for key in self.fm.directories['jobs']['failed'] \
                if key[:6] == 'pejob_'
            }
        self.jobs = {
            *self.jobs_available,
            *self.jobs_running,
            *self.jobs_completed,
            *self.jobs_failed
            }
        self.fm.update()
        self._post_update()

    def run(self, jobID = None, cores = 1):
        print("Running!")
        self._run()
        print("Done!")

    def _make_directory_structure(self):
        campaignStructCheck = ([
            key in self.fm.directories for key in dict(_campaignStructure).keys()
            ])
        if not all(campaignStructCheck):
            if not any(campaignStructCheck):
                self.fm.make_directory_tree(_campaignStructure, exist_ok = True)
            else:
                raise Exception

    def add_job(self, job):
        jobString = utilities.stringify(job)
        jobID = wordhash.get_random_phrase(jobString)
        if not jobID in self.jobs:
            self.jobs_available.add(jobID)
            jobFile = JOBPREFIX + jobID
            self.fm.save_json(job, jobFile, 'jobs')
        self.update()

    def add_jobs(self, joblist):
        for job in joblist:
            self.add_job(job)

    def run_job(self, jobID = None, cores = 1):
        if jobID is None:
            jobID = random.choice(tuple(self.jobs_available))
        jobFilename = os.path.abspath(
            os.path.join(
                self.fm.directories['jobs']['.'],
                JOBPREFIX + jobID + '.json'
                )
            )
        with open(self._systemoutfile, 'a') as outfile:
            with open(self._systemerrorfile, 'a') as errorfile:
                ignoreme = subprocess.call(
                    ['sh', self.runsh, self.runpy, jobFilename],
                    stdout = outfile,
                    stderr = errorfile
                    )
