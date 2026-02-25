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
    
    commit_parser = subparser.add_parser(
        "commit", help="Create a new commit"
    )
    commit_parser.add_argument(
        "-m", 
        "--message", 
        help="Commit message" , 
        required=True
    )
    commit_parser.add_argument(
        "--author", 
        help="Author Name and email" , 
    )
    
    checkout_parser = subparser.add_parser(
        'checkout',
        help="Create or Switch to branch"
    )
    checkout_parser.add_argument(
        "branch",
        help="Branch to switch to"
    )
    checkout_parser.add_argument(
        "-b", 
        "--create-branch", 
        action="store_true", 
        help="create or switch to a new branch"
    )
    branch_parser = subparser.add_parser(
        "branch",
        help="List or manage the Branches"
    )
    branch_parser.add_argument(
        "name",
        nargs="?" 
    )
    
    branch_parser.add_argument(
        "-d",
        "--delete-branch",
        action="store_true",
        help="Delete a branch"
    )
    
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
        
        elif args.command == 'commit':
            if not repo.git_dir.exists():
                print("Not a git repository")
                return
            author = args.author or "MiniGit user <user@minigit>"
            repo.commit(args.message, author)
        elif args.command == "checkout":
            if not repo.git_dir.exists():
                print("Not a minigit repository")
                return
            repo.checkout(args.branch, args.create_branch)
        elif args.command == "branch":
            repo.branch(args.name, args.delete_branch)
          
    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)
    
    
main()

