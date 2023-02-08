import os
import getpass
from fileseq import FrameSet
from silex_client.utils.log import logger as log

DEFAULT_GROUP = 'angele'
DEFAULT_POOL = ''
DEFAULT_CHUNKSIZE = 5

import logging

log = logging.getLogger('deadline')


class DeadlineJobTemplate:
    """
    Job with default params
    """

    JOB_INFO = {
        # "Name": self.get_jobname(),
        "Group": DEFAULT_GROUP,
        "Priority": '50',
        "UserName": getpass.getuser().lower(),  # already checked by submitter
        # "Plugin": "RezHoudini",
        # "LimitGroups": DEFAULT_LIMIT_GROUP,
        "MachineName": os.environ['COMPUTERNAME'],
        # "ConcurrentTasks": self.submit_node.evalParm("concurrentTasks"),
        'MachineLimit': 0,
        'Pool': DEFAULT_POOL,
        # 'OutputDirectory0': self.get_output_dir(),
        # 'InitialStatus': 'Suspended'
        # "Frames": frames,
        "ChunkSize": DEFAULT_CHUNKSIZE,
    }

    PLUGIN_INFO = {
        # "RezRequires": os.environ["REZ_USED_REQUEST"],
    }

    def __init__(self):
        self.job_type = 'job'

    def get_job_name(self):
        pass
        # # to be implemented
        # name = "{}_{}".format(name, self.job_type)
        # return name

    def get_output_dir(self):
        pass


class DeadlineCommandLineJob(DeadlineJobTemplate):

    EXECUTABLE = "C:\\rez\\__install__\\Scripts\\rez\\rez.exe"
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 command: str,
                 frame_range: FrameSet,
                 group=DEFAULT_GROUP,
                 pool=DEFAULT_POOL,
                 chunk_size=DEFAULT_CHUNKSIZE,
                 batch_name=None):

        self.job_info = self.JOB_INFO
        self.plugin_info = self.PLUGIN_INFO
        self.batch_name = batch_name
        self.group = group
        self.pool = pool

        self.job_info.update({
            "Name": job_title,
            "UserName": user_name,
            "Frames": frame_range.frange,
            "ChunkSize": chunk_size,
            "Group": self.group,
            "Pool": self.pool,
            "Plugin": "CommandLine"
        })

        self.plugin_info.update({
            "Executable": self.EXECUTABLE,
            "Arguments": command
        })

        if batch_name is not None:
            self.job_info.update({
                "BatchName": self.batch_name
            })


class DeadlineMayaBatchJob(DeadlineJobTemplate):
    # auto filled :
    #   - department (task)
    #   - pool : mapped by Sid
    #   - group render | user

    job_type = 'render'
    plugin = 'RezMayaBatch'

    def __init__(self, path, frame_range, render_path=None, chunk_size=DEFAULT_CHUNKSIZE, priority=50,
                 comment=None, renderer=None):
        # path to be implemented

        self.job_info = self.JOB_INFO
        self.plugin_info = self.PLUGIN_INFO

        # step_value = 'step{}'.format(step) if step > 1 else ''
        # frames = '{}-{}'.format(start, end) + step_value

        self.job_info.update({
            "Name": self.get_job_name(),  # TODO: add pass ?
            "Frames": frame_range,
            "department": "to be implemented",
            "Priority": str(priority),
            "Plugin": self.plugin,
            'OutputDirectory0': render_path,
            'ChunkSize': chunk_size
        })

        self.plugin_info.update({
            "Version": os.environ["REZ_MAYA_MAJOR_VERSION"],  # needed in "RezMayaBatch.py" in StartJob()
            "SceneFile": self.sid.path,
            "Renderer": renderer,
        })
