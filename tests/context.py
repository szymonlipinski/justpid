import pathlib
import sys

here = pathlib.Path(__file__).parent.resolve()

sys.path.insert(0, here / "..")

import simplepid as sp  # noqa: F401,E402
