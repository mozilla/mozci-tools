from cleo.commands.command import Command
from cleo.helpers import argument, option

from citools.dump_failures import dump_failures


class PushCommand(Command):
    arguments = [
        argument(
            "branch",
            description="Push branch."
        ),
        argument(
            "rev",
            description="Push revision."
        ),
    ]


class PushFailuresCommand(PushCommand):
    name = "push failures"
    description = "Display failing tests for a given push."

    def handle(self):
        dump_failures(
            self.argument("branch"),
            self.argument("rev"),
        )
