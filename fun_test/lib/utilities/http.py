import requests


def fetch_text_file(url):
    result = None
    try:
        requests_output = requests.get(url, timeout=3)
        if requests_output.status_code == 200:
            result = requests_output.content
        else:
            print("Unable to fetch {}. Status code: {}".format(url, requests_output.status_code))
    except Exception as ex:
        print("Requests failure: {}".format(str(ex)))

    return result


def fetch_binary_file(url, target_file_path):
    result = None
    try:
        requests_output = requests.get(url, timeout=3)
        if requests_output.status_code == 200:
            content = requests_output.content
            with open(target_file_path, "wb") as f:
                f.write(content)
            result = True
        else:
            print("Unable to fetch {}. Status code: {}".format(url, requests_output.status_code))
    except Exception as ex:
        print("Requests failure: {}".format(str(ex)))
    return result

if __name__ == "__main__":
    # print fetch_text_file(url="http://dochub.fungible.local/doc/jenkins/funos/latest/build_info.txt")
    pass
    fetch_text_file(url="http://dochub.fungible.local/doc/jenkins/funsdk/latest/Linux/funos.mips64-base.tgz")