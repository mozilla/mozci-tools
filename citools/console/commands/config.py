import os
import subprocess

from cleo import Command
from mozci.configuration import config


class ConfigCommand(Command):
    """
    Open your mozci configuration file in an editor.

    config
    """

    def handle(self):
        path = config.path
        editor = os.environ.get("EDITOR")

        if editor is not None:
            subprocess.run([editor, path])
        else:
            self.line(f'{"Error: set the $EDITOR environment variable"}')
