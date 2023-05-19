import sys

from cleo.application import Application

from citools.console.commands.config import ConfigCommand
from citools.console.commands.migration import FileBugsCommand
from citools.console.commands.push import PushFailuresCommand


def cli():
    application = Application()
    application.add(PushFailuresCommand())
    application.add(FileBugsCommand())
    application.add(ConfigCommand())
    application.run()


if __name__ == "__main__":
    sys.exit(cli())
