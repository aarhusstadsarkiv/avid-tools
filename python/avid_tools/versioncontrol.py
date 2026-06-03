import logging
from pathlib import Path

import git

from avid_tools.utils import find_avid_dir

logger = logging.getLogger(__name__)


class AVIDVersionControl:
    """
    Perform version control on files that are to be edited
    """
    repo: git.Repo
    avid_dir: Path

    def __init__(self, avid_path: Path | None = None):
        self.avid_dir = avid_path if avid_path is not None else find_avid_dir(Path.cwd())

        if not self.avid_dir.joinpath(".git").exists():
            self.repo = git.Repo.init(self.avid_dir)
        else:
            self.repo = git.Repo(path=self.avid_dir)

    def _changed(self, file: str | Path) -> bool:
        if not self.repo.head.is_valid():
            return True

        unstaged = self.repo.index.diff(None, paths=[file])
        staged = self.repo.index.diff("HEAD", paths=[file])

        unchanged = (len(unstaged) == 0 and len(staged) == 0)
        return not unchanged

    def _rel_path(self, file: str | Path) -> Path:
        path = Path(file)
        if not path.is_absolute():
            path = self.avid_dir / path
        path = path.resolve()
        path.relative_to(self.avid_dir)  # raises if outside repo
        return path

    def _is_tracked(self, file: str | Path) -> Path:
        path = self._rel_path(file)
        return str(path) in self.repo.git.ls_files()  # pyright: ignore

    def add(self, file: str | Path, message: str | None = None) -> bool:
        rel_path = file if isinstance(file, str) else file.relative_to(self.avid_dir)

        if not Path(file).exists():
            raise FileNotFoundError(f"Cannot add missing file: {file}")

        if not self._changed(file):
            return False

        self.repo.index.add([file])
        self.repo.index.commit(f"ADD {rel_path}" if message is None else message)

        return True

    def delete(self, file: str | Path, message: str | None = None) -> bool:
        """
        Delete file from disk and register the deletion in the version control
        """ 
        file_rel = self._rel_path(file)

        if not file_rel.exists():
            return False

        if not self._is_tracked(file):
           # Only items changed are tracked by git, otherwise it becomes too large
           # add to git before removing
           self.add(file, f"ADD {file_rel} before removal")

        self.repo.index.remove(str(file_rel), working_tree=True)
        self.repo.index.commit(message or f"DELETE {file_rel}")
        return True

    def move(self, file_src: str | Path, file_dst: str | Path, message: str | None = None):
        src_path, dst_path = Path(file_src), Path(file_dst)
        if dst_path.exists():
            raise FileExistsError(f"Destination file {file_dst} exists")

        if not src_path.exists():
            raise FileNotFoundError(f"Source file {file_src} does not exist")

        src_path.copy(dst_path)
        self.delete(src_path, f"ADD {file_src} before move")
        self.add(dst_path, message)

        self.repo.index.move()

class AVIDEditFile:
    """
    Context manager that adds/commits a file on enter and exit
    """
    vc: AVIDVersionControl
    file: str | Path
    message: str | None

    def __init__(
            self,
            vc: AVIDVersionControl,
            file: str | Path,
            message: str | None = None
            ):
        self.vc = vc
        self.file = file
        self.message = message

    def __enter__(self) -> "AVIDEditFile":
        rel_path = self.file if isinstance(self.file,str) else self.file.relative_to(self.vc.avid_dir)
        logger.info(f"ADD {rel_path} pre modification")
        self.vc.add(self.file, self.message or f"ADD {rel_path} pre modification")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        rel_path = self.file if isinstance(self.file,str) else self.file.relative_to(self.vc.avid_dir)
        logger.info(f"ADD {rel_path} post modification")
        self.vc.add(self.file, self.message or f"ADD {rel_path} post modification")
        return False
