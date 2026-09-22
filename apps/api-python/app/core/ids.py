"""Centralised ID generation — cuid2 for all primary keys."""
from cuid2 import cuid_wrapper

_gen = cuid_wrapper()


def new_id() -> str:
    return _gen()
