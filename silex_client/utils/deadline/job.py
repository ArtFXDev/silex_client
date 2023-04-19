"""
https://docs.thinkboxsoftware.com/products/deadline/10.1/1_User%20Manual/manual/manual-submission.html

"""
from typing import Optional, List, Any, Dict
from pprint import pformat

import socket
from math import floor
from fileseq import FrameSet
from pathlib import Path

import logging

log = logging.getLogger("deadline")


class DeadlineJob:
    """
    Job with default params
    """

    JOB_INFO = {
        "Group": "",
        "MachineName": socket.gethostname(),
        "MachineLimit": 0,
        "Pool": "",
        "ChunkSize": 5,
        "Priority": 50
    }

    PLUGIN_INFO = {}

    def __init__(
        self,
        job_title: str,
        user_name: str,
        frame_range: FrameSet,
        batch_name: Optional[str] = None,
        rez_requires: Optional[str] = None,
        depends_on_previous: bool = False,
        output_path: Optional[str] = None,
    ):
        self._id = None
        self._output_path = output_path
        self._frame_range = frame_range
        self.job_info: Dict[str, Any] = self.JOB_INFO.copy()
        self.plugin_info: Dict[str, Any] = self.PLUGIN_INFO.copy()

        self.depends_on_previous = depends_on_previous

        self.job_info.update(
            {"Name": job_title, "UserName": user_name, "Frames": frame_range.frange}
        )
        self.plugin_info.update({"RezRequires": rez_requires})
        if batch_name:
            self.job_info.update({"BatchName": batch_name})

    def set_group(self, group):
        self.job_info.update({"Group": group})

    def set_pool(self, pool):
        self.job_info.update({"Pool": pool})

    def set_chunk_size(self, chunk_size):
        self.job_info.update({"ChunkSize": chunk_size})

    def set_priority(self, value):
        self.job_info.update({"Priority": value})

    def set_dependency(self, job_id):
        self.job_info.update({"JobDependencies": job_id})

    def get_dependency(self):
        self.job_info.get("JobDependencies")

    def set_delay(self, minutes: int):
        """
        Convert number of minutes in format days:hours:minutes:seconds
        Update job_info to add delay.

        :param minutes: Number of minutes (int)
        """

        days = floor(minutes / 1440)
        leftover_minutes = minutes % 1440
        hours = floor(leftover_minutes / 60)
        minute = minutes - (days*1440) - (hours*60)
        self.job_info.update({
            "JobDelay": f"{days}:{hours}:{minute}:00",
            "ScheduledType": "Once"
        })

    def is_delay(self):
        """
        Returns if the job has delay.

        :return: True if delay, False if not
        """
        return 'JobDelay' in self.job_info

    @property
    def id(self):
        """
        Returns the job ID.

        :return: ID or None if the job was not submitted.
        """
        return self._id

    @id.setter
    def id(self, id):
        """
        ID should be set by DeadlineRunner on submission.

        :param id:
        :return:
        """
        self._id = id

    @property
    def output_path(self):
        """
        Returns the path, if set, else None
        :return:
        """
        return self._output_path

    @property
    def frame_range(self):
        """
        Returns the frame range (type FrameSet), if set, else None
        :return:
        """
        return self._frame_range

    @property
    def batch_name(self):
        return self.job_info.get("BatchName")

    def __str__(self):
        return f"[job.{self.__class__.__name__}] ID: {self.id}\nINFO: {pformat(self.job_info)}\nPLUGIN: {pformat(self.plugin_info)}"


class CommandLineJob(DeadlineJob):
    # This used only in the non rez version.
    EXECUTABLE = "C:\\rez\\__install__\\Scripts\\rez\\rez.exe"

    def __init__(
        self,
        job_title: str,
        user_name: str,
        frame_range: FrameSet,
        command: str,
        rez_requires: Optional[str] = None,
        batch_name: Optional[str] = None,
        output_path: Optional[str] = None,
        is_single_frame: Optional[bool] = False,
        depends_on_previous: bool = False,
    ):
        super().__init__(
            job_title=job_title,
            user_name=user_name,
            frame_range=frame_range,
            rez_requires=rez_requires,
            batch_name=batch_name,
            depends_on_previous=depends_on_previous,
            output_path=output_path,
        )

        self.job_info.update({"Plugin": "RezCommandLine"})
        if output_path:
            self.job_info.update(
                {"OutputDirectory0": str(Path(output_path).parent)}
            )

        self.plugin_info.update(
            {
                "Executable": self.EXECUTABLE,
                "Arguments": command,
                "SingleFramesOnly": is_single_frame
            }
        )


class VrayJob(DeadlineJob):
    def __init__(
        self,
        job_title: str,
        user_name: str,
        frame_range: FrameSet,
        file_path: str,
        output_path: str,
        is_files_per_frames: Optional[bool] = False,
        batch_name: Optional[str] = None,
        resolution: Optional[List[int]] = None,
        rez_requires: Optional[str] = None,
        depends_on_previous: bool = False,
    ):
        super().__init__(
            job_title=job_title,
            user_name=user_name,
            frame_range=frame_range,
            batch_name=batch_name,
            rez_requires=rez_requires,
            depends_on_previous=depends_on_previous,
        )

        self.job_info.update(
            {"OutputDirectory0": str(Path(output_path).parent), "Plugin": "RezVray"}
        )

        self.plugin_info.update(
            {
                "InputFilename": file_path,
                "OutputFilename": output_path,
                "SeparateFilesPerFrame": is_files_per_frames
            }
        )

        if resolution is not None:
            self.plugin_info.update({"Width": resolution[0], "Height": resolution[1]})

    @property
    def output_path(self):
        """
        Returns the path, if set, else None
        Re-implemented here because the path is stored in the plugin_info.

        :return:
        """
        return self.plugin_info.get("OutputFilename")


class ArnoldJob(DeadlineJob):
    def __init__(
        self,
        job_title: str,
        user_name: str,
        frame_range: FrameSet,
        file_path: str,
        output_path: str,
        batch_name: Optional[str] = None,
        rez_requires: Optional[str] = None,
        depends_on_previous: bool = False,
    ):
        super().__init__(
            job_title=job_title,
            user_name=user_name,
            frame_range=frame_range,
            batch_name=batch_name,
            rez_requires=rez_requires,
            depends_on_previous=depends_on_previous,
        )

        self.job_info.update(
            {
                "OutputDirectory0": str(Path(output_path).parent),
                "OutputFilename0": str(Path(output_path).name),
                "Plugin": "RezArnold",
            }
        )

        self.plugin_info.update({"InputFile": file_path, "OutputFile": output_path})

    @property
    def output_path(self):
        """
        Returns the path, if set, else None
        Re-implemented here because the path is stored in the plugin_info.

        :return:
        """
        return self.plugin_info.get("OutputFile")


class HuskJob(DeadlineJob):
    def __init__(
        self,
        job_title: str,
        user_name: str,
        frame_range: FrameSet,
        file_path: str,
        output_path: str,
        log_level: str,
        batch_name: Optional[str] = None,
        rez_requires: Optional[str] = None,
        depends_on_previous: bool = False,
    ):
        super().__init__(
            job_title=job_title,
            user_name=user_name,
            frame_range=frame_range,
            batch_name=batch_name,
            rez_requires=rez_requires,
            depends_on_previous=depends_on_previous,
        )

        self.job_info.update(
            {"OutputDirectory0": str(Path(output_path).parent), "Plugin": "RezHusk"}
        )

        self.plugin_info.update(
            {
                "SceneFile": file_path,
                "ImageOutputDirectory": output_path,
                "LogLevel": log_level
            }
        )

    @property
    def output_path(self):
        """
        Returns the path, if set, else None
        Re-implemented here because the path is stored in the plugin_info.

        :return:
        """
        return self.plugin_info.get("ImageOutputDirectory")


class HoudiniJob(DeadlineJob):
    def __init__(
        self,
        job_title: str,
        user_name: str,
        frame_range: FrameSet,
        file_path: str,
        output_path: str,
        rop_node: str,
        batch_name: Optional[str],
        resolution=None,
        sim_job=False,
        rez_requires: Optional[str] = None,
        depends_on_previous: bool = False,
    ):
        super().__init__(
            job_title=job_title,
            user_name=user_name,
            frame_range=frame_range,
            batch_name=batch_name,
            rez_requires=rez_requires,
            depends_on_previous=depends_on_previous
        )
        # self.job_info = dict(self.JOB_INFO)
        self.job_info.update(
            {"OutputDirectory0": str(Path(output_path).parent), "Plugin": "RezHoudini"}
        )

        self.plugin_info.update(
            {
                "SceneFile": file_path,
                "Output": output_path,
                "OutputDriver": rop_node,
                "SimJob": sim_job,
            }
        )

        if resolution is not None:
            self.plugin_info.update({"Width": resolution[0]})
            self.plugin_info.update({"Height": resolution[1]})

    @property
    def output_path(self):
        """
        Returns the path, if set, else None
        Re-implemented here because the path is stored in the plugin_info.

        :return:
        """
        return self.plugin_info.get("Output")


class MayaBatchJob(DeadlineJob):
    def __init__(
        self,
        job_title: str,
        user_name: str,
        frame_range: FrameSet,
        file_path: str,
        output_path: str,
        renderer: str,
        batch_name: Optional[str],
        rez_requires: Optional[str] = None,
        depends_on_previous: bool = False,
    ):
        super().__init__(
            job_title=job_title,
            user_name=user_name,
            frame_range=frame_range,
            batch_name=batch_name,
            rez_requires=rez_requires,
            depends_on_previous=depends_on_previous,
            output_path=output_path,
        )

        self.job_info.update(
            {
                "OutputDirectory0": str(Path(output_path).parent),
                "Plugin": "RezMayaBatch",
            }
        )

        prefix = str(Path(output_path).stem) + "_" + output_path.split("/")[-2]

        self.plugin_info.update(
            {
                "SceneFile": file_path,
                "OutputFilePrefix": prefix,
                "OutputFilePath": str(Path(output_path).parent),
                "Renderer": renderer,
                "RezRequires": rez_requires,
                "Version": 2022,
            }
        )


class NukeJob(DeadlineJob):
    def __init__(
        self,
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
        depends_on_previous: bool = False,
    ):
        super().__init__(
            job_title,
            user_name,
            frame_range,
            rez_requires,
            batch_name,
            depends_on_previous,
        )

        self.job_info.update(
            {"OutputDirectory0": str(Path(output_path).parent), "Plugin": "Nuke"}
        )

        self.plugin_info.update(
            {
                "SceneFile": file_path,
                "OutputFilePath": output_path,
                "WriteNode": write_node,
                "UseGPU": use_gpu,
                "NukeX": nuke_x,
                "Version": "13.2",
            }
        )

    @property
    def output_path(self):
        """
        Returns the path, if set, else None
        Re-implemented here because the path is stored in the plugin_info.

        :return:
        """
        return self.plugin_info.get("OutputFilePath")
