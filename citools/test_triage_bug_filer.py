"""
This script automates the process of filing bugs for tests skipped due to new
or migrating platforms.

It requires a bit of setup to use:

1. Ensure you can login via the bugzilla client. First add:

    [DEFAULT]
    url = https://bugzilla.mozilla.org

to ~/.config/python-bugzilla/bugzillarc. Next generate a new API key from
your Bugzilla profile and paste it into the prompt you get from:

    $ bugzilla login --api-key`.

If you'd like to test the tool out, use `https://bugzilla.allizom.org` as the
url instead and request a test account from #bmo in slack.

2. Set the `GECKO` environment variable to your mozilla-central clone.

3. Craft the patch that disables tests. You can optionally use `{{bug}}` as a
placeholder for the bug id, or {{reason}} as a placeholder for the reason string.
E.g:

    skip-if =
      os == "linux" && debug  # {{bug}} - {{reason}}


4. Export the patch to a file:

    $ hg export . > orig.patch

5. Run the tool. You'll need to supply the patch file, a reason string and an
optional try url. Also consider redirecting the output to a new file:

    $ ./test-triage-bug-filer path/to/orig.patch "new platform triage for foo" --try-url <try push url> > new.patch

6. Import the new patch and prune the old one:

    $ hg import new.patch
    $ hg prune -r <old revision>
"""  # noqa: E501


import json
import os
import subprocess
import sys
import traceback
from itertools import chain

import bugzilla
from unidiff import PatchSet

bzapi = bugzilla.Bugzilla("https://bugzilla.mozilla.org")

BUG_SUMMARY_TEMPLATE = "Tests skipped in '{path}' for {reason}"
BUG_DESCRIPTION_TEMPLATE = """
Note: This bug was filed automatically [via script](https://hg.mozilla.org/build/braindump/file/tip/test-related/test-triage-bug-filer).

The following tests are being disabled in [{path}](https://searchfox.org/mozilla-central/source/{path}) due to {reason}:
{skipped_tests}

Full diff:
```diff
{diff}
```
{try_blurb}
### Disclaimer
Adding new platforms is not an exact science, and in order to get to green and
enable coverage ASAP, we often err on the side of disabling when in doubt. For
this reason, it's possible that the annotation was added in error, is covered
by an existing intermittent, or was fixed sometime between now and when the
annotation was made.

If you believe this is the case here, please feel free to remove the
annotation. Sorry for the inconvenience and thanks for understanding.
""".lstrip()  # noqa: E501

TRY_BLURB_TEMPLATE = """
{try_url}
To run these failures in your own try push, first ensure the patches from bug {bug_id}
have landed, revert the `skip-if` annotations, then run:
```bash
$ ./mach try fuzzy --rebuild 3 {path}
```

Finally use the [fuzzy interface](https://firefox-source-docs.mozilla.org/tools/try/selectors/fuzzy.html) to select the task(s) which are relevant to the
`skip-if` expression(s).
"""  # noqa: E501

TRY_URL_TEMPLATE = """
See this [try push]({try_url}) for failures. If failures are missing, they were
either discovered on a subsequent try push or this bug is invalid.
"""


def get_bug_components(paths):
    proc = subprocess.run(
        ["mach", "file-info", "bugzilla-component", "--format=json"] + paths,
        capture_output=True,
        text=True,
        check=True,
        cwd=os.environ["GECKO"],
    )
    return json.loads(proc.stdout)


def get_skipped_tests(manifest):
    skipped_tests = set()
    for hunk in manifest:
        last_test = "unknown"
        last_key = None
        for line in hunk:
            if line.value.startswith("["):
                last_test = line.value.strip().strip("[]")
            elif not line.value.startswith(" ") and "=" in line.value:
                last_key = line.value[: line.value.index("=")].strip()

            if not line.is_added or "{bug}" not in line.value:
                continue

            if last_key == "skip-if":
                skipped_tests.add(last_test)
    return skipped_tests


def create_bug(
    product,
    component,
    summary,
    description,
    depends_on,
    bugtype="task",
    version="unspecified",
    dry_run=False,
    **kwargs,
):
    if dry_run:
        description = "  " + "\n    ".join(description.splitlines())
        print(
            f"""
The following bug would be filed:
  {summary}
  Product: {product}
  Component: {component}
  Depends on: {depends_on}
  Description:
  {description}
"""
        )
        return

    createinfo = bzapi.build_createbug(
        product=product,
        component=component,
        summary=summary,
        description=description,
        version=version,
        depends_on=depends_on,
    )
    createinfo["type"] = bugtype
    createinfo.update(kwargs)
    try:
        bug = bzapi.createbug(createinfo)
        print(bug.weburl, file=sys.stderr)
        return bug.id
    except Exception:
        print("Failed to create bug:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)


def process_diff(
    diff: str, reason: str, depends_on: str, try_url: str = "", dry_run: bool = False
):
    if not bzapi.logged_in:
        bzapi.interactive_login()

    try_url = try_url or ""

    patch = PatchSet.from_filename(diff, encoding="utf-8")
    components = get_bug_components([m.path for m in patch])

    for manifest in patch:
        if (
            not manifest.path.endswith(".ini")
            or "testing/web-platform" in manifest.path
        ):
            continue

        skipped_tests = get_skipped_tests(manifest)
        if not skipped_tests:
            continue

        product, component = components[manifest.path]
        summary = BUG_SUMMARY_TEMPLATE.format(path=manifest.path, reason=reason)

        skipped_tests_str = "* " + "\n* ".join(skipped_tests)
        if try_url:
            url = TRY_URL_TEMPLATE.format(
                try_url=f"{try_url}&test_paths={manifest.path}"
            )
        try_blurb = TRY_BLURB_TEMPLATE.format(
            path=manifest.path, try_url=url, bug_id=depends_on
        )
        description = BUG_DESCRIPTION_TEMPLATE.format(
            path=manifest.path,
            reason=reason,
            skipped_tests=skipped_tests_str,
            diff=str(manifest),
            try_blurb=try_blurb,
        )
        bug_id = create_bug(
            product, component, summary, description, depends_on, dry_run=dry_run
        )
        if not bug_id:
            continue

        for line in chain.from_iterable([hunk for hunk in manifest]):
            if line.is_added:
                line.value = line.value.replace("{bug}", f"Bug {bug_id}")
                line.value = line.value.replace("{reason}", reason)

    if not dry_run:
        print(patch)
