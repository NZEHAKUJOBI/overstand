"""
Dynamic settings loader based on DJANGO_ENV environment variable.

- 'dev' (default): Development settings
- 'prod': Production settings
- 'test': Test settings (optional)
"""

import os

env = os.environ.get("DJANGO_ENV", "dev").lower()

if env == "prod":
    from .prod import *  # noqa: F401 F403
else:
    from .dev import *  # noqa: F401 F403
