import asyncio
import importlib
import inspect
import logging
import sys
import shelve
from datetime import datetime as dt, timezone as tz

from discord.backoff import ExponentialBackoff
from discord.ext import commands as cmd

# Currently, the module system is just a wrapper over the
# cog and extension system provided by the commands library, with some minor extensions.
# In the future, it might be better to implement this from the ground up,
# including only the features we need.


# We re-export various discord extensions so we could intercept them in the future.
command = cmd.command
group = cmd.group

CheckFailure = cmd.CheckFailure

parent_module = __name__.rsplit('.', maxsplit=1)[0]


def get_logger():
    calling_frame = inspect.stack()[1].frame
    module_name = inspect.getmodule(calling_frame).__name__

    prefix = f'{parent_module}.modules.'
    if module_name.startswith(prefix):
        module_name = module_name[len(prefix):]

    return logging.getLogger(f'bot.{module_name}')


class Module(cmd.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conf = shelve.open(str(bot.config_dir / self.name), writeback=True)
        self.log = logging.getLogger(f'bot.{self.name}')
        self._scheduled_tasks = set()
        self._on_load()

    def __del__(self):
        # Ensure shelf is definitely closed
        self.conf.close()

    def _on_load(self):
        if hasattr(self, 'on_load'):
            self.on_load()
        
        self.log.info('Loaded!')

    def _on_unload(self):
        for task in self._scheduled_tasks:
            task.cancel()

        if hasattr(self, 'on_unload'):
            self.on_unload()

        self.conf.close()

        self.log.info('Unloaded!')

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.cog_unload = cls._on_unload

    def schedule_task(self, coro, *, in_delta=None, at_datetime=None):
        if in_delta is not None:
            in_seconds = in_delta.total_seconds()

        elif at_datetime is not None:
            in_seconds = (at_datetime - dt.now(tz.utc)).total_seconds()

        else:
            raise TypeError('Must supply either in_delta or at_datetime')

        async def scheduled_closure():
            try:
                await asyncio.sleep(in_seconds)
                await coro

            finally:
                self._scheduled_tasks.discard(asyncio.current_task())

        task = asyncio.create_task(scheduled_closure())
        self._scheduled_tasks.add(task)
        return task

    def schedule_repeated(self, coro, *args, every_delta):
        async def scheduled_closure():
            try:
                while True:
                    try:
                        await coro(*args)

                    except asyncio.CancelledError:
                        return

                    except Exception:
                        self.log.error('Exception in repeated schedule:', exc_info=True)

                    await asyncio.sleep(every_delta.total_seconds())

            finally:
                self._scheduled_tasks.discard(asyncio.current_task())

        task = asyncio.create_task(scheduled_closure())
        self._scheduled_tasks.add(task)
        return task

def get_module_class(name):
    # First we (re)load the python module containing the module class
    module_path = f'{parent_module}.modules.{name}'
    
    if module_path in sys.modules:
        py_module = importlib.reload(sys.modules[module_path])

    else:
        py_module = importlib.import_module(module_path)

    # Get a list of Module subclasses defined in the python module
    module_classes = inspect.getmembers(py_module, lambda x: inspect.isclass(x) and issubclass(x, Module))

    assert len(module_classes) == 1, f'Module {name!r} should define exactly one Module class, not {len(module_classes)}'

    module_class = module_classes[0][1]

    # Make sure the cog and the module system use the same name.
    # This will become unneccessary if we ever depending on the cog system.
    module_class.__cog_name__ = module_class.name = name

    # inspect.getmembers returns (name, member) tuples.
    # We only want the member, not the name.
    return module_classes[0][1]


def is_owner():
    async def pred(ctx):
        return await ctx.bot.is_owner(ctx.author)

    return cmd.check(pred)