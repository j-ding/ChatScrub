import os  # For environment variable access
import discord  # Discord API
import tkinter as tk  # GUI framework
from tkinter import ttk  # Themed widgets for Tkinter
from discord.ext import commands  # Discord bot commands extension
from dotenv import load_dotenv  # Load environment variables
import asyncio  # Async operations
import threading  # Multi-threading for running Discord bot and UI simultaneously

# Load bot token from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Configure bot with required intents
intents = discord.Intents.default()
intents.message_content = True  # Allows bot to read message content
intents.guilds = True  # Allows bot to interact with servers (guilds)
intents.messages = True  # Enables message retrieval & deletion

# Initialize bot with command prefix
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store found messages for UI selection
found_messages = {}  # {msg_id: (discord.Message, formatted_string)}

class DiscordBotUI:
    """GUI for managing Discord messages using Tkinter."""
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Message Manager")  # Set window title
        self.root.geometry("900x600")  # Set window size

        # Main container frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create scrollable canvas
        self.canvas = tk.Canvas(self.main_frame)
        self.v_scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.canvas.xview)
        
        # Create frame inside canvas to hold scrollable content
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Embed scrollable frame inside canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Pack UI components
        self.canvas.pack(side="left", fill="both", expand=True)
        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar.pack(side="bottom", fill="x")

        # "Select All" checkbox
        self.select_all_var = tk.BooleanVar()
        self.select_all_checkbox = ttk.Checkbutton(self.root, text="Select All", variable=self.select_all_var, command=self.toggle_all)
        self.select_all_checkbox.pack(pady=5)

        # Delete button
        self.delete_button = ttk.Button(self.root, text="Delete Selected", command=self.delete_selected)
        self.delete_button.pack(pady=10)

        # Status label
        self.status_label = ttk.Label(self.root, text="", foreground="blue")
        self.status_label.pack()

        # Store checkboxes and message data
        self.checkboxes = []
        self.message_vars = []

        # Configure grid layout
        self.scrollable_frame.columnconfigure(1, weight=1)

    def display_messages(self, messages, keywords):
        """Display retrieved messages in Tkinter UI with keyword highlighting."""
        # Clear previous entries
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.checkboxes.clear()
        self.message_vars.clear()

        for msg_id, (msg_obj, msg_text) in messages.items():
            var = tk.BooleanVar()

            # Create a frame for each message
            row_frame = ttk.Frame(self.scrollable_frame)
            row_frame.grid(sticky="ew", padx=10, pady=2)
            row_frame.columnconfigure(1, weight=1)

            # Checkbox for selecting messages
            chk = ttk.Checkbutton(row_frame, variable=var)
            chk.grid(row=0, column=0, sticky="w")

            # Text widget to display message content
            text_width = min(max(len(msg_text) // 2, 20), 100)
            text_widget = tk.Text(row_frame, wrap="word", height=2, width=text_width)
            text_widget.grid(row=0, column=1, sticky="nsew")
            text_widget.insert("1.0", msg_text)
            text_widget.config(state="disabled")

            # Highlight keywords in red
            for keyword in keywords:
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

            # Store checkboxes and associated messages
            self.checkboxes.append(chk)
            self.message_vars.append((var, msg_obj))

    def toggle_all(self):
        """Select or deselect all checkboxes."""
        new_state = self.select_all_var.get()
        for var, _ in self.message_vars:
            var.set(new_state)

    def delete_selected(self):
        """Delete selected messages."""
        to_delete = [msg for var, msg in self.message_vars if var.get()]

        if not to_delete:
            self.status_label.config(text="No messages selected.", foreground="red")
            return

        self.status_label.config(text="Deleting messages...", foreground="blue")
        self.root.update_idletasks()

        # Perform deletion asynchronously
        self.root.after(10, lambda: bot.loop.create_task(self.perform_deletion(to_delete)))

    async def perform_deletion(self, to_delete):
        """Perform async message deletion and update status."""
        await delete_messages(to_delete)
        self.status_label.config(text="Deletion complete!", foreground="green")

# Create UI instance
root = tk.Tk()
ui = DiscordBotUI(root)

def run_discord_bot():
    """Runs the Discord bot in a separate thread."""
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start(TOKEN))

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

async def delete_messages(messages):
    """Delete messages efficiently."""
    for message in messages:
        try:
            await message.delete()
            print(f"🗑 Deleted message in {message.channel}")
        except discord.Forbidden:
            print(f"❌ No permission to delete messages in {message.channel}")

# Run Discord bot in a separate thread
threading.Thread(target=run_discord_bot, daemon=True).start()

# Start Tkinter main loop
root.mainloop()
