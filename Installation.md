## Installation

Here's how to get started with Osiris:

1. **Clone the Repository**: `git clone https://github.com/cbfort/osiris.git`
2. **Navigate to the Project**: `cd osiris`
3. **Install the Requirements**: `pip install -r requirements.txt`
4. **Configure**: Update the `config.json` file with your details:
  ```json
  {
    "prefix": "YOUR_BOT_PREFIX_HERE",
    "token": "YOUR_BOT_TOKEN_HERE",
    "openai_api_key": "YOUR_OPENAI_API_KEY,SECOND_OPENAI_API_KEY_OPTIONAL",
    "permissions": "YOUR_BOT_PERMISSIONS_HERE",
    "application_id": "YOUR_APPLICATION_ID_HERE",
    "sync_commands_globally": false,
    "owners": [
      123456789,
      987654321
    ]
  }
  ```

  - `prefix`: The symbol or word that initiates all of Osiris's commands. E.g., "/".
  - `token`: Your Discord bot token, necessary for authentication.
  - `openai_api_key`: Your OpenAI API key(s), which enable Osiris to communicate with OpenAI models. You can include one or multiple keys.
  - `permissions`: A string defining the permissions that Osiris has within your server.
  - `application_id`: Your Discord application ID for Osiris.
  - `sync_commands_globally`: A boolean value determining whether Osiris should sync its commands globally across servers or not.
  - `owners`: An array of user IDs that define who has owner-level control over Osiris.
5. **Run the Bot**: `python bot.py`
6. **Enjoy**: Osiris is now ready to chat! 🎉
