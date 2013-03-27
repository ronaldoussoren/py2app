import sys
import os


root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )
    )

sys.argv[0] = os.path.realpath(sys.argv[0])
fp = open(os.path.join(root, "env.txt"), "w")
fp.write(repr(dict(os.environ)))
fp.write('\n')
fp.close()
