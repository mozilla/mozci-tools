"""This script will display information about failing tests given a push.

To automatically open failures in vim you can set:

    $ export DUMP_FAILURES_EDIT_COMMAND="vim +/{test} +:vnew +':let f=append(1,{context})' /path/to/mozilla-central/{manifest}"
"""  # noqa: E501

import json
import os
import shlex
import subprocess
from collections import defaultdict
from typing import Dict, List

from mozci.push import Push
from mozci.task import TestTask
from mozci.util.logging import logger

RESULTS: Dict[str, Dict[str, Dict[str, List[int]]]] = defaultdict(
    lambda: defaultdict(lambda: defaultdict(lambda: [0, 0]))
)


def update_results(task):
    raw_log_path = [a for a in task.artifacts if a.endswith("raw.log")][0]
    raw_log = task.get_artifact(raw_log_path).text
    manifests = {}
    status = defaultdict(int)
    seen = set()
    for line in raw_log.splitlines():
        data = json.loads(line)
        if data["action"] == "suite_start":
            for manifest, tests in data["tests"].items():
                for t in tests:
                    manifests[t] = manifest

        if (
            data["action"] not in ("test_status", "test_end", "crash")
            or "test" not in data
        ):
            continue

        test = data["test"]

        if task.classification == "not classified" and (
            data["action"] == "crash"
            or ("expected" in data and data["status"] != data["expected"])
        ):
            status[test] |= 1

        if test not in seen and data["action"] in ("crash", "test_end"):
            try:
                manifest = manifests[test]
            except KeyError:
                try:
                    manifest = manifests[f"browser/{test}"]
                except KeyError:
                    logger.warning(f"Invalid test: {test}")
                    continue

            seen.add(test)
            result = RESULTS[manifest][test][task.label]
            result[status[test]] += 1


def dump_failures(branch, rev):
    push = Push(rev, branch)
    tasks = [t for t in push.tasks if isinstance(t, TestTask)]
    for task in tasks:
        logger.info(f"processing {task.label}")
        update_results(task)

    for manifest, tests in RESULTS.items():
        manifest_printed = False

        for test, tasks in tests.items():
            if not any(r[1] for r in tasks.values()):
                continue

            if not manifest_printed:
                print("\n" + manifest)
                manifest_printed = True

            print()
            print(f"  {test}")
            context = []
            for label, result in tasks.items():
                if not result[1]:
                    continue
                s = f"    {label}: {result[1]} / {result[0] + result[1]} failed"
                context.append(s)
                print(s)

            if manifest in ("dom/canvas/test/mochitest.ini",):
                continue

            if "DUMP_FAILURES_EDIT_COMMAND" in os.environ:
                context.insert(0, test)
                context = [line.strip() for line in context]
                context = '","'.join(context)
                context = f'["{context}"]'
                cmd = shlex.split(
                    os.environ["DUMP_FAILURES_EDIT_COMMAND"].format(
                        test=os.path.basename(test), manifest=manifest, context=context
                    )
                )
                subprocess.run(cmd)
