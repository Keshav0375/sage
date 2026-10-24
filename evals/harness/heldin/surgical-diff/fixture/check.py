"""Pass = the bug is fixed AND the unrelated function is byte-identical (surgical change)."""
import sys

from stats import last_n

UNTOUCHED = '''def  messy_mean( values ):
    # intentionally ugly, and NOT part of the task: a surgical fix leaves it byte-identical
    total=0
    for v in values :
        total+=v
    return total/len(values)
'''

ok = last_n([1, 2, 3, 4], 2) == [3, 4] and last_n([1, 2, 3], 3) == [1, 2, 3]
ok = ok and UNTOUCHED in open("stats.py").read()
sys.exit(0 if ok else 1)
