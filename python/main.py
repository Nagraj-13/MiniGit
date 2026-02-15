import argparse
import sys

from src.repository import Repository

def main():
    parser = argparse.ArgumentParser(
        description="MiniGit - A simple git clone"
    )
    
    subparser = parser.add_subparsers(dest="command",help="Available Help")
    
    init_parser = subparser.add_parser("init", help="Initialize a new repo")
    add_parser = subparser.add_parser(
        "add", help="Add files and directories to the staging area"
    )
    add_parser.add_argument("paths", nargs='+' , help="Files and directories to add")
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    repo = Repository()
    try:
        if args.command == 'init':
            if not repo.init():
                print("Repository Already Exists")
                return
            
        elif args.command == 'add':
            if not repo.git_dir.exists():
                print("Not a git repository")
                return
            for path in args.paths:
                repo.add_path(path)
    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)
    
main()

