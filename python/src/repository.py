import json
from pathlib import Path
from typing import Dict
from src.objects import Blob, MiniGitObjects

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
        
    def init(self) -> bool:
        if self.git_dir.exists():
            return False
        try:
            # create layout
            for d in (self.objects_dir, self.refs_dir, self.heads_dir,
                      self.info_dir, self.logs_dir, self.hooks_dir):
                d.mkdir(parents=True, exist_ok=True)

            # initial HEAD (use main for modern convention)
            self.head_file.write_text("ref: refs/heads/master\n")
            # empty index
            self.index_file.write_text(json.dumps({}, indent=4))  # or self.save_index({})
            print(f"Initialized an empty MiniGit repository in {self.git_dir}")
            return True
        except Exception as e:
            print(f"Failed to initialize repository: {e}")
            return False
    
    def store_object(self, obj:MiniGitObjects)-> str:
        obj_hash = obj.hash()
        obj_directory = self.objects_dir/obj_hash[:2]
        obj_file = obj_directory / obj_hash[2:]
        
        if not obj_directory.exists():
            obj_directory.mkdir(exist_ok=True)
            obj_file.write_bytes(obj.serialize())

        return obj_hash
    
    def load_index(self)-> Dict[str, str]:
        if not self.index_file.exists():
            return {}
        try:
            return json.loads(self.index_file.read_text())
        
        except:
            return {}
    
    def save_index(self, index: Dict[str, str]):
        self.index_file.write_text(json.dumps(index, indent=4))
    
    def add_file(self, path:str):
        # Read file content 
        # Create blob object from the content and compress it
        # store the blob in the databse (.git/objects or .minigit/objects)
        # update the index to include the file
        full_path = self.path / path
        if not full_path.exists():
             raise FileNotFoundError(f"File {path} not found")
         
        content = full_path.read_bytes()
        
        blob = Blob(content)
        
        blob_hash= self.store_object(blob)
        index = self.load_index()
        index[path] = blob_hash
        self.save_index(index)
        print(f"Added  {path}")
        
    def add_directory(self, path):
        # recurively traverse the directory
        # create blog objects for each file
        # store all the blobs in the object database (.minigit/objects)
        # update the index to include all the files
        full_path = self.path / path
        
        if not full_path.exists():
             raise FileNotFoundError(f"File {path} not found")\
                 
        if not full_path.is_dir():
            raise ValueError(f"{path} is not a directory")
        
        index = self.load_index()
        added_count = 0
        
        for file_path in full_path.rglob("*"):
            if file_path.is_file():
                if ".minigit" in file_path.parts:
                    continue
                
                content = file_path.read_bytes()
                blob = Blob(content)
                blob_hash = self.store_object(blob)
                relative_path = str(file_path.relative_to(self.path))
                index[relative_path] = blob_hash
                added_count += 1
                
        self.save_index(index)       
        if added_count > 0:
            print(f"Added {added_count} files from the directory {path}")
        else:
            print(f"Directory {path} is already up to date")
            
    def add_path(self, path)->None:
        full_path = self.path / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        
        if full_path.is_file():
            self.add_file(path)
        elif full_path.is_dir():
            self.add_directory(path)
        else:
            raise ValueError(f"{path} is neither a file nor a directory")
        
    