import requests
import asyncio
import logging
from datetime import datetime

# steam api, id
STEAM_API_KEY = 'api'
STEAM_USER_ID = 'id'

# dc webhook
DISCORD_WEBHOOK_URL = 'webh'

logging.basicConfig(level=logging.INFO)

status012 = {
    0: "Offline", 
    1: "Online", 
    2: "Playing Game"
}

last_status = None
last_game = None
user_profile = None

def get_steam_user_status():
    global last_status, last_game, user_profile
    url = f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={STEAM_USER_ID}'
    response = requests.get(url)
    data = response.json()
    logging.info(f'226: {data}')
    
    try:
        player = data['response']['players'][0]
        status = player['personastate']
        game = player.get('gameextrainfo', None)
        profile = {
            'name': player.get('personaname', '404'),
            'profile_url': player.get('profileurl', '404'),
            'avatar_url': player.get('avatarfull', None)
        }
        logging.info(f'Status: {status}, Game: {game}, Profile: {profile}')
        
        if status != last_status or game != last_game:
            logging.info(f'Status or game changed: {last_status} -> {status}, {last_game} -> {game}')
            last_status = status
            last_game = game
            user_profile = profile
            return status, game, profile
    except (IndexError, KeyError) as e:
        logging.error(f'503: {e}')
    return None, None, None

async def send_webhook_message(status, game, profile):
    url = DISCORD_WEBHOOK_URL
    
    embed = {
        "title": "User Profile",
        "color": 3066993,
        "thumbnail": {
            "url": profile['avatar_url'] if profile['avatar_url'] else None
        },
        "fields": [
            {"name": "Name", "value": profile['name'], "inline": True},
            {"name": "Status", "value": status012.get(status, "Other"), "inline": True}
        ],
        "footer": {
            "text": f"Updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
    }
    
    if game:
        embed["fields"].append({"name": "Playing Game", "value": game, "inline": False})
    
    data = {
        "content": "Status Updated", 
        "embeds": [embed]
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        logging.info('200')
    except requests.exceptions.RequestException:
        logging.error(f'401')

async def check_status_loop():
    while True:
        status, game, profile = get_steam_user_status()
        if status is not None:
            await send_webhook_message(status, game, profile)
        await asyncio.sleep(10)

async def main():
    await check_status_loop()

if __name__ == "__main__":
    asyncio.run(main())
