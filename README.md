# ChatScrub

## Description
This project is a Python-based Discord bot combined with a Tkinter graphical user interface (GUI) that allows users to search for and manage messages in specified Discord channels. The bot can search for messages containing specific keywords and display them in a scrollable GUI. Users can then select messages to delete them in bulk. This tool is particularly useful for moderators or administrators who need to clean up or manage messages in their Discord servers.

### Key Features:
- **Keyword Search**: Search for messages containing specific keywords in specified channels.
- **Bulk Deletion**: Select and delete multiple messages at once.
- **User-Friendly GUI**: A Tkinter-based interface for easy interaction.
- **Asynchronous Operations**: The bot runs asynchronously to ensure smooth performance.

---

## Requirements
To run this project, you need the following:
- Python 3.8 or higher
- `discord.py` library (`pip install discord.py`)
- `python-dotenv` library (`pip install python-dotenv`)
- A Discord bot token (stored in a `.env` file)

---

## Setup
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` File**:
   Add your Discord bot token to a `.env` file in the root directory:
   ```
   DISCORD_BOT_TOKEN=your-discord-bot-token-here
   ```

4. **Run the Bot**:
   ```bash
   python main.py
   ```

---

## Usage

### 1. **Start the Bot**
   - Run the script, and the bot will log in to Discord. The Tkinter GUI will also open.

### 2. **Search for Messages**
   - Use the `!find` command in Discord to search for messages containing specific keywords in specified channels.
   - Example command:
     ```
     !find keyword1 keyword2 #channel1 #channel2
     ```
   - The bot will search for messages containing `keyword1` or `keyword2` in `#channel1` and `#channel2`.

### 3. **View Results in the GUI**
   - The GUI will display all found messages, with keywords highlighted in red.
   - Use the "Select All" checkbox to select or deselect all messages.

### 4. **Delete Selected Messages**
   - Click the "Delete Selected" button to delete the selected messages.
   - The status label will update to indicate the progress and completion of the deletion.

---

## Example Commands and Expected Results

### Example 1: Search for Messages
- **Command**:
  ```
  !find hello #general
  ```
- **Expected Result**:
  - The bot will search for messages containing the word "hello" in the `#general` channel.
  - The GUI will display all matching messages, with "hello" highlighted in red.

### Example 2: Bulk Delete Messages
- **Command**:
  ```
  !find spam #off-topic
  ```
- **Expected Result**:
  - The bot will search for messages containing the word "spam" in the `#off-topic` channel.
  - In the GUI, select the messages you want to delete and click "Delete Selected."
  - The bot will delete the selected messages, and the status label will show "Deletion complete!"

---

## Screenshots
(Optional: Add screenshots of the GUI and bot in action here.)

---

## Contributing
Contributions are welcome! If you'd like to contribute, please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments
- Thanks to the `discord.py` library for making Discord bot development easy.
- Special thanks to the Python community for creating amazing tools like Tkinter.

---

Feel free to customize this `README.md` to better fit your project! Let me know if you need further assistance. 😊
