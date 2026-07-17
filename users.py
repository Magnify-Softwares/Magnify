import asyncio
import aiohttp
import json
from discord import Client, Embed
import sys


TOKEN = ""  
TARGET_SERVER_ID = 1
WEBHOOK_URL = ""


VERBOSE = True


class MemberDumper(Client):
    def __init__(self):
        super().__init__()
        self.webhook_session = None
        self.member_data = []
        self.progress = 0
        
    async def on_ready(self):
        
        self.webhook_session = aiohttp.ClientSession()
        
        guild = self.get_guild(TARGET_SERVER_ID)
        if not guild:
            print("[✗] Server not found! Check the ID or permissions.")
            await self.close()
            return
        
        print("[⏳] Fetching member list... (this may take a moment)")
        await guild.chunk()
        
        members = guild.members
        total = len(members)
        print(f"[✓] Found {total} members. Processing...")
        

        chunk_size = 10  
        chunks = [members[i:i+chunk_size] for i in range(0, len(members), chunk_size)]
        
        for idx, chunk in enumerate(chunks):
            await self.send_member_chunk(chunk, idx + 1, len(chunks))
            await asyncio.sleep(0.5)  
        
        await self.send_summary(total)
        
        print(f"[✓] Complete! Dumped {total} members to webhook.")
        await self.close()
        
    async def send_member_chunk(self, chunk, chunk_num, total_chunks):
        """Send a chunk of members as an embed"""
        try:
            embed = Embed(
                title=f"👥 Member List – Part {chunk_num}/{total_chunks}",
                description=f"Showing {len(chunk)} members",
                color=0x00ffcc,
                timestamp=datetime.now()
            )
            
            for member in chunk:
                status_emoji = {
                    "online": "🟢",
                    "idle": "🟡",
                    "dnd": "🔴",
                    "offline": "⚫"
                }.get(str(member.status), "⚫")
                
                bio = getattr(member, "bio", "No bio set") or "No bio set"
                
                member_info = (
                    f"**{status_emoji} {member.display_name}**\n"
                    f"┣ 📛 `{member.name}#{member.discriminator}`\n"
                    f"┣ 🆔 `{member.id}`\n"
                    f"┣ 🖼️ [Avatar]({member.display_avatar.url})\n"
                    f"┣ 📝 *{bio[:100]}{'...' if len(bio) > 100 else ''}*\n"
                    f"┗ 🎮 {', '.join([a.name for a in member.activities]) if member.activities else 'No activity'}"
                )
                
                embed.add_field(
                    name=f"Member {chunk.index(member) + 1}",
                    value=member_info,
                    inline=False
                )
                
                if chunk.index(member) == 0:
                    embed.set_thumbnail(url=member.display_avatar.url)
            

            payload = {
                "username": "📊 Member Dumper",
                "avatar_url": "https://cdn.discordapp.com/attachments/000/000/000/0000000000000.png",
                "embeds": [embed.to_dict()]
            }
            
            async with self.webhook_session.post(WEBHOOK_URL, json=payload) as resp:
                if resp.status not in (200, 204):
                    print(f"[!] Webhook failed (chunk {chunk_num}): {resp.status}")
                elif VERBOSE:
                    print(f"[✓] Sent chunk {chunk_num}/{total_chunks}")
                    
        except Exception as e:
            print(f"[!] Error sending chunk {chunk_num}: {e}")
    
    async def send_summary(self, total):
        try:
            embed = Embed(
                title="📊 Member Dump Complete",
                description=f"Successfully dumped **{total}** members from the server.",
                color=0x00ffcc,
                timestamp=datetime.now()
            )
            embed.add_field(name="Server ID", value=str(TARGET_SERVER_ID), inline=True)
            embed.add_field(name="Timestamp", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"), inline=True)
            embed.set_footer(text="One-time member extraction • Shadow Spy")
            
            payload = {
                "username": "📊 Member Dumper",
                "avatar_url": "https://cdn.discordapp.com/attachments/000/000/000/0000000000000.png",
                "embeds": [embed.to_dict()]
            }
            
            async with self.webhook_session.post(WEBHOOK_URL, json=payload) as resp:
                if resp.status not in (200, 204):
                    print(f"[!] Summary webhook failed: {resp.status}")
                    
        except Exception as e:
            print(f"[!] Error sending summary: {e}")
    
    async def close(self):
        if self.webhook_session:
            await self.webhook_session.close()
        await super().close()

if __name__ == "__main__":
    from datetime import datetime
    
    print("""
magnify scrape members
    """)
    
    bot = MemberDumper()
    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        asyncio.run(bot.close())
    except Exception as e:
        print(f"[✗] Fatal: {e}")
