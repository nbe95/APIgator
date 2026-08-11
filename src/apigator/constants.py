"""Global constants used throughout the APIgator application."""

import os
from uuid import uuid4

# Application version retrieved from environment variable, defaults to unknown
VERSION = os.getenv("APIGATOR_VERSION") or "(unknown)"

# Path to the configuration file that defines API queries and aggregation rules
CONFIG_FILE = "./config.yaml"

# Unique identifier for this APIgator instance, generated at startup
# Used for self-referencing request detection to prevent infinite loops
INSTANCE_ID = str(uuid4())
