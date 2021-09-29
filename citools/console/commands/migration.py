from cleo import Command

from citools import test_triage_bug_filer


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


class MigrationCommands(Command):
    """
    Contains commands related to performing test migrations.

    migration
    """

    commands = [FileBugsCommand()]

    def handle(self):
        return self.call("help", self._config.name)
