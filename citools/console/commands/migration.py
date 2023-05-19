from cleo.commands.command import Command
from cleo.helpers import argument, option

from citools import test_triage_bug_filer


class FileBugsCommand(Command):
    name = "migration file-bugs"
    description = "Files bugs for tests skipped due to new or migrating platforms."
    arguments = [
        argument(
            "diff",
            description="Path to diff that skips tests",
        )
    ]
    options = [
        option(
            "reason",
            description="Reason tests are being skipped.",
        ),
        option(
            "bug-id",
            description="Bugzilla ID of the bug that will be landing the changes.",
        ),
        option(
            "try-url",
            description="URL to the try push demonstrating failures.",
        ),
        option(
            "dry-run",
            description="Don't submit bugs, instead print a string representation.",
        ),
    ]
    help = test_triage_bug_filer.__doc__

    def handle(self):
        test_triage_bug_filer.process_diff(
            self.argument("diff"),
            self.option("reason"),
            self.option("bug-id"),
            try_url=self.option("try-url"),
            dry_run=self.option("dry-run"),
        )
