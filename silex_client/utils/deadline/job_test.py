import fileseq
from silex_client.utils.deadline.job import DeadlineCommandLineJob
from silex_client.utils.deadline.runner import DeadlineRunner

"""
Notes:
- make a test for each plugin
- make a test for each machine
- make a test for each plugin for each machine
- rez_requires can be optional for most plugins
- allow string frame_range ?
"""

if __name__ == "__main__":
    # Submit to Deadline Runner
    dr = DeadlineRunner()

    full_cmd = "rez env houdini arnold testpipe -- hython -m hrender //tars.artfx.fr/testpipe/testpipe/shots/s01/p010/lighting_hou_arnold/publish/v000/hip/main/testpipe_s01_p010_lighting_hou_arnold_publish_v000_main.hipnc -e -v -S -w 480 -h 270 -f 1 2 -d /out/arnold1 -o //tars.artfx.fr/testpipe/testpipe/shots/s01/p010/lighting_hou_arnold/publish/v000/exr/render/arnold/testpipe_s01_p010_lighting_hou_arnold_publish_v000_render_arnold.$F4.exr"

    rez_requires = "houdini arnold testpipe"
    argument_cmd = "hython -m hrender //tars.artfx.fr/testpipe/testpipe/shots/s01/p010/lighting_hou_arnold/publish/v000/hip/main/testpipe_s01_p010_lighting_hou_arnold_publish_v000_main.hipnc -e -v -S -w 480 -h 270 -f 1 2 -d /out/arnold1 -o //tars.artfx.fr/testpipe/testpipe/shots/s01/p010/lighting_hou_arnold/publish/v000/exr/render/arnold/testpipe_s01_p010_lighting_hou_arnold_publish_v000_render_arnold.$F4.exr"

    frames = fileseq.FrameSet("1-5")

    job = DeadlineCommandLineJob(
        job_title="silex_test_job",
        user_name="michael.haussmann",
        frame_range=frames,
        command=full_cmd,
        rez_requires=rez_requires,
    )

    job.set_group("pipeline")
    # job.set_pool(parameters["pools"])
    job.set_chunk_size(5)
    job.set_priority(60)

    done = dr.run(job)
    print(f"Result: {done}")
