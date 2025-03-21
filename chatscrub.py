import os
import discord
import tkinter as tk
from tkinter import ttk
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import threading

# Load bot token from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Bot setup with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True  # Required for retrieving & deleting messages

bot = commands.Bot(command_prefix="!", intents=intents)

# Store found messages for UI selection
found_messages = {}  # {msg_id: (discord.Message, formatted_string)}

# Tkinter UI
class DiscordBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Message Manager")
        self.root.geometry("700x500")
        
        # Message List Frame
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable List
        self.canvas = tk.Canvas(self.frame)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Delete Button
        self.delete_button = ttk.Button(self.root, text="Delete Selected", command=self.delete_selected)
        self.delete_button.pack(pady=10)
        
        self.checkboxes = []  # Store checkboxes
        self.message_vars = []  # Store checkbox states
    

    def display_messages(self, messages):
        """Update Tkinter UI with messages."""
        # Clear old widgets before displaying new ones
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
    
        self.checkboxes.clear()
        self.message_vars.clear()
        
        for msg_id, (msg_obj, msg_text) in messages.items():  
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.scrollable_frame, text=msg_text, variable=var)  # ✅ FIXED
            chk.pack(anchor="w", padx=10, pady=2)
            self.checkboxes.append(chk)
            self.message_vars.append((var, msg_obj))  
        
        self.root.update_idletasks()  # ✅ Ensures UI refreshes

    def delete_selected(self):
        """Delete selected messages."""
        to_delete = [msg for var, msg in self.message_vars if var.get()]
        self.root.after(10, lambda: bot.loop.create_task(delete_messages(to_delete)))


# Instantiate UI
root = tk.Tk()
ui = DiscordBotUI(root)

def run_discord_bot():
    """Runs the Discord bot safely in a separate thread."""
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start(TOKEN))

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def find(ctx, keyword: str, *channels: discord.TextChannel):
    """Find messages containing a keyword and update UI."""
    global found_messages
    found_messages.clear()
    
    msg_index = 1
    messages_to_display = {}

    print(f"🔍 Searching for '{keyword}' in {len(channels)} channels...")  

    for channel in channels:
        print(f"📡 Searching in #{channel.name}...")  
        try:
            found_any = False  # Track if we find anything
            count = 0  # Track messages processed

            async for message in channel.history(limit=None):
                count += 1
                if count % 50 == 0:  # Show progress every 50 messages
                    print(f"🔄 Processed {count} messages in #{channel.name}...")

                if keyword.lower() in message.content.lower():
                    msg_text = f"[{channel.name}] {message.author}: {message.content} ({message.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
                    found_messages[msg_index] = (message, msg_text)
                    messages_to_display[msg_index] = (message, msg_text)
                    print(f"✅ MATCH: {msg_text}")  
                    found_any = True
                    msg_index += 1

            print(f"✅ Finished searching #{channel.name}. Processed {count} messages.")

            if not found_any:
                print(f"❌ No matches in #{channel.name}")

        except discord.Forbidden:
            print(f"❌ No permission to read messages in #{channel.name}")

    if messages_to_display:
        root.after(0, ui.display_messages, messages_to_display)
        print("✅ Messages loaded into UI.")
    else:
        print("⚠️ No messages matched the keyword.")

async def delete_messages(messages):
    """Delete selected messages from Discord."""
    for message in messages:
        try:
            await message.delete()
            print(f"🗑 Deleted: {message.content}")
        except discord.Forbidden:
            print(f"❌ No permission to delete: {message.content}")

# Run Discord bot in a separate thread
threading.Thread(target=run_discord_bot, daemon=True).start()

# Start Tkinter main loop
root.mainloop()
