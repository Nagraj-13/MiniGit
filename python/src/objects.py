from __future__ import annotations
import hashlib
import time
from typing import List, Tuple
import zlib


class MiniGitObjects:
    def __init__(self, obj_type: str, content:bytes):
        self.type = obj_type
        self.content = content
        
    
    def hash(self)-> str:
        # hash format <type> <size>\0 <content> 
        header = f"{self.type} {len(self.content)}\0".encode()
        return hashlib.sha1(header + self.content).hexdigest()
    
    def serialize(self) -> bytes:
        header = f"{self.type} {len(self.content)}\0".encode()
        return zlib.compress(header + self.content)
    
    @classmethod
    def de_serialize(cls, data:bytes)-> MiniGitObjects:
        decompressed = zlib.decompress(data)
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx]
        content = decompressed[null_idx+1:]
        obj_type, size = header.split(b" ")
        
        return cls(obj_type.decode(), content)
    
    
class Blob(MiniGitObjects):
    def __init__(self, content:bytes):
        super().__init__('blob', content)
    
    def get_content(self) -> bytes:
        return self.content
    

class Tree(MiniGitObjects):
    def __init__(self, entries:List[Tuple[str,str,str]]=None):
        self.entries = entries or []
        content = self._serialize_entries()
        super().__init__("tree", content)
        
    def _serialize_entries(self) -> bytes:
        # <mode> <name>\0<hash><mode> <name>\0<hash><mode> <name>\0<hash>  # len(hash) = 20 ,, sha1 -> 20
        content = b""
        for mode, name, obj_hash in sorted(self.entries):
            content += f"{mode} {name}\0".encode()
            content += bytes.fromhex(obj_hash)
            
        return content
    
    def add_entry(self, mode:str, name:str, obj_hash:str):
        self.entries.append((mode, name, obj_hash))
        self.content = self._serialize_entries()
        
    @classmethod
    def from_content(cls, content:bytes)-> Tree:
        tree = cls()
        i=0
        while i < len(content):
            null_idx = content.find(b"\0",i)
            if null_idx == -1:
                break
            mode_name = content[i:null_idx].decode()
            mode, name = mode_name.split(" ", 1)
            if null_idx + 21 > len(content):
                raise ValueError("Corrupted tree object")
            obj_hash = content[null_idx + 1 : null_idx + 21].hex()
            tree.entries.append((mode, name, obj_hash))
            
            i = null_idx + 21
            
        return tree
    
    
class Commit(MiniGitObjects):
    def __init__(
        self, 
        tree_hash:str, 
        parent_hashes:List[str], 
        author:str, 
        committer:str,
        message: str,
        timestamp: int = None,
    ):  
        self.tree_hash = tree_hash
        self.parent_hashes = parent_hashes
        self.author = author
        self.committer = committer
        self.message = message
        self.timestamp = timestamp or int(time.time())
        
        content = self._serialize_commit()
        
        super().__init__("commit", content)
        
    def _serialize_commit(self):
        lines = [f"tree {self.tree_hash}"]
            
        for parent_hash in self.parent_hashes:
            lines.append(f"parent {parent_hash}")
                
        lines.append(f"author {self.author} {self.timestamp} +0000")  # +0000 -> utc standard time
        lines.append(f"committer {self.committer} {self.timestamp} +0000")
        lines.append(f"")
        lines.append(self.message)
        
        return "\n".join(lines).encode()
    
    @classmethod
    def from_content(cls, content:bytes) -> Commit:
        lines = content.decode().split("\n")
        tree_hash = None
        parent_hashes = []
        author = None
        committer = None
        message_start = 0
        
        for i, line in enumerate(lines):
            if line.startswith("tree "):
                tree_hash = line[5:]
            elif line.startswith("parent "):
                parent_hashes.append(line[7:])
            elif line.startswith("author "):
                author_parts = line[7:].rsplit(" ", 2)
                author = author_parts[0]
                timestamp = int(author_parts[1])
            elif line.startswith("committer "):
                committer_parts = line[10:].rsplit(" ", 2)
                committer = committer_parts[0]
            elif line == "":
                message_start = i + 1
                break
            
        message = "\n".join(lines[message_start:])
        commit  = cls(tree_hash, parent_hashes,author,committer,message, timestamp)
        return commit