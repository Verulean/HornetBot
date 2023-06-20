import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context, errors
import logging
import time
from datetime import datetime, timedelta
import os

from components import auth, helpcmd, embeds

import config
import save

# Move old log and timestamp
if not os.path.exists(config.LOG_FOLDER): os.mkdir(f"./{config.LOG_FOLDER}")
if os.path.exists(config.LOG_PATH): os.rename(config.LOG_PATH, f"{config.LOG_FOLDER}/{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S_hornet.log')}")
# Setup logging
log_handler = logging.FileHandler(filename=config.LOG_PATH, encoding="utf-8", mode="w")
discord.utils.setup_logging(handler=log_handler, level=logging.DEBUG, root = True)

def getParams(cmd: commands.Command):
    paramstring = ""
    for name, param in cmd.params.items():
        if not param.required: 
            paramstring += f"*<{param.name}>* "
        else: 
            paramstring += f"<{param.name}> "
    print(f"{cmd.name} {paramstring}")
    return cmd.usage if cmd.usage is not None else paramstring

class HornetBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        # Intents (all)
        intents = discord.Intents.default()
        intents.message_content = True
        intents.presences = True
        intents.members = True
        self.case_insensitive = True
        super().__init__(intents=intents, help_command=helpcmd.HornetHelpCommand(), case_insensitive=True, max_messages=10000, **kwargs)

    async def on_ready(self):
        """Load modules after load"""
        modules = []
        for file in os.listdir(f"{os.path.dirname(__file__)}/modules/"):
            if not file.endswith(".py"): continue
            mod_name = file[:-3]   # strip .py at the end
            modules.append(mod_name)
            
        # Add extensions from /modules/
        for ext in modules:
            await self.load_extension(f"modules.{ext}")
        save.initModules()
    
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        ectx = embeds.EmbedContext(ctx)

        command = ctx.command
        cog = ctx.cog
        if command and command.has_error_handler(): return
        if cog and cog.has_error_handler(): return

        if isinstance(error, commands.errors.MissingRequiredArgument):
            cmd = ctx.command
            await ectx.embedReply(title=f"Command: {ctx.prefix}{cmd} {getParams(cmd)}", \
                                  message=f"Required parameter `{error.param.name}` is missing")
            return
        
        await ectx.embedReply(title=f"Unhandled exception in Hornet!", \
                              message=f"Consider reporting to <@196347053100630016>\r\n```{str(error.with_traceback(None))}```")
        
        return await super().on_command_error(ctx, error)

botInstance = HornetBot(command_prefix =';', activity=discord.Game(name="Hollow Knight: Silksong"))

# Base bot commands
@botInstance.command(help="pong!", hidden=True)
async def ping(context: Context):
    await context.reply('pong!')

@botInstance.command(help="Time since bot went up", hidden=True)
async def uptime(context: Context):
    await embeds.embedMessage(context, title="Uptime:", message=f"{timedelta(seconds=int(time.time() - startTime))}")

@botInstance.command(help="Get user's avatar by id")
async def avatar(context: Context, user: discord.User):
    await context.reply(user.display_avatar.url)

@botInstance.command(help="Add admin role (owner only)")
@commands.check(auth.isOwner)
async def addAdminRole(context: Context, role: discord.Role):
    save.getGuildData(context.guild.id)["adminRoles"].append(role.id)
    save.save()
    await context.message.delete()

@botInstance.command(help="Remove admin role (owner only)")
@commands.check(auth.isOwner)
async def removeAdminRole(context: Context, role: discord.Role):
    save.getGuildData(context.guild.id)["adminRoles"].remove(role.id)
    save.save()
    await context.message.delete()

startTime = time.time()
botInstance.run(config.token)