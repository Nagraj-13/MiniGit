import argparse
import sys

from src.repository import Repository

def main():
    parser = argparse.ArgumentParser(
        description="MiniGit - A simple git clone"
    )
    
    subparser = parser.add_subparsers(dest="command",help="Available Help")
    
    init_parser = subparser.add_parser("init", help="Initialize a new repo")
    init_parser = subparser.add_parser("add", help="Initialize a new repo")
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'init':
            repo = Repository()
            if not repo.init():
                print("Repository Already Exists")
                return
    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)
    
main()