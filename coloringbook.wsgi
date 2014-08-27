# Uncomment and edit the following lines if the coloringbook package or
# your configuration file isn't already on the PYTHONPATH.

# import sys
# 
# sys.path.insert(0, '/absolute/path/to/coloringbook')
# 
# sys.path.insert(0, '/absolute/path/to/config')

import coloringbook
import config  # change this to a different name if applicable

application = coloringbook.create_app(config)
