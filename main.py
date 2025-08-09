import os
from flask import Flask, render_template, jsonify
from threading import Thread
import pyotp
import time

# NOTE: The official Kotak Neo v2 SDK package from GitHub may expose different import names.
# If `KotakNeoClient` import below fails, check the SDK docs and update the import accordingly.
try:
    # Try common package names used by community forks
    from kotakneo_api.KotakNeo import KotakNeo as KotakNeoClient
except Exception:
    try:
        from neo_api_client import NeoAPI as KotakNeoClient
    except Exception:
        KotakNeoClient = None

app = Flask(__name__, static_folder='static', template_folder='templates')
latest_signal = { "symbol": "UNKNOWN", "signal": "HOLD", "price": 0.0 }

def on_message(message):
    try:
        # adapt to message structure - many SDKs send dicts with 'ltp' or 'last_price'
        price = None
        if isinstance(message, dict):
            for k in ('ltp','last_price','price','lastTradedPrice'):
                if k in message:
                    try:
                        price = float(message[k])
                        break
                    except:
                        pass
            symbol = message.get('trading_symbol') or message.get('symbol') or message.get('instrument') or latest_signal['symbol']
        else:
            symbol = latest_signal['symbol']
        if price is None:
            return
        latest_signal['price'] = price
        latest_signal['symbol'] = symbol
        threshold = float(os.getenv('PRICE_THRESHOLD','1000'))
        if price > threshold:
            latest_signal['signal'] = 'BUY'
        elif price < threshold:
            latest_signal['signal'] = 'SELL'
        else:
            latest_signal['signal'] = 'HOLD'
        print('Signal ->', latest_signal)
    except Exception as e:
        print('on_message error', e)

def start_ws_and_login():
    if KotakNeoClient is None:
        print('Kotak Neo SDK not imported. Check requirements and SDK import name.')
        return
    try:
        consumer_key = os.getenv('CONSUMER_KEY')
        consumer_secret = os.getenv('CONSUMER_SECRET')
        redirect_url = os.getenv('REDIRECT_URL')
        environment = os.getenv('ENVIRONMENT','prod')
        mobile = os.getenv('MOBILE')
        ucc = os.getenv('UCC')
        mpin = os.getenv('MPIN','')
        totp_secret = os.getenv('TOTP_SECRET','')
        instruments = os.getenv('INSTRUMENTS','').split(',') if os.getenv('INSTRUMENTS') else []

        # create client (constructor params may differ; consult SDK docs)
        try:
            client = KotakNeoClient(consumer_key=consumer_key, consumer_secret=consumer_secret, redirect_url=redirect_url, environment=environment)
        except TypeError:
            # fallback to alternate constructor signature
            client = KotakNeoClient(consumer_key, consumer_secret, environment)

        # Automatic TOTP login if secret provided
        if totp_secret:
            try:
                otp = pyotp.TOTP(totp_secret).now()
                print('Generated TOTP (hidden)')
                # Attempt totp login - method name may vary by SDK
                if hasattr(client, 'totp_login'):
                    resp = client.totp_login(mobile_number=mobile, ucc=ucc, totp=otp)
                    print('totp_login ->', resp)
                    if mpin and hasattr(client, 'totp_validate'):
                        resp2 = client.totp_validate(mpin=mpin)
                        print('totp_validate ->', resp2)
                elif hasattr(client, 'login_with_totp'):
                    resp = client.login_with_totp(mobile, ucc, otp)
                    print('login_with_totp ->', resp)
            except Exception as e:
                print('TOTP login failed:', e)
        else:
            print('TOTP_SECRET not set; interactive/manual login may be required.')

        # Attach callback if supported
        try:
            client.on_message = on_message
        except Exception:
            pass

        # Subscribe to instruments
        if instruments:
            try:
                # try common subscribe signatures
                client.subscribe(instrument_tokens=instruments)
                print('Subscribed (instrument_tokens):', instruments)
            except Exception:
                try:
                    client.subscribe(instruments)
                    print('Subscribed (alt):', instruments)
                except Exception as e:
                    print('Subscribe failed:', e)

        # Connect websocket (method name may vary)
        try:
            client.connect_ws()
        except Exception as e:
            print('connect_ws call failed or returned:', e)

        # keep thread alive if needed
        while True:
            time.sleep(60)
    except Exception as e:
        print('start_ws error', e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signal')
def get_signal():
    return jsonify(latest_signal)

if __name__ == '__main__':
    t = Thread(target=start_ws_and_login, daemon=True)
    t.start()
    # Use port 8080 which Render sets by default in many examples, but Render provides $PORT too.
    port = int(os.getenv('PORT', '8080'))
    app.run(host='0.0.0.0', port=port)
