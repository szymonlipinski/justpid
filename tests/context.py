import pathlib
import sys

here = pathlib.Path(__file__).parent.resolve()

sys.path.insert(0, here / "..")

import justpid as jp  # noqa: F401,E402
