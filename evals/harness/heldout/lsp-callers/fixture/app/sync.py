from net import fetch


def pull_all(urls):
    return [fetch(u) for u in urls]
