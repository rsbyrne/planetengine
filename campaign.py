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
from . import paths
message = utilities.message

import time
import random
def random_sleep():
    time.sleep(random.random())

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
        ('failed', ()),
        ('threads', ())
        )),
    )

def get_jobID(job):
    jobString = utilities.stringify(job)
    jobID = JOBPREFIX + wordhash.get_random_phrase(jobString)
    return jobID

def get_threadID():
    threadID = 'thread_' + wordhash.get_random_phrase()
    return threadID

def load(name, path):
    campaignDir = os.path.join(path, name)
    return _built.load_built('campaign', campaignDir)

class Campaign(_built.Built):

    name = 'campaign'
    path = paths.defaultPath

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
            if os.path.basename(self.script) == 'campaign_0.py':
                name = os.path.basename(os.path.dirname(script))
            else:
                name = os.path.splitext(os.path.basename(self.script))[0]
        self.name = name
        if path is None:
            path = os.path.abspath(
                os.path.dirname(
                    os.path.dirname(
                        script
                        )
                    )
                )
        self.path = path

        del inputs['name']
        del inputs['path']
        del inputs['suite']

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = script
            )

        ignore_strs = [
            'pemod_',
            'planetengine',
            ]
        self.fm = disk.FileManager(name, path, ignore_strs = ignore_strs)

        if not 'campaign_0.py' in self.fm.directories:
            self.save(path = self.fm.path, name = 'campaign')

        self._make_directory_structure()

        self.runpy = self._make_copy_of_planetengine_file('run.py', 'linux')
        self.runsh = self._make_copy_of_planetengine_file('run.sh', 'linux')

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

    def _make_copy_of_planetengine_file(self, fileName, pepath = 'linux'):
        filePath = os.path.join(self.fm.path, fileName)
        if mpi.rank == 0:
            if not os.path.isfile(filePath):
                shutil.copyfile(
                    os.path.join(planetengineDir, pepath, fileName),
                    filePath
                    )
        self.fm.liberate_path(fileName)
        return filePath

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
        stdoutFilepath = os.path.join(self.fm.path, 'logs', jobID + '.out')
        stderrFilepath = os.path.join(self.fm.path, 'logs', jobID + '.error')
        if wait:
            message("Running " + jobID + "...")
        if mpi.rank == 0:
            with open(stdoutFilepath, 'w') as outfile:
                with open(stderrFilepath, 'w') as errorfile:
                    process = subprocess.Popen(
                        ['mpirun', '-np', str(cores), 'python', self.runpy, 'single', jobID],
                        stdout = outfile,
                        stderr = errorfile
                        )
                    if wait:
                        process.wait()
        mpi.comm.barrier()
        if wait:
            message("Completed " + jobID)

    def autorun(self, cores = 1):
        message("Autorun engaged on " + str(cores) + " cores...")
        while True:
            self.update()
            if len(self.jobs_available) > 0:
                try: self.subrun(cores = cores, wait = True)
                except: random_sleep()
            else:
                break
        message("Jobs exhausted: autorun complete.")

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

    # def _post_load_hook(self, name, path):
    #
