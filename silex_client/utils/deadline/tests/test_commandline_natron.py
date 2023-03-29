"""
Test for the RezCommandLine Submitter


"""
from pathlib import Path
import getpass

import fileseq

from silex_client.utils.deadline.job import CommandLineJob
from silex_client.utils.deadline.runner import DeadlineRunner

# https://github.com/ArtFXDev/silex_natron/tree/main/silex_natron

"""
--res "1920,1080"                     Output resolution. Default: 1920x1080.
  
  --username username                   Name of the artist/user to be overlayed.
  
  --filename untitled.ntp               Name of the project file.
  
  --project default_proj                Name of the film/project.
  
  --task compositing                    Name of the task.
  
  --seq s01                             Sequence number of the given input.
  
  --shot p010                           Shot number of the given input."""

rez_requires = "silex_natron"
argument_cmd = "overlay --username {username} --filename {filename} --project {project} --task {task} --seq {seq} --shot {shot} --res {res} {input} {output}"
# argument_cmd = "overlay {input} {output}"


if __name__ == "__main__":
    # Submit to Deadline Runner
    dr = DeadlineRunner()

    root = Path("M:/testpipe/shots/s01/p010/lighting_hou_vray/publish/v000/exr/render/temp_firemen_test")
    frame = "firemen_s01_p010_lighting_main_publish_v000_render.####.exr"
    movie_name = "firemen_s01_p010_lighting_main_publish_v000_render.mp4"

    data = {
        "username": "test_user",
        "filename": "TBD",
        "project": "testpipe",
        "task": "testing",
        "seq": "s99",
        "shot": "p099",
        "res": "1920,1080",  # TODO: find a solution...
        "input": root / frame,
        "output": root / movie_name
    }

    argument_cmd = argument_cmd.format(**data)

    job = CommandLineJob(
        job_title="silex_test_job_rez_commandline_natron",
        user_name=getpass.getuser().lower(),
        frame_range=fileseq.FrameSet("1"),
        command=argument_cmd,
        rez_requires=rez_requires,
        batch_name="silex_test_jobs",
        output_path=str(root / movie_name),
        is_single_frame=True
    )

    # optionals
    job.set_group("pipeline")
    # job.set_pool(parameters["pools"])
    # job.set_chunk_size(5)
    # job.set_priority(60)

    # extras
    # job.job_info["InitialStatus"] = "Suspended"
    # job.job_info["Allowlist"] = "md8-2017-046"

    # Uncomment to test the base plugin
    # job.job_info["Plugin"] = "CommandLine"
    # job.job_info["Name"] = "silex_test_job_commandline"
    # job.plugin_info["Arguments"] = full_cmd
    print(job)
    done = dr.run(job)["_id"]
    print(f"Result: {done}")
