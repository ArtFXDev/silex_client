
from silex_client.action.command_base import CommandBase


class DeadlineRenderTaskCommand(CommandBase):


    def define_job_names(self, output_path):

        # get job_title and batch_name
        path_split = output_path.split("/")
        batch_name = "_".join(path_split[1:6])
        job_title = path_split[-2]
        return {"job_title": job_title, "batch_name": batch_name}
