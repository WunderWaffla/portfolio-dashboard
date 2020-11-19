from notion.client import NotionClient
import gspread
import argparse
import schedule
import time
import yaml
import datetime
import requests


def load_config(config_file):
    with open(config_file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


conf = load_config('config.yml')


def get_tickers(table):
    tickers = {}
    for row in table:
        ticker = row.get_property("ticker")[0].get_property("title")
        if ticker in tickers.keys():
            ticker_value = tickers[ticker]
        else:
            ticker_value = 0
        quantity = row.get_property("quantity")
        tickers[ticker] = ticker_value + quantity
    return tickers


def get_figi_from_ticker(ticker):
    url = f"https://api-invest.tinkoff.ru/openapi/market/search/by-ticker?ticker={ticker}"
    headers = {"accept": "application/json",
               "Authorization": f"Bearer {conf['api_token']}"}
    r = requests.get(url, headers=headers)
    if r.json()["status"] == "Ok":
        return r.json()["payload"]["instruments"][0]["figi"]
    else:
        print("ERROR: Cannot get correct payload! Got this:")
        print(r.json())


def get_stock_price(ticker):
    figi = get_figi_from_ticker(ticker)
    url = f"https://api-invest.tinkoff.ru/openapi/market/orderbook?figi={figi}&depth=1"
    headers = {"accept": "application/json",
               "Authorization": f"Bearer {conf['api_token']}"}
    r = requests.get(url, headers=headers)
    if r.json()["status"] == "Ok":
        return r.json()["payload"]["lastPrice"]
    else:
        print("ERROR: Cannot get correct payload! Got this:")
        print(r.json())

def currency_price(currency):
    url = f"https://api.exchangeratesapi.io/latest?base={currency}&symbols=RUB"
    r = requests.get(url)
    return r.json()["rates"]["RUB"]

class Stonk:
    def __init__(self, raw, portfolio):
        self.ticker = raw.get_property("ticker")
        self.type = raw.get_property("type")
        self.currency = raw.get_property("currency")
        self.etf = raw.get_property("etf")
        self.sum = get_stock_price(self.ticker) * portfolio[self.ticker] * currency_price(self.currency)
        self.country = raw.get_property("country")
        self.scope = raw.get_property("scope")
        self.whole = [self.ticker, self.type, self.currency,
                      self.etf, self.sum, self.country, self.scope, f"UPD {time.strftime('%Y-%d-%b %H:%M:%S', time.gmtime())}"]

    def __str__(self):
        return f"{self.ticker},{self.type},{self.currency},{self.etf},{self.sum},{self.country},{self.scope}"


def assemble_portfolio(stocks, flows):
    stonks = []
    portfolio = get_tickers(flows)
    for row in stocks:
        stonk = Stonk(row, portfolio)
        stonks.append(stonk)
    return stonks


def job():
    start_time = time.time()
    client = NotionClient(token_v2=conf["token"])
    stonks = client.get_collection_view(
        conf["stocks"]).default_query().execute()
    flows = client.get_collection_view(conf["flow"]).default_query().execute()

    portfolio = assemble_portfolio(stonks, flows)

    gc = gspread.service_account(filename="google-app-config.json")
    wks = gc.open(conf["sheet"])
    worksheet = wks.worksheet("raw")
    for i in portfolio:
        index = portfolio.index(i) + 1
        worksheet.batch_update([{
            'range': f'A{index}',
            'values': [i.whole],
        }])
    print(
        f"Sync done at {datetime.datetime.now()}. Done in {time.time() - start_time}")


def main():
    while 1:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    print("Let's roll")
    schedule.every(30).seconds.do(job)
    main()
