"""This script will display information about failing tests given a push.

To automatically open failures in vim you can set:

    $ export DUMP_FAILURES_EDIT_COMMAND="vim +/{test} +:vnew +':let f=append(1,{context})' /path/to/mozilla-central/{manifest}"
"""  # noqa: E501

import json
import os
import pathlib
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

REGRESSIONS: Dict[str, str] = defaultdict()


def find_related_manifest(path):
    found_paths = [path]
    try:
        # make absolute path in case this has symlinks
        path_absolute = pathlib.Path(path).resolve(strict=True).parent
        for found_manifest in pathlib.Path(path_absolute).glob("**/*.ini"):
            if found_manifest not in found_paths:
                found_paths.append(str(found_manifest))
    except FileNotFoundError:
        return found_paths
    except RuntimeError:
        return found_paths
    return found_paths


SKIPPED_MANIFESTS = find_related_manifest("dom/canvas/mochistest.ini")


def update_results(task):
    raw_log_path_list = [a for a in task.artifacts if a.endswith("raw.log")]
    if not raw_log_path_list:
        return
    raw_log_path = raw_log_path_list[0]
    raw_log = task.get_artifact(raw_log_path).text
    manifests = {}
    status = defaultdict(int)
    seen = set()
    for line in raw_log.splitlines():
        data = json.loads(line)
        if data["action"] == "suite_start":
            # When empty, data["tests"] is a list and not a dictionary
            # More context: https://github.com/mozilla/mozci-tools/issues/27
            if "tests" not in data or type(data["tests"]) is not dict:
                continue
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
                    if data["source"] == "web-platform-tests":
                        manifest = f"testing/web-platform/meta/{test}.ini"
                    else:
                        manifest = manifests[f"browser/{test}"]
                except KeyError:
                    logger.warning(f"Invalid test: {test}")
                    continue

            seen.add(test)
            result = RESULTS[manifest][test][task.label]
            result[status[test]] += 1


def dump_failures(branch, rev):
    push = Push(rev, branch)
    push_status, regressions = push.classify()

    process_regressions(regressions)

    tasks = [t for t in push.tasks if isinstance(t, TestTask)]
    for task in tasks:
        logger.info(f"processing {task.label}")
        update_results(task)

    summary_dict = summarize_failures()

    for manifest, tests in summary_dict.items():
        if manifest in REGRESSIONS:
            line = REGRESSIONS[manifest]
            print("\n" + manifest + " Regressions class: " + line)

        for test, context in tests.items():
            print(f"  {test}")
            if context:
                print(context)

            if manifest in SKIPPED_MANIFESTS:
                print(f" This: {manifest} has exceptions that are not supported yet")

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


def summarize_failures():
    summary_dict = {}
    for manifest, tests in RESULTS.items():
        summary_dict[manifest] = {}
        for test, tasks in tests.items():
            summary_dict[manifest][test] = []
            if not any(r[1] for r in tasks.values()):
                continue

            context = []
            for label, result in tasks.items():
                if not result[1]:
                    continue
                s = f"    {label}: {result[1]} / {result[0] + result[1]} failed"
                context.append(s)
            summary_dict[manifest][test] = context

    return summary_dict


def process_regressions_helper(regressions, regression_class):
    # get each manifest in the regressions
    for manifest in regressions:
        REGRESSIONS[manifest] = regression_class


def process_regressions(regressions):
    process_regressions_helper(regressions.real, "real")
    process_regressions_helper(regressions.unknown, "unknown")
    print("REGRESSIONS: ", REGRESSIONS)
