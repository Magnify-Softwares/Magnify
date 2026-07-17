import asyncio
import aiohttp
import json
import random
import sys
from datetime import datetime
from discord import Client, Embed
from discord.ext import tasks

TOKEN = "place here"
TARGET_SERVER_ID = 1234
TARGET_CHANNEL_ID = 1234
WEBHOOK_URL = "idk make a webhook9"

MONITORED_USER_IDS = []  # Empty = spy everyone
SCAN_INTERVAL = 3.0


class Magnifybypalantir(Client):
    def __init__(self):
        super().__init__()
        self.seen_messages = set()
        self.session = None
        self.webhook_session = None
        self.running = True
        self.message_cache_limit = 2000

    async def on_ready(self):
        self.session = aiohttp.ClientSession()
        self.webhook_session = aiohttp.ClientSession()
        self.spy_loop.start()

    @tasks.loop(seconds=SCAN_INTERVAL)
    async def spy_loop(self):
        try:
            channel = self.get_channel(TARGET_CHANNEL_ID)
            if not channel:
                return

            async for msg in channel.history(limit=50, oldest_first=False):
                if msg.id in self.seen_messages:
                    continue
                
                if MONITORED_USER_IDS and msg.author.id not in MONITORED_USER_IDS:
                    self.seen_messages.add(msg.id)
                    continue

                self.seen_messages.add(msg.id)
                await self.process_message(msg, channel)
                await asyncio.sleep(random.uniform(0.3, 1.2))

                if len(self.seen_messages) > self.message_cache_limit:
                    self.seen_messages = set(list(self.seen_messages)[-1000:])

        except Exception as e:
            print(f"[!] error: {e}")
            await asyncio.sleep(5)

    async def process_message(self, msg, channel):
        try:
            description = msg.content or "*[No text content]*"
            
            attachment_text = ""
            if msg.attachments:
                attachment_text = "\n\n**📎 Attachments:**\n" + "\n".join(
                    f"[{att.filename}]({att.url})" for att in msg.attachments
                )
                description += attachment_text

            embed = Embed(
                title=f"📩 Message from {msg.author.display_name}",
                description=description,
                color=0x00ffcc,
                timestamp=msg.created_at
            )
            embed.set_author(
                name=f"{msg.author} ({msg.author.id})",
                icon_url=msg.author.display_avatar.url
            )
            embed.add_field(name="Channel", value=f"{channel.name}", inline=True)
            embed.add_field(name="Server", value=channel.guild.name, inline=True)
            embed.add_field(
                name="Link",
                value=f"[Jump]({msg.jump_url})",
                inline=False
            )
            

            for att in msg.attachments:
                if att.content_type and att.content_type.startswith('image/'):
                    embed.set_image(url=att.url)
                    break
            
            embed.set_footer(
                text=f"Message ID: {msg.id} • Captured by Magnify by palantir",
                icon_url="https://cdn.discordapp.com/emojis/883027767823859752.png"
            )

            payload = {
                "username": "🕵️ Magnify by palantir",
                "avatar_url": "https://cdn.discordapp.com/attachments/000/000/000/0000000000000.png",
                "embeds": [embed.to_dict()],
                "content": f"**New message** – {msg.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            }
            
            async with self.webhook_session.post(WEBHOOK_URL, json=payload) as resp:
                if resp.status not in (200, 204):
                    print(f"[!] Webhook failed: {resp.status}")
                    error_text = await resp.text()
                    if error_text:
                        print(f"[!] Error: {error_text[:200]}")

        except Exception as e:
            print(f"[!] Message processing error: {e}")

    async def close(self):
        self.running = False
        self.spy_loop.cancel()
        if self.session:
            await self.session.close()
        if self.webhook_session:
            await self.webhook_session.close()
        await super().close()

if __name__ == "__main__":
    print("""
Magnify chaching all chats 
    """)
    
    bot = Magnifybypalantir()
    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        asyncio.run(bot.close())
    except Exception as e:
        print(f"[✗] Fatal: {e}")
