import requests
import dateutil.parser
from datetime import timedelta

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
                results = r.json()
                # results = [x for x in results if x["commit"]["message"].startswith("Merge")]
                # results = [x for x in results if x["commit"]["message"].startswith("Merge")]

                all_commits.extend(results)
        return all_commits


    def get_commit(self, sha, repository_name="FunOS"):
        result = None
        url = "{}/repos/{}/{}/commits/{}".format(self.BASE_URL, self.ORG, repository_name, sha)
        r = requests.get(url=url, headers={'Authorization': 'token {}'.format(self.TOKEN)})
        if r.status_code == 200:
            result = r.json()
        return result

    def get_commit_date(self, commit):
        d = commit["commit"]["author"]["date"]
        return dateutil.parser.parse(d)

    def get_commits_between(self, from_sha, to_sha):
        from_commit = self.get_commit(sha=from_sha)
        from_commit_iso_date_string = from_commit["commit"]["author"]["date"]
        to_commit = self.get_commit(sha=to_sha)
        to_commit_iso_date_string = to_commit["commit"]["author"]["date"]
        commits = self.get_all_commits(since=from_commit_iso_date_string, until=to_commit_iso_date_string)
        return commits

if __name__ == "__main__":
    gm = GitManager()
    from_sha = "49fd75d318c982b51236efe1319e2d186f8366b9"
    to_sha = "7ed046e9f5d2c2345cf05d4933884693fa43b6ee"

    commits = gm.get_commits_between(from_sha=from_sha, to_sha=to_sha)
    print("Num commits: {}".format(len(commits)))
    for commit in commits:
        print commit["sha"], commit["commit"]["committer"]["date"]
