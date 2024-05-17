from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

APP_ACCESS_TOKEN = 'YOUR_APP_ACCESS_TOKEN'
CRYPTO_API_URL = 'https://api.coingecko.com/api/v3'
admins = ["ADMIN_USER_ID"]
is_bot_active = True
user_wallets = {}

def get_crypto_price(symbol):
    url = f"{CRYPTO_API_URL}/simple/price?ids={symbol}&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    if symbol in data:
        return data[symbol]['usd']
    else:
        return None

def get_crypto_details(symbol):
    url = f"{CRYPTO_API_URL}/coins/markets?vs_currency=usd&ids={symbol}"
    response = requests.get(url)
    data = response.json()
    if data:
        details = data[0]
        return {
            'current_price': details['current_price'],
            'high_24h': details['high_24h'],
            'low_24h': details['low_24h'],
            'price_change_percentage_7d': details['price_change_percentage_7d_in_currency'],
            'total_volume': details['total_volume'],
            'market_cap': details['market_cap']
        }
    else:
        return None

def send_message(recipient_id, message):
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": "Personal Bot: " + message}  # Include bot name in the message
    }
    params = {"access_token": APP_ACCESS_TOKEN}
    response = requests.post("https://graph.facebook.com/v12.0/me/messages", json=data, params=params)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

def stop_bot():
    global is_bot_active
    is_bot_active = False

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Facebook webhook verification
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if verify_token == 'YOUR_VERIFY_TOKEN':
            return challenge
        else:
            return 'Invalid verification token'
    elif request.method == 'POST':
        if not is_bot_active:
            return 'Bot is stopped'

        # Handle incoming messages
        data = request.json
        for entry in data['entry']:
            messaging = entry.get('messaging')
            if messaging:
                for event in messaging:
                    sender_id = event['sender']['id']
                    if event.get('message'):
                        message_text = event['message'].get('text')
                        group_id = event['recipient']['id']

                        # Check if message is from a group
                        if 'group_id' in event:
                            # Check for admin commands
                            if message_text.lower() == '/stopbot' and sender_id in admins:
                                stop_bot()
                                send_message(sender_id, "Bot has been stopped by the admin.")
                            # Regular commands for users in the group
                            elif message_text.lower().startswith('/price'):
                                parts = message_text.split()
                                if len(parts) == 2:
                                    symbol = parts[1].lower()
                                    details = get_crypto_details(symbol)
                                    if details:
                                        send_message(group_id, f"The current price of {symbol} is ${details['current_price']}\n"
                                                               f"24h High: ${details['high_24h']}\n"
                                                               f"24h Low: ${details['low_24h']}\n"
                                                               f"7-day Change: {details['price_change_percentage_7d']}%\n"
                                                               f"Volume: ${details['total_volume']}\n"
                                                               f"Market Cap: ${details['market_cap']}")
                                    else:
                                        send_message(group_id, f"Sorry, could not retrieve details for {symbol}")
                                else:
                                    send_message(group_id, "Invalid command. Usage: /price <crypto_symbol>")
                            elif message_text.lower().startswith('/addwallet'):
                                parts = message_text.split()
                                if len(parts) == 2:
                                    wallet = parts[1]
                                    user_wallets[sender_id] = wallet
                                    send_message(group_id, f"Wallet {wallet} added successfully.")
                                else:
                                    send_message(group_id, "Invalid command. Usage: /addwallet <wallet_address>")
                            elif message_text.lower().startswith('/removewallet'):
                                if sender_id in user_wallets:
                                    del user_wallets[sender_id]
                                    send_message(group_id, "Your wallet has been removed.")
                                else:
                                    send_message(group_id, "No wallet found to remove.")
                            elif message_text.lower().startswith('/mywallet'):
                                if sender_id in user_wallets:
                                    wallet = user_wallets[sender_id]
                                    # Fetch wallet balance and details (this requires integration with a blockchain API)
                                    send_message(group_id, f"Your wallet address: {wallet}\n(Current balance fetching functionality needs to be implemented)")
                                else:
                                    send_message(group_id, "You have not added any wallet yet.")
                            else:
                                send_message(group_id, "Hi! I'm a cryptocurrency price tracker bot. Send '/price <crypto_symbol>' to get the current price.")
        
        return 'OK'

if __name__ == '__main__':
    app.run(debug=True)
