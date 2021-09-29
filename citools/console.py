import sys

from cleo import Application, Command

from citools import test_triage_bug_filer
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


class PushCommand(Command):
    """
    Contains commands that operate on a single push.

    push
        {branch : Branch the push belongs to (e.g autoland, try, etc).}
        {rev : Head revision of the push.}
    """

    commands = [PushFailuresCommand()]

    def handle(self):
        return self.call("help", self._config.name)


class FileBugsCommand(Command):
    """
    Files bugs for tests skipped due to new or migrating platforms.

    file-bugs
        {diff : Path to diff that skips tests}
        {--reason= : Reason tests are being skipped.}
        {--bug-id= : Bugzilla ID of the bug that will be landing the changes.}
        {--try-url= : URL to try push demonstrating failures.}
        {--dry-run : Don't submit bugs, instead print a string representation.}
    """

    help = test_triage_bug_filer.__doc__

    def handle(self):
        test_triage_bug_filer.process_diff(
            self.argument("diff"),
            self.option("reason"),
            self.option("bug-id"),
            try_url=self.option("try-url"),
            dry_run=self.option("dry-run"),
        )


def cli():
    application = Application()
    application.add(PushCommand())
    application.add(FileBugsCommand())
    application.run()


if __name__ == "__main__":
    sys.exit(cli())
