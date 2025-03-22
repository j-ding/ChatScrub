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
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Retrieve the Discord bot token from environment variables

# Bot setup with necessary intents
intents = discord.Intents.default()  # Create default intents
intents.message_content = True  # Enable message content intent
intents.guilds = True  # Enable guilds intent
intents.messages = True  # Required for retrieving & deleting messages

# Initialize the bot with a command prefix and specified intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Store found messages for UI selection
found_messages = {}  # Dictionary to hold found messages with their IDs and content

class DiscordBotUI:
    def __init__(self, root):
        """Initialize the Tkinter UI for managing Discord messages."""
        self.root = root
        self.root.title("Discord Message Manager")  # Set the window title
        self.root.geometry("900x600")  # Set the window size

        # Main Frame (Holds everything)
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)  # Expand the main frame

        # Canvas for Scrollable Content
        self.canvas = tk.Canvas(self.main_frame)  # Create a canvas for scrollable content
        self.v_scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)  # Vertical scrollbar
        self.h_scrollbar = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.canvas.xview)  # Horizontal scrollbar
        
        self.scrollable_frame = ttk.Frame(self.canvas)  # Frame that will hold the scrollable content
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))  # Configure scroll region

        # Create a window in the canvas for the scrollable frame
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)  # Link scrollbars to canvas

        # Packing UI Components
        self.canvas.pack(side="left", fill="both", expand=True)  # Pack the canvas
        self.v_scrollbar.pack(side="right", fill="y")  # Pack the vertical scrollbar
        self.h_scrollbar.pack(side="bottom", fill="x")  # Pack the horizontal scrollbar

        # "Select All" Checkbox
        self.select_all_var = tk.BooleanVar()  # Variable to track the state of the "Select All" checkbox
        self.select_all_checkbox = ttk.Checkbutton(self.root, text="Select All", variable=self.select_all_var, command=self.toggle_all)  # Checkbox to select/deselect all messages
        self.select_all_checkbox.pack(pady=5)  # Pack the checkbox

        # Delete Button
        self.delete_button = ttk.Button(self.root, text="Delete Selected", command=self.delete_selected)  # Button to delete selected messages
        self.delete_button.pack(pady=10)  # Pack the button

        # Status Label
        self.status_label = ttk.Label(self.root, text="", foreground="blue")  # Label to display status messages
        self.status_label.pack()  # Pack the status label

        # Store checkboxes and message data
        self.checkboxes = []  # List to hold checkbox widgets
        self.message_vars = []  # List to hold message data and associated BooleanVars

        # Configure Grid Layout for Expanding Effect
        self.scrollable_frame.columnconfigure(1, weight=1)  # Allow the second column to expand

    def display_messages(self, messages, keywords):
        """Update Tkinter UI with messages and highlight multiple keywords in red."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()  # Clear previous message widgets

        self.checkboxes.clear()  # Clear the checkbox list
        self.message_vars.clear()  # Clear the message variable list

        for msg_id, (msg_obj, msg_text) in messages.items():
            var = tk.BooleanVar()  # Create a BooleanVar for each message checkbox

            # Ensure row_frame is always initialized
            row_frame = ttk.Frame(self.scrollable_frame)  # Create a frame for each message
            row_frame.grid(sticky="ew", padx=10, pady=2)  # Place the frame in the grid
            row_frame.columnconfigure(1, weight=1)  # Allow the text widget to expand

            chk = ttk.Checkbutton(row_frame, variable=var)  # Create a checkbox for the message
            chk.grid(row=0, column=0, sticky="w")  # Place the checkbox in the grid

            # Determine the width of the text widget based on message length
            text_width = min(max(len(msg_text) // 2, 20), 100)  # Set a reasonable width for the text widget
            text_widget = tk.Text(row_frame, wrap="word", height=2, width=text_width)  # Create a text widget for the message
            text_widget.grid(row=0, column=1, sticky="nsew")  # Place the text widget in the grid
            text_widget.insert("1.0", msg_text)  # Insert the message text
            text_widget.config(state="disabled")  # Make the text widget read-only

            # Apply red color to all keywords
            for keyword in keywords:
                start_idx = "1.0"  # Start searching from the beginning of the text
                while True:
                    start_idx = text_widget.search(keyword, start_idx, stopindex="end", nocase=True)  # Search for the keyword
                    if not start_idx:
                        break  # Exit if no more keywords are found
                    end_idx = f"{start_idx}+{len(keyword)}c"  # Calculate the end index of the keyword
                    text_widget.config(state="normal")  # Enable editing to apply tags
                    text_widget.tag_add("highlight", start_idx, end_idx)  # Highlight the keyword
                    text_widget.config(state="disabled")  # Disable editing again
                    start_idx = end_idx  # Move the start index to the end of the highlighted keyword

            text_widget.tag_config("highlight", foreground="red")  # Configure the highlight tag to use red color

            self.checkboxes.append(chk)  # Store the checkbox
            self.message_vars.append((var, msg_obj))  # Store the message variable and object

    def toggle_all(self):
        """Check or uncheck all message checkboxes."""
        new_state = self.select_all_var.get()  # Get the current state of the "Select All" checkbox
        for var, _ in self.message_vars:  # Iterate over stored BooleanVar objects
            var.set(new_state)  # Set each checkbox to the new state

    def delete_selected(self):
        """Delete selected messages with feedback."""
        to_delete = [msg for var, msg in self.message_vars if var.get()]  # Collect messages that are selected

        if not to_delete:
            self.status_label.config(text="No messages selected.", foreground="red")  # Update status if no messages are selected
            return

        self.status_label.config(text="Deleting messages...", foreground="blue")  # Update status to indicate deletion
        self.root.update_idletasks()  # Update the UI

        # Simulating async deletion
        self.root.after(10, lambda: bot.loop.create_task(self.perform_deletion(to_delete)))  # Schedule the deletion task

    async def perform_deletion(self, to_delete):
        """Perform async message deletion and update status."""
        await delete_messages(to_delete)  # Call the function to delete messages
        self.status_label.config(text="Deletion complete!", foreground="green")  # Update status after deletion


# Instantiate UI
root = tk.Tk()  # Create the main Tkinter window
ui = DiscordBotUI(root)  # Create an instance of the DiscordBotUI class

def run_discord_bot():
    """Runs the Discord bot safely in a separate thread."""
    asyncio.set_event_loop(asyncio.new_event_loop())  # Set a new event loop for the bot
    loop = asyncio.get_event_loop()  # Get the current event loop
    loop.run_until_complete(bot.start(TOKEN))  # Start the bot

@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    print(f"✅ Logged in as {bot.user}")  # Print a message indicating the bot is logged in

@bot.command()
async def find(ctx, *args):
    """Find messages containing any of the given keywords in the specified channels."""
    global found_messages  # Use the global found_messages dictionary
    found_messages.clear()  # Clear previous search results

    if len(args) < 2:
        await ctx.send("Usage: `!find keyword1 keyword2 ... #channel1 #channel2`")  # Provide usage instructions
        return

    # Extract keywords (ignore anything that starts with '#' or '<#')
    keywords = [word.lower() for word in args if not word.startswith("#") and not word.startswith("<#")]  # Collect keywords

    # Extract channels correctly
    channels = []  # List to hold valid channels
    for word in args:
        if word.startswith("#"):  # User manually types "#channel-name"
            channel = discord.utils.get(ctx.guild.channels, name=word[1:])  # Remove '#' and get channel by name
        elif word.startswith("<#") and word.endswith(">"):  # Proper channel mention "<#123456789>"
            try:
                channel_id = int(word.strip("<#>"))  # Extract channel ID
                channel = ctx.guild.get_channel(channel_id)  # Get channel by ID
            except ValueError:
                continue  # Skip invalid channel IDs
        else:
            continue  # Skip non-channel words
        
        if channel:
            channels.append(channel)  # Add valid channels to the list

    if not channels:
        await ctx.send("No valid channels specified. Please mention channels using `#channel-name` or `<#channel_id>`.")  # Notify if no valid channels were found
        return

    msg_index = 1  # Initialize message index for display
    messages_to_display = {}  # Dictionary to hold messages to display

    print(f"🔍 Searching for {keywords} in {len(channels)} channels...")  # Log the search operation

    for channel in channels:
        print(f"📡 Searching in #{channel.name}...")  # Log the channel being searched
        try:
            async for message in channel.history(limit=None, oldest_first=True):  # limit = none searches all messages in the channel
                if any(keyword in message.content.lower() for keyword in keywords):  # Check if any keyword is in the message
                    msg_text = f"[{channel.name}] {message.author}: {message.content} ({message.created_at.strftime('%Y-%m-%d %H:%M:%S')})"  # Format message text
                    found_messages[msg_index] = (message, msg_text)  # Store found message
                    messages_to_display[msg_index] = (message, msg_text)  # Store message for display
                    print(f"✅ MATCH: {msg_text}")  # Log the matched message
                    msg_index += 1  # Increment message index

        except discord.Forbidden:
            print(f"❌ No permission to read messages in #{channel.name}")  # Log permission error

    if messages_to_display:
        root.after(0, ui.display_messages, messages_to_display, keywords)  # Update UI with found messages

async def delete_messages(messages):
    """Delete selected messages in bulk for faster performance."""
    channel_messages = {}  # Dictionary to group messages by channel

    # Group messages by channel
    for message in messages:
        if message.channel not in channel_messages:
            channel_messages[message.channel] = []  # Initialize list for new channel
        channel_messages[message.channel].append(message)  # Add message to the channel's list

    # Bulk delete messages per channel
    for channel, msgs in channel_messages.items():
        try:
            if len(msgs) == 1:
                await msgs[0].delete()  # Delete single message
            else:
                await channel.purge(check=lambda m: m.id in [msg.id for msg in msgs])  # Bulk delete messages
            print(f"🗑 Deleted {len(msgs)} messages in #{channel.name}")  # Log deletion
        except discord.Forbidden:
            print(f"❌ No permission to delete messages in #{channel.name}")  # Log permission error
        except discord.HTTPException as e:
            print(f"⚠️ Error deleting messages: {e}")  # Log any HTTP errors

# Run Discord bot in a separate thread
threading.Thread(target=run_discord_bot, daemon=True).start()  # Start the bot in a separate thread

# Start Tkinter main loop
root.mainloop()  # Run the Tkinter event loop
