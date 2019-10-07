import os
import shutil
import subprocess
import random

from . import wordhash
from . import mpi
from . import disk
from . import utilities
from . import planetengineDir

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

class Campaign:

    def __init__(self, name, path, runpy):

        self.fm = disk.FileManager(name, path)

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

        self.update()

    def _update(self):
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

    def update(self):
        self._update()

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
        with open(self._systemoutfile, 'a') as outfile:
            with open(self._systemerrorfile, 'a') as errorfile:
                ignoreme = subprocess.call(
                    ['sh', self.runsh, self.runpy, jobID],
                    stdout = outfile,
                    stderr = errorfile
                    )
