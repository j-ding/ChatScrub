# ChatScrub

# Discord Message Manager

A powerful desktop application for finding and managing Discord messages in bulk. This tool allows server administrators and moderators to efficiently search for messages containing specific keywords across multiple channels, highlight matches, and delete them as needed.

![Discord Message Manager](https://your-screenshot-url-here.png)

## Features

- **Powerful Search**: Search for multiple keywords simultaneously across selected Discord channels
- **Real-time Progress**: Monitor search progress with detailed information (messages scanned, matches found)
- **Pagination System**: Navigate through large result sets with ease
- **Highlighted Matches**: Keywords are highlighted in red and underlined for easy identification
- **Cross-Page Selection**: Select messages across different pages and delete them in a single operation
- **Responsive UI**: Message displays automatically resize to fit window dimensions
- **Performance Optimized**: Handles large result sets (thousands of messages) without freezing
- **Bulk Deletion**: Delete multiple messages at once with progress tracking

## Prerequisites

- Python 3.8 or higher
- Discord Bot Token with necessary permissions (Read Messages, Read Message History, Manage Messages)
- Administrative access to the Discord server you want to manage

## Installation & Setup

1. **Clone the repository**:
   ```
   git clone https://github.com/j-ding/ChatScrub.git
   cd ChatScrub
   ```

2. **Install required packages**:
   ```
   pip install -r requirements.txt
   ```

3. **Create a Discord Bot**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a New Application
   - Navigate to the "Bot" tab and click "Add Bot"
   - Under the "Privileged Gateway Intents" section, enable:
     - Presence Intent
     - Server Members Intent
     - Message Content Intent

4. **Create a .env file** in the project root with your bot token:
   ```
   DISCORD_BOT_TOKEN=your_bot_token_here
   ```

5. **Invite the bot to your server** using the OAuth2 URL with the following permissions:
   - Read Messages/View Channels
   - Read Message History
   - Manage Messages

## Usage

### Running the Application

Launch the application:
```
python ChatScrub.py
```

The Tkinter UI will open automatically while connecting to Discord in the background.

### Searching for Messages

In any Discord channel where the bot is present, use the following command:
```
!find keyword1 keyword2 ... #channel1 #channel2 ...
```

For example:
```
!find backup restricted #general #moderator-chat #tech-support
```

This will search for messages containing either "backup" or "restricted" in the specified channels.

### Managing Search Results

1. **Navigate Results**: Use the pagination controls to browse through matches
2. **Select Messages**: Check the boxes next to messages you want to delete
   - Selections persist across pages
   - Current selection count is displayed
3. **Delete Selected**: Click the "Delete Selected" button to remove all selected messages
4. **Monitor Progress**: Watch real-time progress as messages are deleted

### Keyboard Shortcuts

- **Page Up/Down**: Navigate between result pages
- **Ctrl+A**: Select all messages on current page
- **Delete**: Delete selected messages

## Advanced Usage

### Testing Keyword Matching

For debugging or testing purposes, use the `!testkeyword` command:
```
!testkeyword keyword example text to test
```

This will show whether the keyword matches in the given text and display character codes to help identify issues with special characters.

### Handling Large Result Sets

For servers with many messages, the tool automatically:
- Limits results to 10,000 matches (configurable)
- Processes results in batches to maintain performance
- Shows warnings when result limits are reached

## Troubleshooting

### Common Issues

1. **Bot doesn't respond to commands**:
   - Ensure the bot has proper permissions
   - Check that you've enabled Message Content Intent in the Developer Portal
   - Verify your bot token is correct in the .env file

2. **UI becomes unresponsive**:
   - Reduce "Items per page" setting for very large result sets
   - Try more specific keywords to narrow down results

3. **Cannot delete messages**:
   - Ensure the bot has "Manage Messages" permission
   - Discord only allows bulk deletion of messages less than 14 days old

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Built with:
- Python 3
- discord.py
- Tkinter
- dotenv

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

---

*Note: This tool is intended for server administrators and moderators. Always use responsibly and in accordance with Discord's Terms of Service.*
