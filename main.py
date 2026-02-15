import argparse
def main():
    parser = argparse.ArgumentParser(
        description="GetGit - A simple git clone"
    )
    
    subparser = parser.add_subparsers(dest="command",help="Available Help")
    
    init_parser = subparser.add_parser("init", help="Initialize a new repo")
    
    args = parser.parse_args()
    print(args)

main()