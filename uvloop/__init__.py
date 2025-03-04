import asyncio

from asyncio.events import BaseDefaultEventLoopPolicy as __BasePolicy

from . import includes as __includes
from .loop import Loop as __BaseLoop


__all__ = ('new_event_loop', 'EventLoopPolicy')


class _Loop(__BaseLoop, asyncio.AbstractEventLoop):
    pass


def new_event_loop():
    """Return a new event loop."""
    return _Loop()


class EventLoopPolicy(__BasePolicy):
    """Event loop policy.

    The preferred way to make your application use uvloop:

    >>> import asyncio
    >>> import uvloop
    >>> asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    >>> asyncio.get_event_loop()
    <uvloop._Loop running=False closed=False debug=False>
    """

    def _loop_factory(self):
        return new_event_loop()
