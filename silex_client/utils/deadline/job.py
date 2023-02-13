import os
import getpass
from fileseq import FrameSet
from pathlib import Path
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
        "Group": DEFAULT_GROUP,
        "MachineName": os.environ['COMPUTERNAME'],
        'MachineLimit': 0,
        'Pool': DEFAULT_POOL,
        "ChunkSize": DEFAULT_CHUNKSIZE,
    }

    PLUGIN_INFO = {}

    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 batch_name=None,
                 depends_on_previous=False):
        self.job_info = self.JOB_INFO
        self.batch_name = batch_name
        self.depends_on_previous = depends_on_previous

        self.job_info.update({
            "Name": job_title,
            "UserName": user_name,
            "Frames": frame_range.frange
        })

        self.plugin_info = {
            "RezRequires": rez_requires
        }
        if batch_name is not None:
            self.job_info.update({
                "BatchName": self.batch_name
            })

    def set_group(self, group):
        self.job_info.update({'Group': group})

    def set_pool(self, pool):
        self.job_info.update({'Pool': pool})

    def set_chunk_size(self, chunk_size):
        self.job_info.update({'ChunkSize': chunk_size})

    def set_priority(self, value):
        flog.info(f"priority = {value}")
        self.job_info.update({"Priority": value})

    def set_dependency(self, job_id):
        self.job_info.update({'JobDependencies': job_id})


class DeadlineCommandLineJob(DeadlineJobTemplate):
    EXECUTABLE = "C:\\rez\\__install__\\Scripts\\rez\\rez.exe"

    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 command: str,
                 rez_requires: str,
                 batch_name=None,
                 depends_on_previous=False):
        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)
        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

        self.job_info.update({
            "Plugin": "CommandLine"
        })

        self.plugin_info.update({
            "Executable": self.EXECUTABLE,
            "Arguments": command
        })


class DeadlineVrayJob(DeadlineJobTemplate):
    def __init__(self, job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 file_path: str,
                 output_path: str,
                 batch_name=None,
                 depends_on_previous=False):
        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)

        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "Plugin": "Vray"
        })

        self.plugin_info.update({
            "InputFilename": file_path,
            "OutputFilename": output_path,
        })


class DeadlineArnoldJob(DeadlineJobTemplate):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 file_path: str,
                 output_path: str,

                 batch_name=None,
                 depends_on_previous=False):
        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)

        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "OutputFilename0": str(Path(output_path).name),
            "Plugin": "Arnold"
        })

        self.plugin_info.update({
            "InputFile": file_path,
            "OutputFile": output_path
        })


class DeadlineHuskJob(DeadlineJobTemplate):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 file_path: str,
                 output_path: str,
                 log_level: str,
                 batch_name=None,
                 depends_on_previous=False):
        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)
        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "Plugin": "Husk_Dev"
        })

        self.plugin_info.update({
            "SceneFile": file_path,
            "ImageOutputDirectory": output_path,
            "LogLevel": log_level,
            "HuskRenderExecutable": "C:/Houdini19/bin/husk.exe"
        })


class DeadlineHoudiniJob(DeadlineJobTemplate):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 file_path: str,
                 output_path: str,
                 rop_node: str,
                 resolution=None,
                 sim_job=False,
                 batch_name=None,
                 depends_on_previous=False):
        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)
        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "Plugin": "Houdini"
        })

        self.plugin_info.update({
            "SceneFile": file_path,
            "Output": output_path,
            "OutputDriver": rop_node,
            "SimJob": sim_job
        })

        if resolution is not None:
            self.plugin_info.update({
                "Width": resolution[0]
            })
            self.plugin_info.update({
                "Height": resolution[1]
            })


class DeadlineMayaBatchJob(DeadlineJobTemplate):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 file_path: str,
                 output_path: str,
                 renderer: str,
                 batch_name=None,
                 depends_on_previous=False):
        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)
        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "Plugin": "MayaBatch"
        })

        self.plugin_info.update({
            "SceneFile": file_path,
            "OutputFilePath": output_path,
            "Renderer": renderer,
            "RezRequires": rez_requires,
            "Version": 2022
        })


class DeadlineNukeJob(DeadlineJobTemplate):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 rez_requires: str,
                 file_path: str,
                 output_path: str,
                 project_path: str,
                 write_node: str,
                 use_gpu: bool,
                 batch_name=None,
                 depends_on_previous=False):
        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)
        self.job_info = dict(self.JOB_INFO)
        self.plugin_info = dict(self.PLUGIN_INFO)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "Plugin": "Nuke"
        })

        self.plugin_info.update({
            "SceneFile": file_path,
            "OutputFilePath": output_path,
            "WriteNode": write_node,
            "UseGPU": use_gpu
        })
