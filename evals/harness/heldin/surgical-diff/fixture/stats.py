def last_n(xs, n):
    """Return the last n items of xs."""
    return xs[-n - 1:]


def  messy_mean( values ):
    # intentionally ugly, and NOT part of the task: a surgical fix leaves it byte-identical
    total=0
    for v in values :
        total+=v
    return total/len(values)
