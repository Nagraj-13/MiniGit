from __future__ import annotations
import hashlib
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
        obj_type, size = header.split(" ")
        
        return cls(obj_type, content)
    
    
class Blob(MiniGitObjects):
    def __init__(self, content:bytes):
        super().__init__('blob', content)
    
    def get_content(self) -> bytes:
        return self.content
    
    