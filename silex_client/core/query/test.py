
from silex_client.graph.action import Action
from silex_client.graph.command import Command
from silex_client.graph.step import Step
from silex_client.graph.socket import Socket
from silex_client.utils.enums import Execution
from command_query import CommandQuery
from typing import Iterator


# COMMAND 1 #
socket_1 = Socket(name='param_1', value=1)
command_1 = Command(name="command_1", index=0, inputs={'param_1':socket_1})
step_1 = Step(name='step_1', index=0, children={'command_1':command_1})

command_1.parent = step_1

# COMMAND 2 #
socket_2 = Socket(name='param_2', value=2)
command_2 = Command(name="command_2", index=1, inputs={'param_2':socket_2})
step_2 = Step(name='step_2', index=1, children={'command_2':command_2})


# GENERAL STEP
STEP = Step(name='main_step', index=0, children={'step_1':step_1, 'step_2':step_2})

# ACTION
action = Action(name='Action', children={'main_step':STEP})
step_1.parent = action

query = CommandQuery(command_1)



####################
# test fonctions

def commands():
    """Shortcut to get the commands"""
    return get_all_commands(action)

# def iter_commands(action):
#     """
#     Iterate over all the commands in order
#     """
#     return CommandIterator(action)

def get_commands_from_step(step: Step, command_list= []) :
    """
    Gather all the commands in a step

    returns: Dict(command_index : command_object)
    """

    step_children = step.children
    commands = command_list
    if len(step_children) < 1:
        print(
        f"The step : {step.name}, has no children",
        )
        return None

    for child in step_children.values():
        if isinstance(child, Command):
            commands.append(child)


        if isinstance(child, Step):
            get_commands_from_step(child, commands)
    
    return commands

def get_all_commands(action: Action):
    
    action_children = action.children
    commands = list()

    if len(action_children) < 1:
        print(
        f"The action : {action.name}, has no children (No steps found)",
        )

        return None

    for step in action_children.values():
        command = get_commands_from_step(step)
        if command is not None:
            commands.extend(command)
    
    return commands


# class CommandIterator(Iterator):
#     """
#     Iterator for the commands of an action
#     """

#     def __init__(self, action: Action):
#         self.action = action
#         self.command_index = -1

#     def __iter__(self) :
#         return self

#     def __next__(self) -> Command:
#         print('NEXT')
#         commands = get_all_commands(action)

#         if commands is None:
#             raise StopIteration

#         index_to_command = dict(zip([cmd.index for cmd in commands], commands))
#         new_index = self.command_index
        
#         if self.action.execution_type == Execution.PAUSE:
#             raise StopIteration
#         # Increment the index according to the callback
#         if self.action.execution_type == Execution.FORWARD:
#             new_index += 1
#         if self.action.execution_type == Execution.BACKWARD:
#             new_index -= 1

#         # Test if the command is out of bound and raise StopIteration if so
#         if new_index < 0:
#             raise StopIteration

#         try:
#             command = index_to_command[new_index]
#             self.command_index = new_index
#             return command
#         except KeyError:
#             raise StopIteration



# ###################
# a = commands()
# if a is not None:
#     for cm in a:
#         # print(cm)
#         print(cm.name)
#     cmd = [cm.name for cm in a]
#     print(f'List of commands in the action : \n {cmd}')

# for iter in iter_commands(action):
#     print(f'iterations : {iter}')


# query.set_parameter('param_1', 5)
# print(query.command.inputs)

class A:
    def __init__(self):
        self.commands = commands()

    @property
    def parameters(self):
        """
        Helper to get a list of all the parameters of the action,
        usually used for printing infos about the action

        The format of the output is {<step>:<command> : parameters}
        """
        parameters = {}

        if self.commands is None:
            return None

        for command in self.commands:
            print(command.name)
            # Get parents (i call it parenting chaine)
            parents= [command.name]
            parent = self.get_parent(command)
            print (parent)

            if parent is not None:
                parents.append(parent.name)

                while parent is not None:
                    parent = self. get_parent(parent)
                    if parent is not None:
                        parents.insert(0, parent.name)
            
            print(parents)
            
            # Store parameters (inputs) and return it
            parameters[':'.join(parents)] = command.inputs

        return parameters
    
    def get_parent(self, item):
        return item.parent


a = A()
print(a.parameters)




