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
        try:
            self.clone_funos()
            repo = self.initialize_repository(STASH_DIR + "/FunOS")
            commits_list = self.get_commits_list(repo, faulty_commit, success_commit)
            start = False
            faulty = None
            for commit in commits_list:
                commit_detail = {}
                commit_detail["hexsha"] = commit.hexsha if commit.hexsha else None
                commit_detail["date"] = commit.authored_datetime if commit.authored_datetime else None
                commit_detail["message"] = commit.message if commit.message else None
                commit_detail["author"] = commit.author if commit.author else None
                commit_detail["changed_files"] = []
                if faulty is not None:
                    diff = faulty.diff(commit)
                    for file in diff:
                        if file.a_rawpath not in commit_detail["changed_files"]:
                            commit_detail["changed_files"].append(file.a_rawpath)
                if success_commit in commit.hexsha:
                    result["commits"].append(commit_detail)
                    break
                if start:
                    if "Merge pull" in commit.message:
                        result["commits"].append(commit_detail)
                        faulty = commit
                if faulty_commit in commit.hexsha:
                    faulty = commit
                    start = True
                    result["commits"].append(commit_detail)
        except Exception as ex:
            logger.exception("Exception: {}".format(str(ex)))
        return result

    def get_commits_list(self, repo, faulty_commit, success_commit):
        commits_list = list(repo.iter_commits('master'))
        # logs = repo.git.log('master', '{}...{}'.format(faulty_commit, success_commit)) #always returns from the latest commit and does not include merge commits and goes beyond the end commit
        return commits_list

if __name__ == "__main__":
     m = GitManager()
     list = m.get_commits_between('cee548b56f7ab19165473a2eee74d9b757cb4b6c', '651641b62b6e14a50f14a449a2144b7220dae6ca')
     print "Completed"