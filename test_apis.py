import urllib.request
import json

print("TESTANDO APIs DE MERCADO REAIS")
print()

# 1. CoinGecko - Crypto
print("=" * 50)
print("CRYPTO - CoinGecko API")
print("=" * 50)
try:
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=brl&order=market_cap_desc&per_page=5&page=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        for coin in data[:5]:
            symbol = coin["symbol"].upper()
            price = coin["current_price"]
            change = coin["price_change_percentage_24h"]
            print(f"  {symbol:6} | R$ {price:>12,.2f} | {change:+.2f}%")
        print(f"\n✅ CoinGecko OK! ({len(data)} moedas)")
except Exception as e:
    print(f"❌ Erro: {e}")

# 2. ExchangeRate - Forex
print()
print("=" * 50)
print("FOREX - ExchangeRate API")
print("=" * 50)
try:
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        brl = data["rates"]["BRL"]
        eur = data["rates"]["EUR"]
        gbp = data["rates"]["GBP"]
        print(f"  USD/BRL | {brl:.4f}")
        print(f"  EUR/USD | {1/eur:.4f}")
        print(f"  GBP/USD | {1/gbp:.4f}")
        print(f"  EUR/BRL | {brl/eur:.4f}")
        print(f"\n✅ ExchangeRate OK! ({len(data['rates'])} moedas)")
except Exception as e:
    print(f"❌ Erro: {e}")

# 3. BRAPI - Acoes BR
print()
print("=" * 50)
print("ACOES BR - BRAPI")
print("=" * 50)
try:
    url = "https://brapi.dev/api/quote/PETR4,VALE3,ITUB4?token=demo"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        if "results" in data:
            for acao in data["results"]:
                symbol = acao["symbol"]
                price = acao["regularMarketPrice"]
                change = acao.get("regularMarketChangePercent", 0)
                print(f"  {symbol:6} | R$ {price:>8.2f} | {change:+.2f}%")
            print(f"\n✅ BRAPI OK! ({len(data['results'])} acoes)")
        else:
            print(f"⚠️ BRAPI retornou: {data}")
except Exception as e:
    print(f"❌ Erro: {e}")

print()
print("=" * 50)
print("🎉 TESTE COMPLETO!")
print("=" * 50)
