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
message = utilities.message

JOBPREFIX = 'pejob_'

_campaignStructure = (
    ('jobs', (
        ('completed', ()),
        ('failed', ()),
        ('available', ())
        )),
    ('out', ()),
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

        if not _pre_update is None:
            self._pre_update = _pre_update
        if not _post_update is None:
            self._post_update = _post_update

        self._run = _run

        self.update()

    def _pre_update(self):
        pass
    def _post_update(self):
        pass

    def update(self):
        self._pre_update()
        self.fm.update()
        self.jobs_running = {
            key[:-5] for key in self.fm.directories['jobs'] \
                if key[:6] == 'pejob_'
            }
        self.jobs_available = {
            key[:-5] for key in self.fm.directories['jobs']['available'] \
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

    def _pre_run(self, jobID):
        self.update()
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
        self.update()

    def _post_run(self, jobID, completed):
        self.update()
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
        stderrFile = jobID + '.error'
        stdoutFile = jobID + '.out'
        stderrFilepath = os.path.abspath(os.path.join(self.fm.path, 'logs', stderrFile))
        stdoutFilepath = os.path.abspath(os.path.join(self.fm.path, 'logs', stdoutFile))
        if mpi.rank == 0:
            subprocess.call(
                ['sh', os.path.join(planetengineDir, 'linux', 'cliplogs.sh'), stderrFilepath]
                )
            subprocess.call(
                ['sh', os.path.join(planetengineDir, 'linux', 'cliplogs.sh'), stdoutFilepath]
                )
        mpi.comm.barrier()
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
        self.update()

    def choose_job(self):
        self.update()
        random.seed()
        jobID = random.choice(tuple(self.jobs_available))
        return jobID

    def _master_run(self, jobID = None):
        if jobID is None:
            jobID = self.choose_job()
        self._pre_run(jobID)
        job = self.fm.load_json(
            jobID,
            'jobs'
            )
        completed = self._run(**job)
        self._post_run(jobID, completed)

    def subrun(self, jobID = None, cores = 1, wait = False):
        if jobID is None:
            jobID = self.choose_job()
        stderrFilepath = os.path.join(self.fm.path, 'logs', jobID + '.error')
        stdoutFilepath = os.path.join(self.fm.path, 'logs', jobID + '.out')
        with open(stdoutFilepath, 'w') as outfile:
            with open(stderrFilepath, 'w') as errorfile:
                process = subprocess.Popen(
                    ['mpirun', '-np', str(cores), 'python', self.runpy, 'single', jobID],
                    stdout = outfile,
                    stderr = errorfile
                    )
                if wait:
                    message("Running " + jobID + "...")
                    process.wait()
                    message("Completed " + jobID)

    def autorun(self, cores = 1):
        message("Autorun engaged on " + str(cores) + " cores...")
        while True:
            self.update()
            if len(self.jobs_available) > 0:
                self.subrun(cores = cores, wait = True)
            else:
                break
        message("Jobs exhausted: autorun complete.")

    def multirun(self, threads = 1, cores = 1):
        message("Running in multirun mode...")
        for i in range(threads):
            message("Launching thread #" + str(i) + '...')
            process = subprocess.Popen(
                ['python', self.runpy, 'auto', str(cores)],
                )
            message("Launched thread #" + str(i) + '.')
        message("All threads commissioned.")

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
