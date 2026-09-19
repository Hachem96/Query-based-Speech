"""
Shared slowapi Limiter instance. Imported by ``main.py`` (to register the
exception handler + middleware) and by individual routers (to decorate
endpoints) so every route shares one limiter/storage.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
