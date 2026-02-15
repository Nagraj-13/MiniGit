
import json
from pathlib import Path


class Repository:
    def __init__(self, path="."):
        self.path = Path(path).resolve()
        self.git_dir = self.path / ".minigit"
        
        # .git/objects
        self.objects_dir = self.git_dir / "objects"
        # .git/refs
        self.refs_dir = self.git_dir / "refs"
        # .git/refs/heads
        self.heads_dir = self.refs_dir / "heads"
        # .git/hooks
        self.hooks_dir = self.git_dir / "hooks"
        # .git/info
        self.info_dir = self.git_dir / "info"
        # .git/logs
        self.logs_dir = self.git_dir / "logs"
        
        
        # .git/HEAD file
        self.head_file = self.git_dir / "HEAD"
        
         # .git/index file
        self.index_file = self.git_dir / "index"
        
    def init(self)-> bool:
        if self.git_dir.exists():
            return False
        #create directory
        self.git_dir.mkdir()
        self.objects_dir.mkdir()
        self.refs_dir.mkdir()
        self.heads_dir.mkdir()
        self.info_dir.mkdir()
        self.logs_dir.mkdir()
        self.hooks_dir.mkdir()
        
        # create initial HEAD pointing to a branch
        self.head_file.write_text("ref: refs/heads/master\n")
        
        self.index_file.write_text(json.dumps({},indent=4))
        
        print(f"Initialized an empty MiniGit repository in {self.git_dir}")
        
        return True
    
    