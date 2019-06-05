from lib.utilities.git_utilities import GitManager

if __name__ == "__main__":
    gm = GitManager()
    tags = gm.get_bld_tags()
    for tag in tags:
        print tag