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
        ('failed', ()),
        ('available', ())
        )),
    ('out', (
        ('completed', ()),
        ('failed', ())
        )),
    ('logs', (
        ('completed', ()),
        ('failed', ())
        )),
    )

def get_jobID(job):
    jobString = utilities.stringify(job)
    jobID = JOBPREFIX + wordhash.get_random_phrase(jobString)
    return jobID

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
                    os.path.dirname(
                        script
                        )
                    )
                )
        del inputs['name']
        del inputs['path']

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = script
            )

        self.fm = disk.FileManager(self.name, path)

        if not 'campaign_0.py' in self.fm.directories:
            self.save(path = self.fm.path, name = 'campaign')

        self._make_directory_structure()

        runpyPath = os.path.join(self.fm.path, 'run.py')
        if mpi.rank == 0:
            if not os.path.isfile(runpyPath):
                shutil.copyfile(
                    os.path.join(planetengineDir, 'linux', 'run.py'),
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

    def _pre_update(self):
        pass
    def _post_update(self):
        pass

    def update(self):
        self._pre_update()
        self.fm.update()
        self.jobs_available = {
            key[:-5] for key in self.fm.directories['jobs']['available'] \
                if key[:6] == 'pejob_'
            }
        self.jobs_running = {
            key[:-5] for key in self.fm.directories['jobs'] \
                if key[:6] == 'pejob_'
            }
        self.jobs_completed = {
            key[:-5] for key in self.fm.directories['jobs']['completed'] \
                if key[:6] == 'pejob_'
            }
        self.jobs_failed = {
            key[:-5] for key in self.fm.directories['jobs']['failed'] \
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

    def _pre_run(self, job):
        jobID = get_jobID(job)
        self.fm.move(
            os.path.join(
                self.fm.directories['jobs']['available']['.'],
                jobID + '.json'
                ),
            os.path.join(
                self.fm.directories['jobs']['.'],
                jobID + '.json'
                )
            )

    def run(self, job):
        self._pre_run(job)
        job, out, completed = self._run(job)
        self._post_run(job, out, completed)

    def _post_run(self, job, out, completed):
        jobID = get_jobID(job)
        jobFilename = jobID + '.json'
        self.fm.move(
            os.path.join(
                'jobs',
                jobFilename
                ),
            os.path.join(
                'jobs',
                {True: 'completed', False: 'failed'}[completed],
                jobFilename
                )
            )
        for outName in out:
            self.fm.move(
                os.path.join(
                    'out',
                    outName
                    ),
                os.path.join(
                    'out',
                    {True: 'completed', False: 'failed'}[completed],
                    outName
                    )
                )
        stderrFile = jobID + '.error'
        stdoutFile = jobID + '.out'
        self.fm.move(
            os.path.join(
                'logs',
                stderrFile
                ),
            os.path.join(
                'logs',
                {True: 'completed', False: 'failed'}[completed],
                stderrFile
                )
            )
        self.fm.move(
            os.path.join(
                'logs',
                stdoutFile
                ),
            os.path.join(
                'logs',
                {True: 'completed', False: 'failed'}[completed],
                stdoutFile
                )
            )

    def subrun(self, jobID = None, cores = 1):
        if jobID is None:
            jobID = random.choice(tuple(self.jobs_available))
        stderrFilepath = os.path.join(self.fm.path, 'logs', jobID + '.error')
        stdoutFilepath = os.path.join(self.fm.path, 'logs', jobID + '.out')
        with open(stdoutFilepath, 'w') as outfile:
            with open(stderrFilepath, 'w') as errorfile:
                ignoreme = subprocess.Popen(
                    ['mpirun', '-np', str(cores), 'python', self.runpy, jobID],
                    stdout = outfile,
                    stderr = errorfile
                    )

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
        jobID = get_jobID(job)
        if not jobID in self.jobs:
            self.jobs_available.add(jobID)
            self.fm.save_json(
                job,
                jobID,
                self.fm.directories['jobs']['available']['.']
                )
        self.update()

    def add_jobs(self, joblist):
        for job in joblist:
            self.add_job(job)
