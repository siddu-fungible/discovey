import requests
import dateutil.parser
from datetime import timedelta

class Commit():
    def __init__(self, sha, date):
        self.sha = sha
        self.date = date

    def __str__(self):
        return "Commit: sha {} date: {}".format(self.long_to_short_sha(sha=self.sha), self.date)

    def long_to_short_sha(self, sha):
        return sha[:7]

    def to_dict(self):
        r = {"sha": self.sha, "date": self.date}
        return r


class GitManager:
    BASE_URL = "https://api.github.com"
    ORG = "fungible-inc"
    TOKEN = "6e7ab48474553bbabceeefde388339204ecd6c0f"

    def get_all_commits(self, repository_name="FunOS", from_sha=None, since=None, until=None):
        results = None
        url = "{}/repos/{}/{}/commits".format(self.BASE_URL, self.ORG, repository_name)
        query_params = []

        if from_sha:
            query_params.append("sha={}".format(from_sha))
        if since:
            query_params.append("since={}".format(since))
        if until:
            query_params.append("until={}".format(until))
        if query_params:
            url += "?"
            for query_param in query_params:
                url += query_param
                url += "&"
            url = url[:-1]
        all_commits = []

        for page_index in range(1, 10):
            page_url = url + "&page={}&per_page={}".format(page_index, 100)
            r = requests.get(url=page_url, headers={'Authorization': 'token {}'.format(self.TOKEN)})
            if r.status_code == 200:
                response = r.json()
                # results = [x for x in results if x["commit"]["message"].startswith("Merge")]
                # results = [x for x in results if x["commit"]["message"].startswith("Merge")]
                response = [Commit(sha=x["sha"], date=x["commit"]["committer"]["date"]) for x in response]
                all_commits.extend(response)
        return all_commits


    def get_commit(self, sha, repository_name="FunOS"):
        result = None
        url = "{}/repos/{}/{}/commits/{}".format(self.BASE_URL, self.ORG, repository_name, sha)
        r = requests.get(url=url, headers={'Authorization': 'token {}'.format(self.TOKEN)})
        if r.status_code == 200:
            result = r.json()
            result = Commit(sha=result["sha"], date=result["commit"]["author"]["date"])
        return result

    def get_commit_date(self, commit):
        d = commit["commit"]["author"]["date"]
        return dateutil.parser.parse(d)

    def get_commits_between(self, from_sha, to_sha):
        from_commit = self.get_commit(sha=from_sha)
        from_commit_iso_date_string = from_commit.date
        to_commit = self.get_commit(sha=to_sha)
        to_commit_iso_date_string = to_commit.date
        commits = self.get_all_commits(since=from_commit_iso_date_string, until=to_commit_iso_date_string)
        return commits

if __name__ == "__main__":
    gm = GitManager()
    from_sha = "8c2bd8bec69ccc94b52dd2e99a0f1a107a83b936"
    to_sha = "3e776301dee23c0b0e5e74caf285886fc292a537"

    commits = gm.get_commits_between(from_sha=from_sha, to_sha=to_sha)
    print("Num commits: {}".format(len(commits)))
    for commit in commits:
        print commit.sha, commit.date