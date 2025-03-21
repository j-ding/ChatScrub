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

class DiscordBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Message Manager")
        self.root.geometry("900x600")

        # Main Frame (Holds everything)
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas for Scrollable Content
        self.canvas = tk.Canvas(self.main_frame)
        self.v_scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.canvas.xview)
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Packing UI Components
        self.canvas.pack(side="left", fill="both", expand=True)
        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar.pack(side="bottom", fill="x")

        # "Select All" Checkbox
        self.select_all_var = tk.BooleanVar()
        self.select_all_checkbox = ttk.Checkbutton(self.root, text="Select All", variable=self.select_all_var, command=self.toggle_all)
        self.select_all_checkbox.pack(pady=5)

        # Delete Button
        self.delete_button = ttk.Button(self.root, text="Delete Selected", command=self.delete_selected)
        self.delete_button.pack(pady=10)

        # Status Label
        self.status_label = ttk.Label(self.root, text="", foreground="blue")
        self.status_label.pack()

        # Store checkboxes and message data
        self.checkboxes = []
        self.message_vars = []

        # Configure Grid Layout for Expanding Effect
        self.scrollable_frame.columnconfigure(1, weight=1)

    def display_messages(self, messages, keyword):
        """Update Tkinter UI with messages and highlight keywords in red."""
        # Clear old widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.checkboxes.clear()
        self.message_vars.clear()

        for msg_id, (msg_obj, msg_text) in messages.items():
            var = tk.BooleanVar()

            # Row frame that expands
            row_frame = ttk.Frame(self.scrollable_frame)
            row_frame.grid(sticky="ew", padx=10, pady=2)
            row_frame.columnconfigure(1, weight=1)  # Make column 1 expandable

            # Checkbox
            chk = ttk.Checkbutton(row_frame, variable=var)
            chk.grid(row=0, column=0, sticky="w")

            # Determine text widget width based on message length
            text_width = min(max(len(msg_text) // 2, 20), 100)

            # Text widget with expanding behavior
            text_widget = tk.Text(row_frame, wrap="word", height=2, width=text_width)
            text_widget.grid(row=0, column=1, sticky="nsew")  # Expand fully
            text_widget.insert("1.0", msg_text)
            text_widget.config(state="disabled")  # Read-only

            # Apply red color to keyword
            start_idx = "1.0"
            while True:
                start_idx = text_widget.search(keyword, start_idx, stopindex="end", nocase=True)
                if not start_idx:
                    break
                end_idx = f"{start_idx}+{len(keyword)}c"
                text_widget.config(state="normal")
                text_widget.tag_add("highlight", start_idx, end_idx)
                text_widget.config(state="disabled")
                start_idx = end_idx

            text_widget.tag_config("highlight", foreground="red")

            self.checkboxes.append(chk)
            self.message_vars.append((var, msg_obj))

        # Ensure entire scrollable frame expands
        self.scrollable_frame.columnconfigure(0, weight=1)

        # Ensure the canvas updates
        self.root.update_idletasks()


    def toggle_all(self):
        """Check or uncheck all message checkboxes."""
        new_state = self.select_all_var.get()
        for var, _ in self.checkboxes:
            var.set(new_state)

    def delete_selected(self):
        """Delete selected messages with feedback."""
        to_delete = [msg for var, msg in self.message_vars if var.get()]

        if not to_delete:
            self.status_label.config(text="No messages selected.", foreground="red")
            return

        self.status_label.config(text="Deleting messages...", foreground="blue")
        self.root.update_idletasks()

        # Simulating async deletion
        self.root.after(10, lambda: bot.loop.create_task(self.perform_deletion(to_delete)))

    async def perform_deletion(self, to_delete):
        """Perform async message deletion and update status."""
        await delete_messages(to_delete)
        self.status_label.config(text="Deletion complete!", foreground="green")


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
    """Find messages containing a keyword and update UI in batches."""
    global found_messages
    found_messages.clear()
    
    msg_index = 1
    messages_to_display = {}

    print(f"🔍 Searching for '{keyword}' in {len(channels)} channels...")  

    for channel in channels:
        print(f"📡 Searching in #{channel.name}...")  
        try:
            found_any = False  
            batch_count = 0  # Track number of messages processed
            
            async for message in channel.history(limit=1000, oldest_first=True):
                batch_count += 1

                if batch_count % 1000 == 0:
                    print(f"🔄 Processed {batch_count} messages in #{channel.name}...")

                if keyword.lower() in message.content.lower():
                    msg_text = f"[{channel.name}] {message.author}: {message.content} ({message.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
                    found_messages[msg_index] = (message, msg_text)
                    messages_to_display[msg_index] = (message, msg_text)
                    print(f"✅ MATCH: {msg_text}")  
                    found_any = True
                    msg_index += 1
            
            if not found_any:
                print(f"❌ No matches in #{channel.name}")

        except discord.Forbidden:
            print(f"❌ No permission to read messages in #{channel.name}")

    if messages_to_display:
        root.after(0, ui.display_messages, messages_to_display, keyword)

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
