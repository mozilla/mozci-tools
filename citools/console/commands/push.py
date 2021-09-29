from cleo import Command

from citools.dump_failures import dump_failures


class PushFailuresCommand(Command):
    """
    Display failing tests for a given push.

    failures
    """

    def handle(self):
        dump_failures(
            self.argument("branch"),
            self.argument("rev"),
        )


class PushCommands(Command):
    """
    Contains commands that operate on a single push.

    push
        {branch : Branch the push belongs to (e.g autoland, try, etc).}
        {rev : Head revision of the push.}
    """

    commands = [PushFailuresCommand()]

    def handle(self):
        return self.call("help", self._config.name)
