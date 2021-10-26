from cleo import Command
from mozci.push import Push

from citools.dump_failures import dump_failures


class PushFailuresCommand(Command):
    """
    Display failing tests for a given push.

    failures
        {branch : Branch the push belongs to (e.g autoland, try, etc).}
    """

    def handle(self):
        dump_failures(
            self.argument("branch"),
            self.argument("rev"),
        )


class ClassifyCommand(Command):
    """
    Display the classification for a given push as GOOD, BAD or UNKNOWN.

    classify
        {branch=mozilla-central : Branch the push belongs to (e.g autoland, try, etc).}
    """

    def handle(self):
        push = Push(self.argument("rev"), self.argument("branch"))
        classification = push.classify()
        self.line(
            f'Push associated with the head revision {self.argument("rev")} on the branch '
            f'{self.argument("branch")} is classified as {classification.name}'
        )


class PushCommands(Command):
    """
    Contains commands that operate on a single push.

    push
        {rev : Head revision of the push.}
    """

    commands = [PushFailuresCommand(), ClassifyCommand()]

    def handle(self):
        return self.call("help", self._config.name)
