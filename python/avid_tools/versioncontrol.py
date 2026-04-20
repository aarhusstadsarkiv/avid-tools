from pathlib import Path
from avid_tools.utils import find_avid_dir

import git


class AVIDVersionControl:
    """
    Perform version control on files that are to be edited
    """
    repo: git.Repo

    def __init__(self, avid_path: Path | None = None):
        avid_dir = avid_path if avid_path is not None else find_avid_dir(Path.cwd())

        if not avid_dir.joinpath(".git").exists():
            self.repo = git.Repo.init()
        else:
            self.repo = git.Repo(path=avid_dir)

    def _changed(self, file: str | Path) -> bool:
        if not self.repo.head.is_valid():
            return True

        unstaged = self.repo.index.diff(None, paths=[file])
        staged = self.repo.index.diff("HEAD", paths=[file])

        unchanged = (len(unstaged) == 0 and len(staged) == 0)
        return not unchanged

    def add(self, file: str | Path, message: str | None = None) -> bool:
        if not self._changed(file):
            return False

        self.repo.index.add([file])
        self.repo.index.commit("ADDED File" if message is None else message)

        return True
