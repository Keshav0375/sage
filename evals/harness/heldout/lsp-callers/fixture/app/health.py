import net


def ping():
    return net.fetch("https://example.com/health")["ok"]
