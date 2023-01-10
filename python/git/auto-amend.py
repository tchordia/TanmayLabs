import subprocess
import typer
from typing import Any

from asdev.helper import get_product_dir
from asdev.runner import run
from rich import print
from rich.console import Console

console = Console()
print = console.print


def rund(cmd: str, *args, **kwargs) -> str:
    return run(cmd, *args, capture_output=True, **kwargs).stdout.decode("utf-8").strip()


app = typer.Typer()


@app.command("auto-amend")
def auto_amend() -> None:
    """Auto amend files to their last commit that touched them

    For each staged file, find the last commit that touched the file, and amend it
    with the changes to that file.
    
    """

    print(
        "If something goes terribly wrong... run the following command to undo changes"
    )
    head_commit = rund("git rev-parse HEAD")

    # Save changes in the stash
    stash_hash = rund("git stash create")
    print(f"git reset --hard {head_commit} && git stash apply {stash_hash}")

    run("git fetch origin master")
    staged_files: str = rund("git diff --cached --name-only")
    assert staged_files == "", "There are already staged files!"

    files: str = rund("git diff --name-only")
    lof = files.splitlines()

    for l in lof:
        commit: str = None
        is_commit_an_ancestor_of_master = None
        commit_msg = None
        y = None

        print("Processing file", l, style="magenta")
        commit = rund(f"git log -n 1 --pretty=format:%H -- {l}")
        if commit:
            is_commit_an_ancestor_of_master = run(
                f"git merge-base --is-ancestor  {commit} origin/master"
            ).returncode
            if is_commit_an_ancestor_of_master == 1:
                commit_msg = rund(f"git log -n 1 --pretty=format:%s {commit}")
                y = console.input(
                    f"Amend file [red]`{l}`[/red] to [red]{commit_msg}[/red]? [y/N]"
                )
                if y == "y":
                    print("Amending file to commit....", style="red")
                    run(f"git add {l}")
                    run(f"git commit --fixup={commit}")
                    continue

        print(
            f"Skipping file {l}. Commit: {commit}, commit_msg: {commit_msg}, is_commit_an_ancestor_of_master: {is_commit_an_ancestor_of_master == 0}"
        )

    merge_base = rund("git merge-base origin/master HEAD")
    run(f"git rebase --interactive --autosquash --autostash {merge_base}")


if __name__ == "__main__":
    app()
