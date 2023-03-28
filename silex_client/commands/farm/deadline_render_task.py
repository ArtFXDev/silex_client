
from silex_client.action.command_base import CommandBase


class DeadlineRenderTaskCommand(CommandBase):

    def get_batch_name(self, context):
        project = context.get('project').lower()
        sequence = context.get('sequence').lower()
        shot = context.get('shot').lower()
        task_type = context.get('task_type').lower()
        task = context.get('task').lower().replace('-', '_')

        return f"{project}_{sequence}_{shot}_{task_type}_{task}"

