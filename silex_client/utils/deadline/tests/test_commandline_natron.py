"""
Test for the RezCommandLine Submitter

Passed on the base plugin on machine md8-2017-046, 15/2/2023
With a rezified command.

Passed on the rez plugin on machine md8-2017-046, 15/2/2023
(With the Houdini Vray command)



"""
from pathlib import Path
import getpass

import fileseq

from silex_client.utils.deadline.job import CommandLineJob
from silex_client.utils.deadline.runner import DeadlineRunner

# Houdini Arnold
full_cmd = r"env houdini arnold testpipe -- hython -m hrender \\tars\testpipe\testpipe\shots\s01\p010\lighting_hou_arnold\publish\v000\hip\main\testpipe_s01_p010_lighting_hou_arnold_publish_v000_main.hipnc -e -v -S -w 480 -h 270 -f 1 2 -d /out/arnold1 -o \\tars\testpipe\testpipe\shots\s01\p010\lighting_hou_arnold\publish\v000\exr\render\arnold\testpipe_s01_p010_lighting_hou_arnold_publish_v000_render_arnold.$F4.exr"
rez_requires = "houdini arnold testpipe"
argument_cmd = r"hython -m hrender \\tars\testpipe\testpipe\shots\s01\p010\lighting_hou_arnold\publish\v000\hip\main\testpipe_s01_p010_lighting_hou_arnold_publish_v000_main.hipnc -e -v -S -w 480 -h 270 -f 1 2 -d /out/arnold1 -o \\tars\testpipe\testpipe\shots\s01\p010\lighting_hou_arnold\publish\v000\exr\render\arnold\testpipe_s01_p010_lighting_hou_arnold_publish_v000_render_arnold.$F4.exr"

# Houdini vray
full_cmd = r"env houdini testpipe vray -- hython -m hrender \\tars\testpipe\testpipe\shots\s01\p010\lighting_hou_vray\publish\v000\hip\main\testpipe_s01_p010_lighting_hou_vray_publish_v000_main.hip -e -v -S -w 480 -h 270 -f 1 2 -d /out/vray -o \\tars\testpipe\testpipe\shots\s01\p010\lighting_hou_vray\publish\v000\exr\render\vray\testpipe_s01_p010_lighting_hou_vray_publish_v000_render_vray.$F4.exr"
rez_requires = "houdini vray testpipe"
argument_cmd = r"hython -m hrender \\tars\testpipe\testpipe\shots\s01\p010\lighting_hou_vray\publish\v000\hip\main\testpipe_s01_p010_lighting_hou_vray_publish_v000_main.hip -e -v -S -w 480 -h 270 -f 1 2 -d /out/vray -o \\tars\testpipe\testpipe\shots\s01\p010\lighting_hou_vray\publish\v000\exr\render\vray\testpipe_s01_p010_lighting_hou_vray_publish_v000_render_vray.$F4.exr"



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
argument_cmd = "overlay --username {username} {input} {output}"
# argument_cmd = "overlay {input} {output}"


if __name__ == "__main__":
    # Submit to Deadline Runner
    dr = DeadlineRunner()

    root = Path("M:/testpipe/shots/s01/p010/lighting_hou_vray/publish/v000/exr/render/temp_firemen_test")
    frame = "firemen_s01_p010_lighting_main_publish_v000_render.####.exr"
    movie_name = "firemen_s01_p010_lighting_main_publish_v000_render.mp4"

    argument_cmd = argument_cmd.format(username="test_user",
                                       input=root / frame,
                                       output=root / movie_name)

    job = CommandLineJob(
        job_title="silex_test_job_rez_commandline_natron",
        user_name=getpass.getuser().lower(),
        frame_range=fileseq.FrameSet("1"),
        command=argument_cmd,
        rez_requires=rez_requires,
        batch_name="silex_test_jobs",
        output_path=str(root / movie_name)
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
    job.plugin_info["SingleFramesOnly"] = True
    print(job)
    done = dr.run(job)["_id"]
    print(f"Result: {done}")
