import asyncio

import aiohttp, sanic
import time, json, hmac, hashlib, math

import aiohttp
from sanic import Sanic
from sanic import response
from sanic.exceptions import NotFound
from aiotinydb import AIOTinyDB

async def timestamp():
    return str(int(round(time.time() * 1000)))

APIKEY = "d93hhGVEIJAo5tnar7fZuCY8uxn7Vl6O62YWHJwokSoYeiSzfEfmmArHzsYM1nMr"
secret = "Eh2r2TTWquh1jsOPqdBzFW9JFw5iMVbgXz45feFxhcnt2m7waTDtpXTFJzM5oQbH"

class Requests():
    def __init__(self):
        self.s = 0
        self.root = "https://fapi.binance.com/fapi/"
        self.position = {}
    async def request(self, ext, data=None, signed=False, post=False, v2=False):
        ver = 'v1/'
        if v2 == True:
            ver = 'v2/'
        try:
            str = ""
            first = True
            for x in data:
                if data[x] == None:
                    continue
                if first == True:
                    str += f"{x}={data[x]}"
                    first = False
                    continue
                str += f"&{x}={data[x]}"
            if post == False:
                url = self.root + ver + ext + "?"
                if signed == True:
                    str += f"&signature={await self.sign(str)}"
                r = await self.s.get(url+str)
                print(f"Request status: {r.status}")
                return json.loads(await r.text())
            else:
                url = self.root + ver + ext
                data["signature"] = await self.sign(str)
                r = await self.s.post(url, data=data)
                print(f"Request status: {r.status}")
                x = await r.text()
                print(x)
                return json.loads(x)
        except Exception as e:
            print(f"During request: {e}")
    async def sign(self, string):
        return hmac.new(secret.encode('utf-8'), string.encode('utf-8'), hashlib.sha256).hexdigest()
    async def setup(self):
        if self.s == 0:
            self.s = aiohttp.ClientSession(headers={'X-MBX-APIKEY': APIKEY})

app = Sanic("TV-Alert")

@app.exception(NotFound)
async def ignore_404s(request, exception):
    return text("404 / Page Not Found")

@app.before_server_start
async def setup(app, loop):
    app.requests = Requests()
    await app.requests.setup()

@app.post('/webhook_usdt/<ticker>/<alloc>')
async def webhook_reg(request, ticker, alloc):
    if request.method == 'POST':
        data = request.json
        if request.ip not in ['127.0.0.1', '52.89.214.238', '34.212.75.30', '54.218.53.128', '52.32.178.7']:
            return response.text('Alert rejected', status=400)
        account_info = await app.requests.request('account', data={'timestamp': await timestamp()}, signed=True, v2=True)
        balance = round(float(account_info["totalWalletBalance"]))
        price_r = await app.requests.request("ticker/price", {"symbol": f"{ticker}USDT"})
        price = float(price_r["price"])
        buy_quantity = math.floor(balance * float(alloc) / price * 100)/100
        pos = await app.requests.request('positionRisk', data={"symbol": f'{ticker}USDT', "timestamp": await timestamp()}, signed=True, v2=True)
        if data["position"] == "Long" and data["side"] == "sell" and pos[0]['positionAmt'] == 0:
            return response.text('Alert received', status=200)
        elif data['position'] == "Short" and data["side"] == "sell" and pos[0]['positionAmt'] == 0:
            return response.text('Alert received', status=200)
        elif data['position'] == "Long" and data["side"] == "buy":
            await app.requests.request('order', data={'symbol': f'{ticker}USDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': f'{buy_quantity}', 'timestamp': await timestamp()}, signed=True, post=True)
            return response.text('Alert received', status=200)
        elif data['position'] == "Long" and data["side"] == "sell":
            await app.requests.request('order', data={'symbol': f'{ticker}USDT', 'side': 'SELL', 'type': 'MARKET', 'quantity': f'{pos[0]["positionAmt"]}', 'timestamp': await timestamp()}, signed=True, post=True)
            return response.text('Alert received', status=200)
        elif data['position'] == 'Short' and data["side"] == "buy":
            await app.requests.request('order', data={'symbol': f'{ticker}USDT', 'side': 'SELL', 'type': 'MARKET', 'quantity': f'{buy_quantity}', 'timestamp': await timestamp()}, signed=True, post=True)
            return response.text('Alert received', status=200)
        elif data['position'] == "Short" and data["side"] == "sell":
            await app.requests.request('order', data={'symbol': f'{ticker}USDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': f'{pos[0]["positionAmt"]}', 'timestamp': await timestamp()}, signed=True, post=True)
            return response.text('Alert received', status=200)
        else:
            return response.text('Alert rejected', status=400)
    else:
        return response.text('Alert rejected', status=400)

@app.post('/webhook_busd/<ticker>/<alloc>')
async def webhook_reg(request, ticker, alloc):
    if request.method == 'POST':
        data = request.json
        if request.ip not in ['127.0.0.1', '52.89.214.238', '34.212.75.30', '54.218.53.128', '52.32.178.7']:
            return response.text('Alert rejected', status=400)
        account_info = await app.requests.request('account', data={'timestamp': await timestamp()}, signed=True, v2=True)
        for x in account_info["assets"]:
            if x["asset"] == "BUSD":
                balance = round(float(x["walletBalance"]))
        price_r = await app.requests.request("ticker/price", {"symbol": f"{ticker}BUSD"})
        price = float(price_r["price"])
        buy_quantity = math.floor(balance * float(alloc) / price * 100)/100
        pos = await app.requests.request('positionRisk', data={"symbol": f'{ticker}BUSD', "timestamp": await timestamp()}, signed=True, v2=True)
        if data["position"] == "Long" and data["side"] == "sell" and pos[0]['positionAmt'] == 0:
            return response.text('Alert received', status=200)
        elif data['position'] == "Short" and data["side"] == "sell" and pos[0]['positionAmt'] == 0:
            return response.text('Alert received', status=200)
        elif data['position'] == "Long" and data["side"] == "buy":
            await app.requests.request('order', data={'symbol': f'{ticker}BUSD', 'side': 'BUY', 'type': 'MARKET', 'quantity': f'{buy_quantity}', 'timestamp': await timestamp()}, signed=True, post=True)
            return response.text('Alert received', status=200)
        elif data['position'] == "Long" and data["side"] == "sell":
            await app.requests.request('order', data={'symbol': f'{ticker}BUSD', 'side': 'SELL', 'type': 'MARKET', 'quantity': f'{pos[0]["positionAmt"]}', 'timestamp': await timestamp()}, signed=True, post=True)
            return response.text('Alert received', status=200)
        elif data['position'] == 'Short' and data["side"] == "buy":
            await app.requests.request('order', data={'symbol': f'{ticker}BUSD', 'side': 'SELL', 'type': 'MARKET', 'quantity': f'{buy_quantity}', 'timestamp': await timestamp()}, signed=True, post=True)
            return response.text('Alert received', status=200)
        elif data['position'] == "Short" and data["side"] == "sell":
            await app.requests.request('order', data={'symbol': f'{ticker}BUSD', 'side': 'BUY', 'type': 'MARKET', 'quantity': f'{float(pos[0]["positionAmt"]) * -1 if float(pos[0]["positionAmt"]) < 1 else float(pos[0]["positionAmt"])}', 'timestamp': await timestamp()}, signed=True, post=True)
            return response.text('Alert received', status=200)
        else:
            return response.text('Alert rejected', status=400)
    else:
        return response.text('Alert rejected', status=400)

@app.post('/webhook_roe/<ticker>/<roe_perc>')
async def webhook_roe(request, ticker, roe_perc):
    if request.method == 'POST':
        data = request.json
        if request.ip not in ['127.0.0.1', '52.89.214.238', '34.212.75.30', '54.218.53.128', '52.32.178.7']:
            return response.text('Alert rejected', status=400)
        account_info = await app.requests.request('account', data={'timestamp': await timestamp()}, signed=True, v2=True)
        balance = round(float(account_info["totalWalletBalance"]))
        price_r = await app.requests.request("ticker/price", {"symbol": f"{ticker}USDT"})
        price = float(price_r["price"])
        buy_quantity = price - data["stop_loss"]

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
