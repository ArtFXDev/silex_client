from typing import List, Optional, cast

from fileseq import FrameSet
from silex_client.utils import command_builder


class Command:
    """
    A Command is a list of arguments
    """

    def __init__(self, argv: List[str] = [], tags: List[str] = []):
        self.argv = argv
        self.tags = tags

    def __repr__(self) -> str:
        return " ".join(self.argv)


class Task:
    """
    A Task is a set of commands
    A Task can contain other tasks as dependencies
    """

    def __init__(self, title: str = "", argv: Optional[List[str]] = None):
        if len(title) and title[0] == "-":
            self.title = f"({title})"
        else:
            self.title = title

        self.precommands: List[Command] = []
        self._commands: List[Command] = []
        self.children: List[Task] = []

        if argv:
            self._commands.append(Command(argv))

    @property
    def commands(self):
        return self.precommands + self._commands

    def addPreCommand(self, cmd: Command):
        self.precommands.append(cmd)

    def addCommand(self, cmd: Command):
        self._commands.append(cmd)

    def addChild(self, child: "Task"):
        self.children.append(child)

    def __repr__(self) -> str:
        result = f"{self.title}"

        if len(self.children) > 0:
            children = ", ".join([str(c) for c in self.children])
            result += f" <- [{children}]"

        return result


def get_mount_command(nas: str) -> Command:
    """
    Constructs the mount command in order to access files on the render farm
    """
    mount_cmd = command_builder.CommandBuilder(
        "mount_rd_drive",
        delimiter=None,
        dashes="",
        rez_packages=["mount_render_drive"],
    )

    mount_cmd.value(nas)
    return Command(argv=mount_cmd.as_argv())


def wrap_command(
    pres: List[Command], cmd: Command, post: Optional[Command] = None
) -> Command:
    """
    Wraps a command with cmd-wrapper
    Combines a pre, cmd and post command into a single one
    """
    wrap_cmd = command_builder.CommandBuilder(
        "cmd-wrapper", dashes="--", rez_packages=["cmd_wrapper"]
    )

    for pre in pres:
        wrap_cmd.param("pre", f'"{str(pre)}"')

    wrap_cmd.param("cmd", f'"{str(cmd)}"').param(
        "post", f'"{str(post)}"', condition=post is not None
    )

    return Command(argv=wrap_cmd.as_argv())


def wrap_with_mount(
    cmd: command_builder.CommandBuilder, nas: str, post: Optional[Command] = None
):
    """
    Wrap command with a pre-command mounting the network drive
    """
    return wrap_command(
        pres=[get_mount_command(nas)], cmd=Command(cmd.as_argv()), post=post
    )


def frameset_to_frames_str(frameset: FrameSet, sep: str = ";") -> str:
    frames_list = cast(List[str], list(frameset))
    return sep.join(map(str, frames_list))
