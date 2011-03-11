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

fp = open(os.path.join(root, "argv.txt"), "w")
fp.write(repr(sys.argv))
fp.write('\n')
fp.close()
