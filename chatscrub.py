import os
import discord
import tkinter as tk
from tkinter import ttk
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import threading
import time
import json
import os.path

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
max_results = 100000  # Maximum number of results to store (to prevent memory issues)

# Exclusion system variables
exclusion_lists = {}  # Dictionary to store exclusion lists by guild ID
EXCLUSION_FILE = "exclusion_lists.json"  # File to store exclusion lists

def load_exclusion_lists():
    """Load exclusion lists from file."""
    global exclusion_lists
    try:
        if os.path.exists(EXCLUSION_FILE):
            with open(EXCLUSION_FILE, 'r') as f:
                exclusion_lists = json.load(f)
                print(f"Loaded exclusion lists for {len(exclusion_lists)} guilds")
    except Exception as e:
        print(f"Error loading exclusion lists: {e}")
        exclusion_lists = {}

def save_exclusion_lists():
    """Save exclusion lists to file."""
    try:
        with open(EXCLUSION_FILE, 'w') as f:
            json.dump(exclusion_lists, f, indent=2)
        print("Exclusion lists saved to file")
    except Exception as e:
        print(f"Error saving exclusion lists: {e}")

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
        self.page_size_var = tk.StringVar(value="100")
        page_size_combo = ttk.Combobox(self.pagination_frame, textvariable=self.page_size_var, 
                                        values=["50", "100", "500","1000"], width=5)
        page_size_combo.pack(side="left")
        page_size_combo.bind("<<ComboboxSelected>>", self.change_page_size)

        # Selected count label (NEW)
        self.selected_count_var = tk.StringVar(value="0 items selected")
        self.selected_count = ttk.Label(self.pagination_frame, textvariable=self.selected_count_var)
        self.selected_count.pack(side="right", padx=10)

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
        self.delete_button.pack(pady=5)
        
        # Add a button to show exclusions
        self.exclusions_button = ttk.Button(self.root, text="Show Exclusion Lists", command=self.show_exclusions)
        self.exclusions_button.pack(pady=5)

        # Status Label
        self.status_label = ttk.Label(self.root, text="", foreground="blue")
        self.status_label.pack(pady=5)

        # Store checkboxes and message data
        self.checkboxes = []
        self.message_vars = []
        
        # Track selected messages across all pages (NEW)
        self.selected_messages = {}

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
        
        # Reset selections when starting a new search
        self.selected_messages = {}
        
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
        
    def update_matches(self, new_messages):
        """Update the matches with new batch of messages during incremental search."""
        try:
            # Add new messages to all_messages
            if not hasattr(self, 'all_messages'):
                self.all_messages = {}
                
            self.all_messages.update(new_messages)
            
            # If this is the first batch, set keywords if not already set
            if not hasattr(self, 'keywords'):
                self.keywords = []
            
            # Calculate total pages
            self.total_pages = max(1, (len(self.all_messages) + self.items_per_page - 1) // self.items_per_page)
            
            # Update pagination controls
            self.update_pagination_controls()
            
            # Show loading message in UI
            self.status_label.config(text=f"Processing {len(self.all_messages)} matches...", foreground="blue")
            
            # Force UI update
            self.root.update_idletasks()
            
            print(f"Added batch of {len(new_messages)} messages, total now: {len(self.all_messages)}")
        except Exception as e:
            print(f"Error updating matches: {e}")

    def display_current_page(self):
        """Display current page of messages."""
        # Save current selections before clearing the page
        self.save_current_selections()
        
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
                
                # Create checkbox variable with trace to track changes
                var = tk.BooleanVar()
                
                # Set the checkbox state based on stored selections
                if msg_obj.id in self.selected_messages:
                    var.set(True)
                    
                # Add trace to update selection dictionary when checkbox changes
                var.trace_add("write", lambda *args, m_id=msg_obj.id, v=var: self.on_checkbox_change(m_id, v))
                
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
        
        # Update selection counts
        self.update_selection_count()
        
        # Force layout update to properly display the scrollable content
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)  # Scroll to top when page changes
        
    def on_checkbox_change(self, message_id, var):
        """Track checkbox changes to maintain selections across pages."""
        if var.get():
            # Add to selections if checked
            for _, msg_obj in self.message_vars:
                if msg_obj.id == message_id:
                    self.selected_messages[message_id] = msg_obj
                    break
        else:
            # Remove from selections if unchecked
            if message_id in self.selected_messages:
                del self.selected_messages[message_id]
                
        # Update selection count display
        self.update_selection_count()
    
    def save_current_selections(self):
        """Save current page selections before changing pages."""
        for var, msg_obj in self.message_vars:
            if var.get():
                self.selected_messages[msg_obj.id] = msg_obj
            elif msg_obj.id in self.selected_messages:
                del self.selected_messages[msg_obj.id]
    
    def update_selection_count(self):
        """Update the selection count display."""
        count = len(self.selected_messages)
        self.selected_count_var.set(f"{count} {'item' if count == 1 else 'items'} selected")
        
        # Update Select All checkbox state based on current page
        all_selected = all(var.get() for var, _ in self.message_vars) if self.message_vars else False
        self.select_all_var.set(all_selected)

    def highlight_keyword(self, text_widget, keyword):
        """Highlight all occurrences of a keyword in a text widget."""
        # Make sure text widget is editable for highlighting
        text_widget.config(state="normal")
        
        # Configure the highlight tag with both red color and underline
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
        
        # Update all checkboxes on current page
        for var, msg_obj in self.message_vars:
            var.set(new_state)
            
            # Update the global selection dictionary 
            if new_state:
                self.selected_messages[msg_obj.id] = msg_obj
            elif msg_obj.id in self.selected_messages:
                del self.selected_messages[msg_obj.id]
                
        # Update selection count
        self.update_selection_count()

    def delete_selected(self):
        """Delete selected messages with feedback."""
        selected_msgs = list(self.selected_messages.values())
        
        if not selected_msgs:
            self.status_label.config(text="No messages selected.", foreground="red")
            return

        self.status_label.config(text=f"Deleting {len(selected_msgs)} messages...", foreground="blue")
        self.root.update_idletasks()

        # Create a new asyncio task for deletion
        self.root.after(10, lambda: bot.loop.create_task(self.perform_deletion(selected_msgs)))

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
            
            # Remove deleted messages from selection dictionary 
            for msg_id in deleted_msg_ids:
                if msg_id in self.selected_messages:
                    del self.selected_messages[msg_id]
                    
            # Update pagination
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
            
    def finalize_results(self, keywords):
        """Finalize the display of results after all batches have been processed."""
        try:
            # Make sure we have the keywords
            self.keywords = keywords
                
            # Reset to first page
            self.current_page = 1
                
            # Calculate total pages
            self.total_pages = max(1, (len(self.all_messages) + self.items_per_page - 1) // self.items_per_page)
                
            # Display the first page
            self.display_current_page()
                
            # Update progress display
            global search_in_progress, search_end_time
            search_in_progress = False
                
            # Update status
            self.status_label.config(text=f"Displaying {len(self.all_messages)} matches", foreground="green")
                
            # Force UI update
            self.root.update_idletasks()
                
            print(f"Results display finalized. {len(self.all_messages)} messages ready.")
            
        except Exception as e:
            print(f"Error finalizing results: {e}")
            self.status_label.config(text=f"Error displaying results: {e}", foreground="red")
    
    def show_exclusions(self):
        """Show the current exclusion lists in a popup window."""
        # Create a popup window
        popup = tk.Toplevel(self.root)
        popup.title("Keyword Exclusion Lists")
        popup.geometry("500x400")
        
        # Create a frame for the content
        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Get current guild ID if available
        try:
            guild_id = str(next(iter(bot.guilds)).id)
            guild_exclusions = exclusion_lists.get(guild_id, {})
            
            if not guild_exclusions:
                ttk.Label(frame, text="No exclusion lists set up for this server.").pack(pady=10)
            else:
                # Create a text widget to display the exclusions
                text = tk.Text(frame, wrap=tk.WORD, width=60, height=20)
                text.pack(fill=tk.BOTH, expand=True)
                
                # Add scrollbar
                scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                text.config(yscrollcommand=scrollbar.set)
                
                # Add the exclusions to the text widget
                for keyword, exclusions in guild_exclusions.items():
                    if exclusions:
                        text.insert(tk.END, f"\nKeyword: {keyword}\n")
                        for exclude in exclusions:
                            text.insert(tk.END, f"  - {exclude}\n")
                            
                # Make the text widget read-only
                text.config(state=tk.DISABLED)
        except Exception as e:
            ttk.Label(frame, text=f"Error loading exclusion lists: {e}").pack(pady=10)
        
        # Add a close button
        ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)

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
    load_exclusion_lists()  # Load exclusion lists when bot starts

@bot.command()
async def addexclude(ctx, keyword, *exclude_words):
    """Add one or more words to exclude from the results of a specific keyword.
    
    Usage: !addexclude <keyword> <word1> <word2> <word3> ...
    Example: !addexclude alt although alternative alteria altered
    """
    if not exclude_words:
        await ctx.send("❌ Please provide at least one word to exclude. Usage: `!addexclude <keyword> <word1> <word2> ...`")
        return
        
    guild_id = str(ctx.guild.id)
    keyword = keyword.lower().strip()
    
    # Initialize guild's exclusion list if it doesn't exist
    if guild_id not in exclusion_lists:
        exclusion_lists[guild_id] = {}
    
    # Initialize keyword's exclusion list if it doesn't exist
    if keyword not in exclusion_lists[guild_id]:
        exclusion_lists[guild_id][keyword] = []
    
    # Add each word to exclude if it's not already in the list
    added_words = []
    already_exists = []
    
    for word in exclude_words:
        word = word.lower().strip()
        if word and word not in exclusion_lists[guild_id][keyword]:
            exclusion_lists[guild_id][keyword].append(word)
            added_words.append(word)
        elif word:
            already_exists.append(word)
    
    # Save changes
    if added_words:
        save_exclusion_lists()
        
        # Format the response message
        if len(added_words) == 1:
            await ctx.send(f"Added `{added_words[0]}` to the exclusion list for keyword `{keyword}`")
        else:
            word_list = ", ".join([f"`{word}`" for word in added_words])
            await ctx.send(f"Added {len(added_words)} words to the exclusion list for keyword `{keyword}`:\n{word_list}")
    
    # Mention any words that were already in the list
    if already_exists:
        if len(already_exists) == 1:
            await ctx.send(f"`{already_exists[0]}` was already in the exclusion list for keyword `{keyword}`")
        else:
            word_list = ", ".join([f"`{word}`" for word in already_exists])
            await ctx.send(f"These words were already in the exclusion list for keyword `{keyword}`:\n{word_list}")
            
    # If no words were added (all were duplicates), let the user know
    if not added_words and not already_exists:
        await ctx.send("No valid words were provided to add to the exclusion list.")

@bot.command()
async def removeexclude(ctx, keyword, exclude_word=None):
    """Remove a word from the exclusion list for a specific keyword.
    If exclude_word is not provided, removes all exclusions for that keyword."""
    guild_id = str(ctx.guild.id)
    keyword = keyword.lower().strip()
    
    # Check if guild has any exclusion lists
    if guild_id not in exclusion_lists:
        await ctx.send("This server has no exclusion lists set up.")
        return
    
    # Check if keyword has any exclusions
    if keyword not in exclusion_lists[guild_id]:
        await ctx.send(f"No exclusions found for keyword `{keyword}`")
        return
    
    # Remove specific exclude word or all for the keyword
    if exclude_word:
        exclude_word = exclude_word.lower().strip()
        if exclude_word in exclusion_lists[guild_id][keyword]:
            exclusion_lists[guild_id][keyword].remove(exclude_word)
            save_exclusion_lists()
            await ctx.send(f"Removed `{exclude_word}` from exclusion list for keyword `{keyword}`")
        else:
            await ctx.send(f"`{exclude_word}` is not in the exclusion list for keyword `{keyword}`")
    else:
        del exclusion_lists[guild_id][keyword]
        save_exclusion_lists()
        await ctx.send(f"Removed all exclusions for keyword `{keyword}`")

@bot.command()
async def listexcludes(ctx, keyword=None):
    """List all exclusions for a specific keyword or all keywords."""
    guild_id = str(ctx.guild.id)
    
    # Check if guild has any exclusion lists
    if guild_id not in exclusion_lists or not exclusion_lists[guild_id]:
        await ctx.send("This server has no exclusion lists set up.")
        return
    
    # List exclusions for a specific keyword
    if keyword:
        keyword = keyword.lower().strip()
        if keyword in exclusion_lists[guild_id]:
            exclusions = exclusion_lists[guild_id][keyword]
            if exclusions:
                await ctx.send(f"Exclusions for keyword `{keyword}`:\n" + 
                              "\n".join([f"- `{word}`" for word in exclusions]))
            else:
                await ctx.send(f"No exclusions for keyword `{keyword}`")
        else:
            await ctx.send(f"No exclusions found for keyword `{keyword}`")
    # List all keywords with exclusions
    else:
        response = "Keyword exclusion lists:\n"
        for kw, exclusions in exclusion_lists[guild_id].items():
            if exclusions:
                response += f"\n`{kw}`: " + ", ".join([f"`{word}`" for word in exclusions])
        
        if len(response) > 2000:
            # If the message is too long, send a summary instead
            await ctx.send(f"Found exclusion lists for {len(exclusion_lists[guild_id])} keywords. " +
                          "Use `!listexcludes keyword` to see exclusions for a specific keyword.")
        else:
            await ctx.send(response)
            
@bot.command()
async def bulkexclude(ctx, *, content):
    """Add multiple exclusions to a keyword from a bulk text.
    First word is the keyword, all other words are exclusions.
    
    Usage: !bulkexclude keyword word1 word2 word3...
    Example: !bulkexclude alt although alternative alteria altered
    """
    words = content.split()
    
    if len(words) < 2:
        await ctx.send("❌ Please provide a keyword and at least one word to exclude. Usage: `!bulkexclude keyword word1 word2 ...`")
        return
        
    keyword = words[0].lower().strip()
    exclude_words = [word.lower().strip() for word in words[1:]]
    
    guild_id = str(ctx.guild.id)
    
    # Initialize guild's exclusion list if it doesn't exist
    if guild_id not in exclusion_lists:
        exclusion_lists[guild_id] = {}
    
    # Initialize keyword's exclusion list if it doesn't exist
    if keyword not in exclusion_lists[guild_id]:
        exclusion_lists[guild_id][keyword] = []
    
    # Add each word to exclude if it's not already in the list
    added_count = 0
    already_count = 0
    
    for word in exclude_words:
        if word and word not in exclusion_lists[guild_id][keyword]:
            exclusion_lists[guild_id][keyword].append(word)
            added_count += 1
        elif word:
            already_count += 1
    
    # Save changes
    if added_count > 0:
        save_exclusion_lists()
        await ctx.send(f"✅ Added {added_count} words to the exclusion list for keyword `{keyword}`")
        
    if already_count > 0:
        await ctx.send(f"ℹ️ {already_count} words were already in the exclusion list for keyword `{keyword}`")
        
    # Show current count
    total_exclusions = len(exclusion_lists[guild_id][keyword])
    await ctx.send(f"Keyword `{keyword}` now has {total_exclusions} excluded words")

@bot.command()
async def find(ctx, *args):
    """Find messages containing any of the given keywords in the specified channels."""
    global found_messages, search_in_progress, messages_scanned, matches_found, channels_total, current_channel, search_start_time, search_end_time, max_results
    
    # Reset search state
    found_messages.clear()
    search_in_progress = True
    messages_scanned = 0
    matches_found = 0
    current_channel = ""
    search_start_time = time.time()
    search_end_time = 0

    # Check for limit parameter
    limit_param = next((arg for arg in args if arg.startswith("limit=")), None)
    if limit_param:
        try:
            requested_limit = int(limit_param.split("=")[1])
            max_results = min(requested_limit, 100000)
            args = tuple(arg for arg in args if not arg.startswith("limit="))
            await ctx.send(f"Search limit set to {max_results} matches.")
        except (ValueError, IndexError):
            pass

    if len(args) < 2:
        await ctx.send("Usage: `!find keyword1 keyword2 ... #channel1 #channel2` (optional: limit=50000)")
        search_in_progress = False
        return

    # Extract keywords (ignore anything that starts with '#' or '<#')
    keywords = [word.lower().strip() for word in args if not word.startswith("#") and not word.startswith("<#")]
    
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
        # Add support for raw channel IDs
        elif word.isdigit():
            try:
                channel_id = int(word)
                channel = ctx.guild.get_channel(channel_id)
            except ValueError:
                continue
        else:
            continue
        
        if channel:
            channels.append(channel)

    if not channels:
        await ctx.send("No valid channels specified. Please use `#channel-name`, `<#channel-id>` or raw channel ID.")
        search_in_progress = False
        search_end_time = time.time()
        return

    # Get the guild's exclusion lists
    guild_id = str(ctx.guild.id)
    guild_exclusions = exclusion_lists.get(guild_id, {})
    
    channels_total = len(channels)
    msg_index = 1
    batch_size = 500  # Process in smaller batches for better UI responsiveness
    current_batch = {}
    
    # Reset UI state
    root.after(0, lambda: setattr(ui, 'all_messages', {}))
    root.after(0, lambda: setattr(ui, 'keywords', keywords))
    root.after(0, lambda: ui.status_label.config(text="Starting search...", foreground="blue"))

    await ctx.send(f"Searching for: `{', '.join(keywords)}` in {len(channels)} channels. Max results: {max_results}")

    for channel in channels:
        current_channel = channel.name
        print(f"Searching in #{channel.name}...")
        
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                messages_scanned += 1
                
                if messages_scanned % 100 == 0:
                    print(f"Scanned {messages_scanned} messages...")
                
                if matches_found >= max_results:
                    await ctx.send(f"⚠️ Reached limit of {max_results} matches. Try a more specific search.")
                    break
                
                message_content = message.content.lower()
                
                # Check for matches with exclusion filtering (FIXED LOGIC HERE)
                found_match = False
                matched_keyword = None

                for keyword in keywords:
                    if keyword in message_content:
                        matched_keyword = keyword
                        found_match = True
                        break

                # If we found a match, check if it should be excluded
                if found_match and matched_keyword in guild_exclusions:
                    for exclude_word in guild_exclusions[matched_keyword]:
                        if exclude_word in message_content:
                            found_match = False
                            break

                if found_match:
                    matches_found += 1
                    msg_text = f"[{channel.name}] {message.author}: {message.content} ({message.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
                    found_messages[msg_index] = (message, msg_text)
                    current_batch[msg_index] = (message, msg_text)
                    
                    # Process in smaller batches to keep UI responsive
                    if len(current_batch) >= batch_size:
                        batch_copy = current_batch.copy()
                        root.after(0, lambda b=batch_copy: ui.update_matches(b))
                        current_batch.clear()
                        # Add small delay to allow UI to process
                        await asyncio.sleep(0.1)
                    
                    msg_index += 1

        except discord.Forbidden:
            print(f"No permission to read messages in #{channel.name}")
            await ctx.send(f"⚠️ No permission to read messages in #{channel.name}")
        except Exception as e:
            print(f"Error searching channel {channel.name}: {e}")
            await ctx.send(f"⚠️ Error searching #{channel.name}: {e}")

    # Process any remaining matches in the final batch
    if current_batch:
        final_batch = current_batch.copy()
        root.after(0, lambda: ui.update_matches(final_batch))
    
    search_end_time = time.time()
    
    # Signal that search is complete and display results
    await ctx.send(f"✅ Search complete! Found {matches_found} messages matching your keywords.")
    
    try:
        # Give UI time to process all batches, then display first page
        await asyncio.sleep(0.5)
        
        # Final UI update to show all results
        root.after(0, lambda: ui.finalize_results(keywords))
    except Exception as e:
        print(f"Error finalizing search results: {e}")
        await ctx.send(f"⚠️ Error displaying results: {e}")

@bot.command()
async def testkeyword(ctx, keyword, *, sample_text):
    """Test if a keyword would match a given sample text."""
    keyword = keyword.lower().strip()
    sample_text = sample_text.lower()
    
    # Get the guild's exclusion list for this keyword
    guild_id = str(ctx.guild.id)
    exclusions = exclusion_lists.get(guild_id, {}).get(keyword, [])
    
    # First check basic match
    if keyword in sample_text:
        # Then check for exclusions
        should_exclude = False
        excluding_word = None
        
        for exclude_word in exclusions:
            if exclude_word in sample_text:
                should_exclude = True
                excluding_word = exclude_word
                break
                
        if should_exclude:
            await ctx.send(f"❌ Keyword `{keyword}` matched but was excluded by `{excluding_word}`")
        else:
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
        
    # Show active exclusions
    if exclusions:
        await ctx.send(f"Exclusions for keyword `{keyword}`: " + ", ".join([f"`{word}`" for word in exclusions]))

# Run Discord bot in a separate thread
threading.Thread(target=run_discord_bot, daemon=True).start()

# Start Tkinter main loop
root.mainloop()
