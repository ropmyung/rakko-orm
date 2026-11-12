# Modified for Rakko ORM: integrate this module into the rakko package namespace.

from .client import AsyncpgDBClient

client_class = AsyncpgDBClient
