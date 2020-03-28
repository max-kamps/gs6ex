import asyncio
import importlib
import inspect
import logging
import sys

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

    print(f'bot.{module_name}')
    return logging.getLogger(f'bot.{module_name}')


class Module(cmd.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conf = bot.get_shelf(self.name)
        self.log = logging.getLogger(f'bot.{self.name}')
        self._on_load()

    def _on_load(self):
        if hasattr(self, 'on_load'):
            self.on_load()
        
        self.log.info('Loaded!')

    def _on_unload(self):
        self.conf.sync()
        if hasattr(self, 'on_unload'):
            self.on_unload()

        self.log.info('Unloaded!')

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.cog_unload = cls._on_unload


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


def is_superuser():
    async def pred(ctx):
        return await ctx.bot.is_owner(ctx.author) or ctx.message.author.id in ctx.bot.conf['superusers']

    return cmd.check(pred)