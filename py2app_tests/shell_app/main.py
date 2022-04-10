import os
import sys  # noqa: F401

root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

fp = open(os.path.join(root, "env.txt"), "w")
fp.write(repr(dict(os.environ)))
fp.write("\n")
fp.close()
