def update_matches(self, new_messages):
        """Update the matches with new batch of messages during incremental search."""
        # Add new messages to all_messages
        if not hasattr(self, 'all_messages'):
            self.all_messages = {}
            
        self.all_messages.update(new_messages)
        
        # If this is the first batch, set keywords and display first page
        if not hasattr(self, 'keywords'):
            self.keywords = []
            
        # Calculate total pages
        self.total_pages = max(1, (len(self.all_messages) + self.items_per_page - 1) // self.items_per_page)
        
        # Update pagination controls
        self.update_pagination_controls()
        
        # Update progress display
        global search_in_progress
        if not search_in_progress:
            search_in_progress = False
            search_end_time = time.time()
            self.update_progress_ui()
import os
import discord
import tkinter as tk
from tkinter import ttk
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import threading
import time

# Load bot token from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Bot setup with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

# Initialize the bot with a command prefix and specified intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Store found messages for UI selection
found_messages = {}

# Progress tracking variables
search_in_progress = False
messages_scanned = 0
matches_found = 0  # New counter for matches
channels_total = 0
current_channel = ""
search_start_time = 0
search_end_time = 0
max_results = 10000  # Maximum number of results to store (to prevent memory issues)

class DiscordBotUI:
    def __init__(self, root):
        """Initialize the Tkinter UI for managing Discord messages."""
        self.root = root
        self.root.title("Discord Message Manager")
        self.root.geometry("900x600")
        
        # Make root window resizable
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Progress Frame
        self.progress_frame = ttk.LabelFrame(self.root, text="Search Progress")
        self.progress_frame.pack(fill="x", padx=10, pady=5)
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        
        # Progress Labels
        self.progress_status = ttk.Label(self.progress_frame, text="Ready")
        self.progress_status.pack(anchor="w", padx=5)
        
        self.progress_details = ttk.Label(self.progress_frame, text="")
        self.progress_details.pack(anchor="w", padx=5)
        
        self.elapsed_time = ttk.Label(self.progress_frame, text="")
        self.elapsed_time.pack(anchor="w", padx=5)

        # Pagination Frame
        self.pagination_frame = ttk.Frame(self.root)
        self.pagination_frame.pack(fill="x", padx=10, pady=5)
        
        self.page_info = ttk.Label(self.pagination_frame, text="No results")
        self.page_info.pack(side="left", padx=5)
        
        self.prev_button = ttk.Button(self.pagination_frame, text="← Prev", command=self.prev_page, state="disabled")
        self.prev_button.pack(side="left", padx=5)
        
        self.next_button = ttk.Button(self.pagination_frame, text="Next →", command=self.next_page, state="disabled")
        self.next_button.pack(side="left", padx=5)
        
        # Select items per page
        ttk.Label(self.pagination_frame, text="Items per page:").pack(side="left", padx=(20, 5))
        self.page_size_var = tk.StringVar(value="25")
        page_size_combo = ttk.Combobox(self.pagination_frame, textvariable=self.page_size_var, 
                                        values=["10", "25", "50", "100"], width=5)
        page_size_combo.pack(side="left")
        page_size_combo.bind("<<ComboboxSelected>>", self.change_page_size)

        # Main Frame (Holds everything else) - Now with weight for resizing
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

        # Canvas for Scrollable Content
        self.canvas = tk.Canvas(self.main_frame)
        self.v_scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.canvas.xview)
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.columnconfigure(0, weight=1)  # Make the scrollable frame expandable

        # Create a window in the canvas for the scrollable frame
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Configure canvas to resize with window
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)

        # Packing UI Components with proper expansion
        self.h_scrollbar.pack(side="bottom", fill="x")
        self.v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # "Select All" Checkbox
        self.select_all_var = tk.BooleanVar()
        self.select_all_checkbox = ttk.Checkbutton(self.root, text="Select All Visible Items", 
                                                  variable=self.select_all_var, command=self.toggle_all)
        self.select_all_checkbox.pack(pady=5)

        # Delete Button
        self.delete_button = ttk.Button(self.root, text="Delete Selected", command=self.delete_selected)
        self.delete_button.pack(pady=10)

        # Status Label
        self.status_label = ttk.Label(self.root, text="", foreground="blue")
        self.status_label.pack(pady=5)

        # Store checkboxes and message data
        self.checkboxes = []
        self.message_vars = []

        # Pagination variables
        self.current_page = 1
        self.items_per_page = 25
        self.all_messages = {}
        self.total_pages = 1
        
        # Start progress updater
        self.update_progress_display()
        
    def on_canvas_configure(self, event):
        """Handle canvas resize event to update the scrollable area width."""
        # Update the width of the scrollable frame window to fill the canvas
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def display_messages(self, messages, keywords):
        """Store all messages and display the first page."""
        if not hasattr(self, 'all_messages') or self.all_messages is None:
            self.all_messages = {}
            
        # Update with new messages
        self.all_messages.update(messages)
        self.keywords = keywords
        
        # Calculate total pages
        self.total_pages = max(1, (len(self.all_messages) + self.items_per_page - 1) // self.items_per_page)
        self.current_page = 1
        
        # Display the first page
        self.display_current_page()
        
        # Update progress display after search completes
        global search_in_progress, search_end_time
        search_in_progress = False
        search_end_time = time.time()
        self.update_progress_ui()

    def display_current_page(self):
        """Display current page of messages."""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.checkboxes.clear()
        self.message_vars.clear()
        
        # Calculate start and end indices for the current page
        start_idx = (self.current_page - 1) * self.items_per_page + 1
        end_idx = min(start_idx + self.items_per_page - 1, len(self.all_messages))
        
        # Configure columns in scrollable frame for proper expansion
        self.scrollable_frame.columnconfigure(0, weight=0)  # Checkbox column (fixed width)
        self.scrollable_frame.columnconfigure(1, weight=0)  # Number column (fixed width)
        self.scrollable_frame.columnconfigure(2, weight=1)  # Message content column (expandable)
        
        # Set the width of the scrollable frame to match the canvas
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 1:  # Ensure canvas has been rendered
            self.scrollable_frame.config(width=canvas_width)
        
        # Display only messages for current page
        row = 0
        for msg_id in range(start_idx, end_idx + 1):
            if msg_id in self.all_messages:
                msg_obj, msg_text = self.all_messages[msg_id]
                
                var = tk.BooleanVar()
                
                # Create a frame for this row that spans the full width
                row_frame = ttk.Frame(self.scrollable_frame)
                row_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=2, columnspan=3)
                row_frame.columnconfigure(2, weight=1)  # Make the text widget column expandable
                
                # Checkbox
                chk = ttk.Checkbutton(row_frame, variable=var)
                chk.grid(row=0, column=0, sticky="w", padx=(0,5))
                
                # Message number label
                num_label = ttk.Label(row_frame, text=f"{msg_id}.")
                num_label.grid(row=0, column=1, sticky="w", padx=(0,10))
                
                # Text widget for message content with better sizing
                text_widget = tk.Text(row_frame, wrap="word", height=4, borderwidth=1, relief="solid")
                text_widget.grid(row=0, column=2, sticky="nsew", padx=(0,5))
                
                # Insert message content
                text_widget.insert("1.0", msg_text)
                
                # Apply highlighting to all keywords
                for keyword in self.keywords:
                    self.highlight_keyword(text_widget, keyword)
                
                # Make text widget read-only
                text_widget.config(state="disabled")
                
                self.checkboxes.append(chk)
                self.message_vars.append((var, msg_obj))
                row += 1
        
        # Update page information and button states
        self.update_pagination_controls()
        
        # Force layout update to properly display the scrollable content
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)  # Scroll to top when page changes

    def highlight_keyword(self, text_widget, keyword):
        """Highlight all occurrences of a keyword in a text widget."""
        # Make sure text widget is editable for highlighting
        text_widget.config(state="normal")
        
        # Configure the highlight tag
        text_widget.tag_configure("highlight", foreground="red", underline=True)
        
        # Use a simple and reliable approach
        start_pos = "1.0"
        while True:
            # Find next match position (case-insensitive)
            pos = text_widget.search(keyword, start_pos, stopindex="end", nocase=1)
            if not pos:
                break
                
            # Calculate end position
            end_pos = f"{pos}+{len(keyword)}c"
            
            # Add tag to this match
            text_widget.tag_add("highlight", pos, end_pos)
            
            # Move to position after this match
            start_pos = end_pos
            
        # Make text widget read-only again
        text_widget.config(state="disabled")

    def update_pagination_controls(self):
        """Update pagination controls based on current state."""
        # Update page info text
        total_items = len(self.all_messages)
        start_idx = (self.current_page - 1) * self.items_per_page + 1
        end_idx = min(start_idx + self.items_per_page - 1, total_items)
        
        self.page_info.config(text=f"Showing {start_idx}-{end_idx} of {total_items} results " +
                             f"(Page {self.current_page} of {self.total_pages})")
        
        # Enable/disable pagination buttons
        self.prev_button.config(state="normal" if self.current_page > 1 else "disabled")
        self.next_button.config(state="normal" if self.current_page < self.total_pages else "disabled")

    def prev_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.display_current_page()

    def next_page(self):
        """Go to next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.display_current_page()

    def change_page_size(self, event=None):
        """Change number of items displayed per page."""
        try:
            self.items_per_page = int(self.page_size_var.get())
            self.total_pages = max(1, (len(self.all_messages) + self.items_per_page - 1) // self.items_per_page)
            self.current_page = 1  # Reset to first page
            self.display_current_page()
        except ValueError:
            pass  # Ignore invalid input

    def update_progress_ui(self):
        """Update the progress UI based on current search status"""
        global search_in_progress, messages_scanned, current_channel, search_start_time, search_end_time
        
        if search_in_progress:
            if self.progress_bar['mode'] == 'determinate':
                self.progress_bar['mode'] = 'indeterminate'
            
            self.progress_bar.start(10)
            self.progress_status.config(text="Searching...")
            
            # Calculate elapsed time during active search
            elapsed = time.time() - search_start_time
            elapsed_str = f"Time elapsed: {int(elapsed // 60)}m {int(elapsed % 60)}s"
            self.elapsed_time.config(text=elapsed_str)
            
            self.progress_details.config(
                text=f"Scanning channel: {current_channel}\nMessages scanned: {messages_scanned}\nMatches found: {matches_found}"
            )
        else:
            self.progress_bar.stop()
            self.progress_bar['mode'] = 'determinate'
            self.progress_var.set(100) if messages_scanned > 0 else self.progress_var.set(0)
            
            if messages_scanned > 0:
                # Use the final elapsed time when search is complete
                if search_end_time > 0:
                    elapsed = search_end_time - search_start_time
                    elapsed_str = f"Total time: {int(elapsed // 60)}m {int(elapsed % 60)}s"
                    self.elapsed_time.config(text=elapsed_str)
                
                self.progress_status.config(text="Search complete!")
                self.progress_details.config(text=f"Scanned {messages_scanned} messages across {channels_total} channels\nFound {matches_found} matches")
            else:
                self.progress_status.config(text="Ready")
                self.progress_details.config(text="")
                self.elapsed_time.config(text="")

    def update_progress_display(self):
        """Update progress display periodically"""
        self.update_progress_ui()
        self.root.after(500, self.update_progress_display)  # Update every 500ms

    def toggle_all(self):
        """Check or uncheck all visible message checkboxes."""
        new_state = self.select_all_var.get()
        for var, _ in self.message_vars:
            var.set(new_state)

    def delete_selected(self):
        """Delete selected messages with feedback."""
        to_delete = [msg for var, msg in self.message_vars if var.get()]

        if not to_delete:
            self.status_label.config(text="No messages selected.", foreground="red")
            return

        self.status_label.config(text="Deleting messages...", foreground="blue")
        self.root.update_idletasks()

        # Create a new asyncio task for deletion
        self.root.after(10, lambda: bot.loop.create_task(self.perform_deletion(to_delete)))

    async def perform_deletion(self, to_delete):
        """Perform async message deletion and update status."""
        deleted_msg_ids = []
        failed_deletions = 0
        success_deletions = 0
        
        # Delete messages one by one for better reliability
        for msg in to_delete:
            try:
                await msg.delete()
                deleted_msg_ids.append(msg.id)
                success_deletions += 1
                # Update status after each successful deletion
                self.status_label.config(text=f"Deleting messages... ({success_deletions}/{len(to_delete)})", foreground="blue")
                self.root.update_idletasks()
            except discord.Forbidden:
                print(f"❌ No permission to delete message in #{msg.channel.name}")
                failed_deletions += 1
            except discord.HTTPException as e:
                print(f"⚠️ Error deleting message: {e}")
                failed_deletions += 1
            except Exception as e:
                print(f"⚠️ Unexpected error: {e}")
                failed_deletions += 1
        
        # If we successfully deleted any messages, update the UI
        if deleted_msg_ids:
            # Remove deleted messages from all_messages
            new_all_messages = {}
            new_idx = 1
            
            for idx, (msg, text) in self.all_messages.items():
                if msg.id not in deleted_msg_ids:
                    new_all_messages[new_idx] = (msg, text)
                    new_idx += 1
            
            # Update all_messages and redisplay
            self.all_messages = new_all_messages
            self.total_pages = max(1, (len(self.all_messages) + self.items_per_page - 1) // self.items_per_page)
            
            # Adjust current page if needed
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages
                
            # Refresh display
            self.display_current_page()
        
        # Final status update
        if failed_deletions > 0:
            self.status_label.config(
                text=f"Deleted {success_deletions} messages. Failed to delete {failed_deletions} messages.", 
                foreground="orange"
            )
        else:
            self.status_label.config(
                text=f"Successfully deleted {success_deletions} messages!", 
                foreground="green"
            )

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
    """Event handler for when the bot is ready."""
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def find(ctx, *args):
    """Find messages containing any of the given keywords in the specified channels."""
    global found_messages, search_in_progress, messages_scanned, matches_found, channels_total, current_channel, search_start_time, search_end_time
    
    # Reset search state
    found_messages.clear()
    search_in_progress = True
    messages_scanned = 0
    matches_found = 0  # Reset matches counter
    current_channel = ""
    search_start_time = time.time()
    search_end_time = 0  # Reset end time at start of search

    if len(args) < 2:
        await ctx.send("Usage: `!find keyword1 keyword2 ... #channel1 #channel2`")
        search_in_progress = False
        return

    # Extract keywords (ignore anything that starts with '#' or '<#')
    keywords = [word.lower().strip() for word in args if not word.startswith("#") and not word.startswith("<#")]
    
    # Inform about the keywords we're searching for
    print(f"Searching for keywords: {keywords}")

    # Extract channels correctly
    channels = []
    for word in args:
        if word.startswith("#"):
            channel = discord.utils.get(ctx.guild.channels, name=word[1:])
        elif word.startswith("<#") and word.endswith(">"):
            try:
                channel_id = int(word.strip("<#>"))
                channel = ctx.guild.get_channel(channel_id)
            except ValueError:
                continue
        else:
            continue
        
        if channel:
            channels.append(channel)

    if not channels:
        await ctx.send("No valid channels specified. Please mention channels using `#channel-name` or `<#channel_id>`.")
        search_in_progress = False
        search_end_time = time.time()  # Set end time on error
        return

    channels_total = len(channels)
    msg_index = 1
    messages_to_display = {}
    
    # If we already have some messages from a previous search, clear them
    if hasattr(ui, 'all_messages'):
        ui.all_messages = {}

    print(f"🔍 Searching for {keywords} in {len(channels)} channels...")
    await ctx.send(f"Searching for messages with keywords: `{', '.join(keywords)}` in {len(channels)} channels. Please wait...")

    # Flag to track if we hit the result limit
    results_limited = False

    for channel in channels:
        current_channel = channel.name
        print(f"📡 Searching in #{channel.name}...")
        
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                messages_scanned += 1
                
                # Update progress every 100 messages
                if messages_scanned % 100 == 0:
                    print(f"Scanned {messages_scanned} messages...")
                
                # Check if we've hit the maximum results limit
                if matches_found >= max_results:
                    results_limited = True
                    print(f"⚠️ Reached maximum result limit of {max_results}. Stopping search.")
                    break
                
                # Normalize message content for better matching
                message_content = message.content.lower()
                
                # Check each keyword
                found_match = False
                for keyword in keywords:
                    if keyword in message_content:
                        found_match = True
                        # Print debug info for matches
                        print(f"Matched keyword '{keyword}' in: {message.content}")
                        break
                
                if found_match:
                    matches_found += 1  # Increment match counter
                    msg_text = f"[{channel.name}] {message.author}: {message.content} ({message.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
                    found_messages[msg_index] = (message, msg_text)
                    messages_to_display[msg_index] = (message, msg_text)
                    print(f"✅ MATCH #{matches_found}: {msg_text}")
                    msg_index += 1
                    
                    # If we have a lot of matches, update UI in chunks to avoid memory issues
                    if matches_found % 1000 == 0:
                        # Create a copy of the current batch to display
                        current_batch = messages_to_display.copy()
                        # Update display asynchronously
                        root.after(0, lambda batch=current_batch: ui.update_matches(batch))
                        # Clear the batch to save memory
                        messages_to_display = {}

            # If we reached the limit, break out of channel loop too
            if results_limited:
                break

        except discord.Forbidden:
            print(f"❌ No permission to read messages in #{channel.name}")
            await ctx.send(f"⚠️ No permission to read messages in #{channel.name}")

    # Set end time when all channels have been searched
    search_end_time = time.time()
    
    # Send appropriate messages based on results
    if results_limited:
        await ctx.send(f"⚠️ Search stopped after finding {matches_found} messages (maximum limit). Try a more specific search.")
    else:
        await ctx.send(f"✅ Search complete! Found {matches_found} messages matching your keywords. Check the UI to manage results.")
    
    # Display final batch of messages
    if messages_to_display:
        root.after(0, lambda: ui.display_messages(messages_to_display, keywords))
    else:
        search_in_progress = False  # Ensure search is marked as complete even if no messages are found

# Add debug command to test keyword matching
@bot.command()
async def testkeyword(ctx, keyword, *, sample_text):
    """Test if a keyword would match a given sample text."""
    keyword = keyword.lower().strip()
    sample_text = sample_text.lower()
    
    if keyword in sample_text:
        await ctx.send(f"✅ Keyword `{keyword}` MATCHES in the sample text.")
    else:
        await ctx.send(f"❌ Keyword `{keyword}` does NOT match in the sample text.")
    
    # Show character codes for both strings to help debug invisible characters
    keyword_codes = " ".join(f"{ord(c):02x}" for c in keyword)
    await ctx.send(f"Keyword character codes: `{keyword_codes}`")
    
    # Show a small portion of the text around where we expect the keyword
    if len(sample_text) > 100:
        # Try to find the closest position to the keyword
        pos = sample_text.find(keyword[:5]) if len(keyword) >= 5 else 0
        if pos == -1:
            pos = 0
        start = max(0, pos - 20)
        end = min(len(sample_text), pos + len(keyword) + 20)
        sample_snippet = sample_text[start:end]
        snippet_codes = " ".join(f"{ord(c):02x}" for c in sample_snippet)
        await ctx.send(f"Sample text snippet character codes: `{snippet_codes}`")

# Delete this function as we're not using it anymore

# Run Discord bot in a separate thread
threading.Thread(target=run_discord_bot, daemon=True).start()

# Start Tkinter main loop
root.mainloop()
