from fun_settings import *
import logging
from fun_global import *
import git
import os

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
class GitManager:
    def initialize_repository(self, repo_dir):
        repo = git.Repo(repo_dir)
        return repo

    def clone_funos(self):
        if (os.path.exists(STASH_DIR + "/FunOS") == False):
            git.Git(STASH_DIR).clone("git@github.com:fungible-inc/FunOS.git")
        else:
            repo = self.initialize_repository(STASH_DIR + "/FunOS")
            repo.remotes.origin.pull()

    def get_commits_between(self, faulty_commit, success_commit):
        result = {}
        result["commits"] = []
        result["changed_files"] = []
        try:
            self.clone_funos()
            repo = self.initialize_repository(STASH_DIR + "/FunOS")
            commits_list = self.get_commits_list(repo, faulty_commit, success_commit)
            start = False
            for commit in commits_list:
                if success_commit in commit.hexsha:
                    success = commit
                    break
                if start:
                    result["commits"].append(commit)
                if faulty_commit in commit.hexsha:
                    faulty = commit
                    start = True
            diff = faulty.diff(success)
            for file in diff:
                result["changed_files"].append(file.a_rawpath)
        except Exception as ex:
            logger.exception("Exception: {}".format(str(ex)))
        return result

    def get_commits_list(self, repo, faulty_commit, success_commit):
        commits_list = list(repo.iter_commits('master'))
        # logs = repo.git.log('master', '{}...{}'.format(faulty_commit, success_commit)) #always returns from the latest commit and does not include merge commits and goes beyond the end commit
        return commits_list

if __name__ == "__main__":
     m = GitManager()
     list = m.get_commits_between('0af7f75c8a6f89620792ecd6f46212cda81a40b3', 'ec109dc331af27c23a23203b9cff9619e515cbfd')
     print "Completed"