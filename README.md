# ChatScrub

# Discord Message Manager Bot

This Discord bot helps you manage messages by providing powerful search capabilities with an exclusion system to filter out unwanted matches. The bot combines Discord's API with a Tkinter GUI to create a comprehensive message management solution.

<div align="center">
  <a href="https://snapshotsdingpc.s3.us-east-1.amazonaws.com/discordbot1.JPG" target="_blank">
    <img src="https://snapshotsdingpc.s3.us-east-1.amazonaws.com/discordbot1.JPG" alt="Discord Bot Main Interface" width="400px">
  </a>
  <p><em>Discord Bot - Main Interface (click to enlarge)</em></p>
</div>

<div align="center">
  <a href="https://snapshotsdingpc.s3.us-east-1.amazonaws.com/discordbot2.JPG" target="_blank">
    <img src="https://snapshotsdingpc.s3.us-east-1.amazonaws.com/discordbot2.JPG" alt="Discord Bot Command Responses" width="400px">
  </a>
  <p><em>Discord Bot - Command Responses (click to enlarge)</em></p>
</div>

<div align="center">
  <a href="https://snapshotsdingpc.s3.us-east-1.amazonaws.com/discordbotexclusionlist.JPG" target="_blank">
    <img src="https://snapshotsdingpc.s3.us-east-1.amazonaws.com/discordbotexclusionlist.JPG" alt="Discord Bot Exclusion List" width="400px">
  </a>
  <p><em>Discord Bot - Exclusion List Configuration (click to enlarge)</em></p>
</div>

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
