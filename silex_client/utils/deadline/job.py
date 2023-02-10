import os
import getpass
from fileseq import FrameSet
from silex_client.utils.log import logger as log

DEFAULT_GROUP = ''
DEFAULT_POOL = ''
DEFAULT_CHUNKSIZE = 5

import logging

log = logging.getLogger('deadline')
from silex_client.utils.log import flog


class DeadlineJobTemplate:
    """
    Job with default params
    """

    JOB_INFO = {
        # "Name": self.get_jobname(),
        "Group": DEFAULT_GROUP,
        #"Priority": '50',
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


    def set_group(self, group):
        self.job_info.update({'Group': group})

    def set_pool(self, pool):
        self.job_info.update({'Pool': pool})

    def set_chunksize(self, chunksize):
        self.job_info.update({'ChunkSize': chunksize})


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

        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

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

class DeadlineVrayJob(DeadlineJobTemplate):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 scenefile_name: str,
                 outputfile_name: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 group=DEFAULT_GROUP,
                 pool=DEFAULT_POOL,
                 chunk_size=DEFAULT_CHUNKSIZE,
                 batch_name=None):

        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

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
            # "RezRequires": rez_requires,
            "Plugin": "Vray"
        })

        self.plugin_info.update({
            "InputFilename": scenefile_name,
            "OutputFilename": outputfile_name,
        })

        if batch_name is not None:
            self.job_info.update({
                "BatchName": self.batch_name
            })

class DeadlineArnoldJob(DeadlineJobTemplate):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 scenefile_name: str,
                 outputfile_name: str,
                 version: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 group=DEFAULT_GROUP,
                 pool=DEFAULT_POOL,
                 chunk_size=DEFAULT_CHUNKSIZE,
                 batch_name=None):

        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

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
            # "RezRequires": rez_requires,
            "Plugin": "Arnold"
        })

        self.plugin_info.update({
            "InputFile": scenefile_name,
            "OutputFile": outputfile_name,
            "Version": version
        })

        if batch_name is not None:
            self.job_info.update({
                "BatchName": self.batch_name
            })

class DeadlineHuskJob(DeadlineJobTemplate):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 scenefile_path: str,
                 outputfile_path: str,
                 log_level: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 group=DEFAULT_GROUP,
                 pool=DEFAULT_POOL,
                 batch_name=None):

        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

        self.batch_name = batch_name
        self.group = group
        self.pool = pool

        self.job_info.update({
            "Name": job_title,
            "UserName": user_name,
            "Frames": frame_range.frange,
            "Group": self.group,
            "Pool": self.pool,
            # "RezRequires": outputfile_path,
            "Plugin": "Husk_Dev"
        })

        self.plugin_info.update({
            "SceneFile": scenefile_path,
            "ImageOutputDirectory": outputfile_path,
            "LogLevel": log_level,
            "HuskRenderExecutable": "C:/Houdini19/bin/husk.exe"
        })

        if batch_name is not None:
            self.job_info.update({
                "BatchName": self.batch_name
            })

        flog.info(self.job_info)
        flog.info(self.plugin_info)

class DeadlineHoudiniJob(DeadlineJobTemplate):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 scenefile_path: str,
                 outputfile_path: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 rop_node: str,
                 resolution=None,
                 sim_job=False,
                 group=DEFAULT_GROUP,
                 pool=DEFAULT_POOL,
                 batch_name=None,
                 priority_rank=100):

        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

        self.batch_name = batch_name
        self.group = group
        self.pool = pool

        self.job_info.update({
            "Name": job_title,
            "UserName": user_name,
            "Frames": frame_range.frange,
            "Group": self.group,
            "Pool": self.pool,
            #"RezRequires": rez_requires,
            "Plugin": "Houdini",
            "Priority": priority_rank
        })

        self.plugin_info.update({
            "SceneFile": scenefile_path,
            "Output": outputfile_path,
            "OutputDriver": rop_node,
            "SimJob": sim_job
        })

        if batch_name is not None:
            self.job_info.update({
                "BatchName": self.batch_name
            })


        if resolution is not None:
            self.plugin_info.update({
               "Width": resolution[0]
            })
            self.plugin_info.update({
                "Height": resolution[1]
            })

        flog.info(self.job_info)
        flog.info(self.plugin_info)

class DeadlineMayaBatchJob(DeadlineJobTemplate):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 scenefile_name: str,
                 project_path: str,
                 outputfile_name: str,
                 renderer : str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 group=DEFAULT_GROUP,
                 pool=DEFAULT_POOL,
                 chunk_size=DEFAULT_CHUNKSIZE,
                 batch_name=None):

        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

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
            # "RezRequires": rez_requires,
            "Plugin": "MayaBatch"
        })

        self.plugin_info.update({
            "SceneFile": scenefile_name,
            "ProjectPath": project_path,
            "OutputFilePath": outputfile_name,
            "Renderer": renderer
        })

        if batch_name is not None:
            self.job_info.update({
                "BatchName": self.batch_name
            })


# class DeadlineMayaBatchJob(DeadlineJobTemplate):
#     # auto filled :
#     #   - department (task)
#     #   - pool : mapped by Sid
#     #   - group render | user
#
#     job_type = 'render'
#     plugin = 'RezMayaBatch'
#
#     def __init__(self, path, frame_range, render_path=None, chunk_size=DEFAULT_CHUNKSIZE, priority=50,
#                  comment=None, renderer=None):
#         # path to be implemented
#
#         self.job_info = self.JOB_INFO
#         self.plugin_info = self.PLUGIN_INFO
#
#         # step_value = 'step{}'.format(step) if step > 1 else ''
#         # frames = '{}-{}'.format(start, end) + step_value
#
#         self.job_info.update({
#             "Name": self.get_job_name(),  # TODO: add pass ?
#             "Frames": frame_range,
#             "department": "to be implemented",
#             "Priority": str(priority),
#             "Plugin": self.plugin,
#             'OutputDirectory0': render_path,
#             'ChunkSize': chunk_size
#         })
#
#         self.plugin_info.update({
#             "Version": os.environ["REZ_MAYA_MAJOR_VERSION"],  # needed in "RezMayaBatch.py" in StartJob()
#             "SceneFile": self.sid.path,
#             "Renderer": renderer,
#         })
#
