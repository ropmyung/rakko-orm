# Modified for Rakko ORM: integrate this module into the rakko package namespace.

import logging

logger = logging.getLogger("tortoise")
db_client_logger = logging.getLogger("tortoise.db_client")
