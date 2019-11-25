import requests
import dateutil.parser
from datetime import timedelta
from dateutil import parser
from fun_global import get_current_time
import re
import time

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
    #TOKEN = "6e7ab48474553bbabceeefde388339204ecd6c0f"
    TOKEN = "f7d415ebb9247bb8ba41f77c3f5672cf40d3900e"

    def get_funsdk_build_props(self, build_number):
        url = "http://dochub.fungible.local/doc/jenkins/funsdk/{}/bld_props.json".format(build_number)
        bld_props = None
        try:
            r = requests.get(url)
            bld_props = r.json()
        except:
            pass
        return bld_props

    def get_bld_tags(self, repository_name="FunOS", earliest_date=get_current_time() - timedelta(days=30)):
        url = "{}/repos/{}/{}".format(self.BASE_URL, self.ORG, repository_name)
        url = "{}/repos/fungible-inc/FunOS/tags".format(self.BASE_URL)

        all_tags = []

        # r = requests.get(url=url, headers={'Authorization': 'token {}'.format(self.TOKEN)})
        earliest_date_found = False
        for page_index in range(1, 10):
            if earliest_date_found:
                break
            page_url = url + "?page={}&per_page={}".format(page_index, 100)
            r = requests.get(url=page_url, headers={'Authorization': 'token {}'.format(self.TOKEN)})
            if r.status_code == 200:
                response = r.json()
                # response = [x for x in response if len(x["parents"]) > 1]
                # results = [x for x in results if x["commit"]["message"].startswith("Merge")]
                # results = [x for x in results if x["commit"]["message"].startswith("Merge")]
                tags = response

                for tag in tags:
                    tag_name = tag["name"]
                    commit_sha = tag["commit"]["sha"]
                    c = self.get_commit(sha=commit_sha)
                    commit_date = parser.parse(c.date)
                    # print tag_name, commit_sha, commit_date
                    if commit_date < earliest_date and tag_name.startswith("bld_"):
                        earliest_date_found = True
                    if tag_name.startswith("bld_"):
                        build_number = re.sub(r'bld_', '', tag_name)
                        bld_props = self.get_funsdk_build_props(build_number=build_number)
                        new_tag = {"name": tag_name, "sha": commit_sha, "date": commit_date, "bld_props": bld_props}
                        all_tags.append(new_tag)
        return all_tags

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
        query_params.append("merges=true")
        query_params.append("base=master")

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
                # response = [x for x in response if len(x["parents"]) > 1]
                # results = [x for x in results if x["commit"]["message"].startswith("Merge")]
                results = [x for x in response if x["commit"]["message"].startswith("Merge")]
                response = [Commit(sha=x["sha"], date=x["commit"]["committer"]["date"]) for x in results]
                all_commits.extend(response)
            print("Sleeping for 1 second")
            time.sleep(1)
        return all_commits


    def get_commit(self, sha, repository_name="FunOS"):
        result = None
        url = "{}/repos/{}/{}/commits/{}".format(self.BASE_URL, self.ORG, repository_name, sha)
        r = requests.get(url=url, headers={'Authorization': 'token {}'.format(self.TOKEN)}, verify=True)
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
    # from_sha = "c1c35d173a"
    #to_sha = "e352ca6d8e"

    from_sha = "a11bab8"
    to_sha = "178b6eb"

    """
    gm.get_bld_tags()
    """


    commits = gm.get_commits_between(from_sha=from_sha, to_sha=to_sha)
    print("Num commits: {}".format(len(commits)))
    for commit in commits:
        print commit.sha, commit.date



    s1 = "2019-05-22T21:22:00Z"
    s2 = "2019-05-25T06:22:45Z"