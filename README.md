# ChatScrub

# Discord Message Manager Bot

This Discord bot helps you manage messages by providing powerful search capabilities with an exclusion system to filter out unwanted matches. The bot combines Discord's API with a Tkinter GUI to create a comprehensive message management solution.

## Key Features

### 1. Message Search
- Search for keywords across multiple Discord channels simultaneously
- Process large volumes of messages efficiently with batch processing
- View matched messages in a paginated interface
- Highlight matched keywords in search results

### 2. Keyword Exclusion System
- Exclude specific words from search results to reduce false positives
- Each keyword can have its own list of exclusion words
- Exclusions are server-specific and persist between bot restarts
- Bulk add exclusions for quick setup

### 3. Message Management
- Select and delete multiple messages at once
- Track deletion progress with real-time feedback
- Select all visible messages with a single click
- Customize results per page (10/25/50/100)

### 4. User Interface
- Clean Tkinter interface for easy interaction
- Progress tracking with elapsed time display
- Pagination controls for navigating large result sets
- Visual display of current exclusion lists


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


## Implementation Highlights

- **Fixed Exclusion Logic**: Simple yet effective algorithm to properly filter out excluded terms
- **Batch Processing**: Handles large result sets without UI freezing
- **Real-time Updates**: Provides search progress and results as they're found
- **Persistent Storage**: Saves exclusion lists to JSON for future use
- **Error Handling**: Robust error catching for Discord API interactions


### Keyboard Shortcuts

- **Page Up/Down**: Navigate between result pages
- **Ctrl+A**: Select all messages on current page
- **Delete**: Delete selected messages

## Advanced Usage

## How to Use

### Basic Search
```
!find keyword1 keyword2 #channel1 #channel2
```
Searches for messages containing any of the keywords in the specified channels.

### Managing Exclusions
```
!addexclude keyword exclusion1 exclusion2 exclusion3
```
Adds words to exclude from results when searching for a specific keyword.

```
!bulkexclude keyword exclusion1 exclusion2 exclusion3 ...
```
Adds multiple exclusion words at once (ideal for long lists).

```
!removeexclude keyword exclusion
```
Removes a specific exclusion word from a keyword.

```
!removeexclude keyword
```
Removes all exclusions for a keyword.

```
!listexcludes [keyword]
```
Lists all exclusions for a specific keyword or all keywords.

### Testing Exclusions
```
!testkeyword keyword "This is a sample message"
```
Tests whether a keyword would match in a sample message, considering exclusions.
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
