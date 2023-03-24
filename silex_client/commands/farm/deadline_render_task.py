
from silex_client.action.command_base import CommandBase


class DeadlineRenderTaskCommand(CommandBase):

    def get_batch_name(self, context):
        project = context.get('project').lower()
        sequence = context.get('sequence').lower()
        shot = context.get('shot').lower()
        task_type = context.get('task_type').lower()
        task = context.get('task').lower().replace('-', '_')

        return f"{project}_{sequence}_{shot}_{task_type}_{task}"

    def get_job_title(self, output_path):
        path_split = output_path.split("/")
        job_title = path_split[-2]

        return job_title

