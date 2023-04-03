import nextcord, datetime, time, sqlite3
from nextcord.ext import commands, application_checks
from typing import Optional

announcech_id = 630607111239368773
bot_devc_id = 991766420260143204
interval = 60

conn_news = sqlite3.connect("announcements.sqlite3")
c_news = conn_news.cursor()

c_news.execute("""CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER,
    message TEXT,
    role TEXT,
    time TEXT
)""")

#Temporary
def mkpages(iterable:Union[list,str,tuple,dict,set], items:int):
    pages = []
    items = 1 if items <= 0 else items
    for x in iterable:
        page = 0
        appending = True
        while appending:
            try:
                if len(pages[page]) < items:
                    pages[page].append(x)
                    appending = False
                else:
                    page += 1
            except:
                pages.append([x])
                appending = False
    return tuple(pages)

async def get_page(interaction, page) -> None:
    nextPage = nextcord.ui.Button(label=" Next", style=nextcord.ButtonStyle.blurple, emoji="➡️")
    prevPage = nextcord.ui.Button(label=" Previous", style=nextcord.ButtonStyle.blurple, emoji="⬅️")
    refreshPage = nextcord.ui.Button(label=" Refresh", style=nextcord.ButtonStyle.blurple, emoji="🔄")
    view = nextcord.ui.View(timeout=300)
    view.add_item(prevPage)
    view.add_item(refreshPage)
    view.add_item(nextPage)

    data = c_news.execute("SELECT id FROM schedule").fetchall()

    pagedData = mkpages(data, 8)
    dataContent = ""
    lastPage = ceil(len(data)/8)

    if page <= 0:
        page = lastPage
    elif page > lastPage:
        page = 1

    async def callbackNext(interaction):
        await getPage(interaction, page+1)
    async def callbackRefresh(interaction):
        await getPage(interaction, page)
    async def callbackPrev(interaction):
        await getPage(interaction, page-1)

    nextPage.callback = callbackNext
    refreshPage.callback = callbackRefresh
    prevPage.callback = callbackPrev

    try:
        for x in pagedData[page-1]:
            timing = c_news.execute(f"SELECT time FROM schedule WHERE id = {int(x[0])}").fetchone()[0]
            timing = timing.split(':')
            dataContent += f"• `{x[0]}` - <t:{datetime.datetime(timing[0], timing[1], timing[2], timing[3], timing[4], timing[5]).timestamp()}:r>\n\n"
    except:
        dataContent = "Empty" if dataContent == "" else dataContent
        page = 0

    embed = nextcord.Embed(title="List of pending announcements:", description=dataContent, color=0x3366cc)
    embed.set_footer(text=f"Page {page}/{lastPage}")
    try:
        await interaction.response.edit_message(embed=embed, view=view)
    except:
        await interaction.response.send_message(embed=embed, view=view)

class timed_news(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("timed news ready")
        while True:
            announcements = c_news.execute("SELECT id FROM schedule").fetchall()
            for x in announcements:
                timing = c_news.execute(f"SELECT time FROM schedule WHERE id = {x[0]}").fetchone()[0]
                timing = timing.split(':')
                timing = datetime.datetime(timing[0], timing[1], timing[2], timing[3], timing[4], timing[5])
                if datetime.datetime.now() >= timing:
                    message = c_news.execute(f"SELECT message FROM schedule WHERE id = {x[0]}").fetchone()[0]
                    role = c_news.execute(f"SELECT role FROM schedule WHERE id = {x[0]}").fetchone()[0]
                    announcech = await self.bot.fetch_channel(announcech_id)
                    await announcech.send(role)
                    await announcech.send(message)
                    c_news.execute(f"DELETE FROM schedule WHERE id = {x[0]}")
                    conn_news.commit()
            time.sleep(interval)

    @commands.Cog.listener()
    async def on_application_command_error(interaction:Interaction, error):
        error = getattr(error, "original", error)
        if isinstance(error, application_checks.ApplicationMissingPermissions):
            await interaction.response.send_message(f"{error}", ephemeral=True)
        else:
            raise error

    @slash_command(description="Make a scheduled announcement.", guild_id=630606651992309760)
    @application_checks.has_permissions(manage_channels=True)
    async def announce(self,
        interaction:nextcord.Interaction,
        ping_role:nextcord.Role = nextcord.SlashOption(description="Role to ping"),
        message:str = nextcord.SlashOption(description="Announcement message", max_length=2000),
        year:int = nextcord.SlashOption(description="year", min_value=1, max_value=9999),
        month:int = nextcord.SlashOption(description="month", min_value=1, max_value=12),
        day:int = nextcord.SlashOption(description="", min_value=1, max_value=31),
        hours:Optional[int] = nextcord.SlashOption(description="hours", default=0, min_value=0, max_value=24),
        minutes:Optional[int] = nextcord.SlashOption(description="minutes", default=0, min_value=0, max_value=60),
        seconds:Optional[int] = nextcord.SlashOption(description="seconds", default=0, min_value=0, max_value=60),
        ):
        allow = False
        if (month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12) and day > 31:
            pass
        elif (month == 4 or month == 6 or month == 9 or month == 11) and day > 30:
            pass
        elif year % 4 == 0 and month == 2 and day > 29:
            pass
        elif year % 4 != 0 and month == 2 and day > 28:
            pass
        elif year == 1 and day == 1:
            pass
        else:
            allow = True
        if allow and interaction.channel.id == bot_devc_id:
            current_id = 0
            try:
                f = open("id", "rt")
                current_id = int(f.read())
                f.close()
            except:
                pass
            f = open("id", "w")
            f.write(f"{current_id + 1}")
            f.close()
            sql = "INSERT INTO schedule (id, message, role, time) VALUES (?, ?, ?, ?)"
            val = (current_id, message, ping_role.mention, f"{year}:{month}:{day}:{hours}:{minutes}:{seconds}")
            c_news.execute(sql, val)
            conn_news.commit()
            await interaction.response.send_message(f"Announcement scheduled! IT will be posted in <t:{datetime.datetime(year, month, day, hours, minutes, seconds).timestamp()}:r>")
        elif interaction.channel.id != bot_devc_id and allow:
            await interaction.response.send_message(f"<#{bot_devc_id}>")
        elif not allow and interaction.channel.id == bot_devc_id:
            await interaction.response.send_message("Invalid time (Out of range.)")
        else:
            await interaction.response.send_message(f"Invalid time (Out of range.)\n<#{bot_devc_id}>")

    @slash_command(description="List all active announcement", guild_id=630606651992309760)
    @application_checks.has_permissions(manage_channels=True)
    async def list_announce(self, interaction:nextcord.Interaction):
        if interaction.channel.id == bot_devc_id:
            await get_page(interaction, 1)
        else:
            await interaction.response.send_message(f"<#{bot_devc_id}>")

    @slash_command(description="Remove an announcement", guild_id=630606651992309760)
    @application_checks.has_permissions(manage_channels=True)
    async def rm_announce(self, interaction:nextcord.Interaction, id:int = nextcord.SlashOption(description="ID of the announcement")):
        if interaction.channel.id == bot_devc_id:
            c_news.execute(f"DELETE FROM schedule WHERE id = {id}")
            conn_news.commit()
            await interaction.response.send_message("Announcement deleted")
        else:
            await interaction.response.send_message(f"<#{bot_devc_id}>")

    @slash_command(description="View the content of an announcement", guild_id=630606651992309760)
    @application_checks.has_permissions(manage_channels=True)
    async def view_announce(self, interaction:nextcord.Interaction, id:int = nextcord.SlashOption(description="ID of the announcement")):
        if interaction.channel.id == bot_devc_id:
            message = c_news.execute(f"SELECT message FROM schedule WHERE id = {id}").fetchone()[0]
            role = c_news.execute(f"SELECT role FROM schedule WHERE id = {id}").fetchone()[0]
            timing = c_news.execute(f"SELECT time FROM schedule WHERE id = {id}").fetchone()[0]
            timing = timing.split(':')
            await interaction.response.send_message(f"**# Preview:**\nPing Role: `{role}`\nTime: <t:{datetime.datetime(timing[0], timing[1], timing[2], timing[3], timing[4], timing[5]).timestamp()}:r>")
            await interaction.channel.send(message)
        else:
            await interaction.response.send_message(f"<#{bot_devc_id}>")

def setup(bot: commands.Bot):
    bot.add_cog(timed_news(bot))