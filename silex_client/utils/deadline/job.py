"""
https://docs.thinkboxsoftware.com/products/deadline/10.1/1_User%20Manual/manual/manual-submission.html

"""
import os
from typing import Optional, List, Any, Dict
from pprint import pformat

from fileseq import FrameSet
from pathlib import Path
from silex_client.utils.log import logger

import logging
log = logging.getLogger('deadline')
from silex_client.utils.log import flog


class DeadlineJob:
    """
    Job with default params
    """

    JOB_INFO = {
        "Group": "",
        "MachineName": os.environ['COMPUTERNAME'],
        'MachineLimit': 0,
        'Pool': "",
        "ChunkSize": 5,
        "Priority": 50,
        # "InitialStatus": "Active"  # < Active / Suspended >
    }

    PLUGIN_INFO = {}

    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 rez_requires: Optional[str] = None,
                 batch_name: Optional[str] = None,
                 depends_on_previous: bool = False):

        self.job_info: Dict[str, Any] = self.JOB_INFO
        self.plugin_info: Dict[str, Any] = self.PLUGIN_INFO

        self.batch_name = batch_name  # used ?
        self.depends_on_previous = depends_on_previous

        self.job_info.update({
            "Name": job_title,
            "UserName": user_name,
            "Frames": frame_range.frange
        })
        self.plugin_info.update({
            "RezRequires": rez_requires
        })
        if batch_name:
            self.job_info.update({
                "BatchName": batch_name
            })

    def set_group(self, group):
        self.job_info.update({'Group': group})

    def set_pool(self, pool):
        self.job_info.update({'Pool': pool})

    def set_chunk_size(self, chunk_size):
        self.job_info.update({'ChunkSize': chunk_size})

    def set_priority(self, value):
        self.job_info.update({"Priority": value})

    def set_dependency(self, job_id):
        self.job_info.update({'JobDependencies': job_id})

    def __str__(self):
        return f"[job.{self.__class__.__name__}]\nINFO: {pformat(self.job_info)}\nPLUGIN: {pformat(self.plugin_info)}"


class CommandLineJob(DeadlineJob):

    # This used only in the non rez version.
    EXECUTABLE = "C:\\rez\\__install__\\Scripts\\rez\\rez.exe"

    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 command: str,
                 rez_requires: Optional[str] = None,
                 batch_name: Optional[str] = None,
                 depends_on_previous: bool = False):

        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)

        self.job_info.update({
            "Plugin": "RezCommandLine"
        })

        self.plugin_info.update({
            "Executable": self.EXECUTABLE,
            "Arguments": command
        })


class VrayJob(DeadlineJob):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 file_path: str,
                 output_path: str,
                 resolution: Optional[List[int]] = None,
                 rez_requires: Optional[str] = None,
                 batch_name: Optional[str] = None,
                 depends_on_previous: bool = False):

        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "Plugin": "RezVray"
        })

        self.plugin_info.update({
            "InputFilename": file_path,
            "OutputFilename": output_path,
        })

        if resolution is not None:
            self.plugin_info.update({
                "Width": resolution[0],
                "Height": resolution[1]
            })


class ArnoldJob(DeadlineJob):

    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 file_path: str,
                 output_path: str,
                 rez_requires: Optional[str] = None,
                 batch_name: Optional[str] = None,
                 depends_on_previous: bool = False):

        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "OutputFilename0": str(Path(output_path).name),
            "Plugin": "RezArnold"
        })

        self.plugin_info.update({
            "InputFile": file_path,
            "OutputFile": output_path
        })


class HuskJob(DeadlineJob):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 file_path: str,
                 output_path: str,
                 log_level: str,
                 rez_requires: Optional[str] = None,
                 batch_name: Optional[str] = None,
                 depends_on_previous: bool = False):

        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "Plugin": "RezHusk"
        })

        self.plugin_info.update({
            "SceneFile": file_path,
            "ImageOutputDirectory": output_path,
            "LogLevel": log_level,
            # "HuskRenderExecutable": "C:/Houdini19/bin/husk.exe"
        })


class HoudiniJob(DeadlineJob):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 file_path: str,
                 output_path: str,
                 rop_node: str,
                 resolution=None,
                 sim_job=False,
                 rez_requires: Optional[str] = None,
                 batch_name: Optional[str] = None,
                 depends_on_previous: bool = False):

        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "Plugin": "RezHoudini"
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


class MayaBatchJob(DeadlineJob):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 file_path: str,
                 output_path: str,
                 renderer: str,
                 rez_requires: Optional[str] = None,
                 batch_name: Optional[str] = None,
                 depends_on_previous: bool = False):

        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "Plugin": "RezMayaBatch"
        })

        self.plugin_info.update({
            "SceneFile": file_path,
            "OutputFilePrefix": str(Path(output_path).stem),
            "OutputFilePath": str(Path(output_path).parent),
            "Renderer": renderer,
            "RezRequires": rez_requires,
            "Version": 2022
        })


class NukeJob(DeadlineJob):
    def __init__(self,
                 job_title: str,
                 user_name: str,
                 frame_range: FrameSet,
                 file_path: str,
                 output_path: str,
                 write_node: str,
                 use_gpu: bool,
                 nuke_x: bool,
                 rez_requires: Optional[str] = None,
                 batch_name: Optional[str] = None,
                 depends_on_previous: bool = False):

        super().__init__(job_title, user_name, frame_range, rez_requires, batch_name, depends_on_previous)

        self.job_info.update({
            "OutputDirectory0": str(Path(output_path).parent),
            "Plugin": "Nuke"
        })

        self.plugin_info.update({
            "SceneFile": file_path,
            "OutputFilePath": output_path,
            "WriteNode": write_node,
            "UseGPU": use_gpu,
            "NukeX": nuke_x,
            "Version":"13.2"
        })

