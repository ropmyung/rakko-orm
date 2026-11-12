# Modified for Rakko ORM: integrate this module into the rakko package namespace.

from .client import PsycopgClient

client_class = PsycopgClient
