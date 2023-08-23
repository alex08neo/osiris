from discord.ext import commands

class UserBlacklisted(commands.CheckFailure):
    def __init__(self):
        super().__init__("User is blacklisted.")

class UserNotOwner(commands.CheckFailure):
    def __init__(self):
        super().__init__("User is not the owner of the bot.")

class UserNotServerAdmin(commands.CheckFailure):
    def __init__(self):
        super().__init__("User is not an admin of the server.")