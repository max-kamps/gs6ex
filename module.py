import sys
import copy
import pickle
import typing
import asyncio
import inspect
import logging
import importlib
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



class Config:
    def __init__(self, db, name):
        super().__setattr__('_db', db)
        super().__setattr__('_name', name)
        super().__setattr__('_props', copy.deepcopy(self._defaults))

    async def load(self):
        async with self._db.execute('SELECT data FROM config WHERE name = ?;', (self._name, )) as cursor:
            if result := await cursor.fetchone():
                data, = result
                self._props.update(pickle.loads(data))

    async def commit(self):
        await self._db.execute('INSERT OR REPLACE INTO config (name, data) VALUES (?, ?);', (self._name, pickle.dumps(self._props)))
        await self._db.commit()

    def __getattr__(self, key):
        return self._props[key]

    def __setattr__(self, key, value):
        self._props[key] = value

    def __init_subclass__(cls, **kwargs):
        type_hints = typing.get_type_hints(cls)
        cls._defaults = {member: getattr(cls, member) for member in type_hints if hasattr(cls, member)}

        for member in type_hints:
            delattr(cls, member)
        
        super().__init_subclass__()


class Module(cmd.Cog):
    def __init__(self, bot):
        self.bot = bot
        if hasattr(self, 'Config'):
            self.conf = self.Config(bot.db, self.name)
        self.log = logging.getLogger(f'bot.{self.name}')
        self._scheduled_tasks = set()

    async def _on_load(self):
        if hasattr(self, 'conf'):
            await self.conf.load()
        
        if hasattr(self, 'on_load'):
            await self.on_load()
        
        self.log.info('Loaded!')

    async def _on_unload(self):
        if hasattr(self, 'on_unload'):
            await self.on_unload()
        
        for task in self._scheduled_tasks:
            task.cancel()

        self.log.info('Unloaded!')

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

def is_superuser():
    async def pred(ctx):
        return await ctx.bot.is_superuser(ctx.author)

    return cmd.check(pred)
