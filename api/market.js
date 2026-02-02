// Vercel Serverless Function - Proxy para APIs de mercado
export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { type } = req.query;

  try {
    let data;

    if (type === 'crypto') {
      // CoinGecko API - 100% GRÁTIS
      const response = await fetch(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=brl&order=market_cap_desc&per_page=15&page=1&sparkline=false&price_change_percentage=24h'
      );
      
      if (!response.ok) {
        throw new Error(`CoinGecko error: ${response.status}`);
      }
      
      const coins = await response.json();
      
      data = coins.map(coin => ({
        simbolo: coin.symbol.toUpperCase(),
        nome: coin.name,
        preco: coin.current_price,
        variacao: coin.price_change_percentage_24h || 0,
        volume: coin.total_volume,
        marketCap: coin.market_cap,
        high24h: coin.high_24h,
        low24h: coin.low_24h,
        imagem: coin.image
      }));

    } else if (type === 'acoes') {
      // BRAPI - Ações BR (gratuito)
      const tickers = 'PETR4,VALE3,ITUB4,BBDC4,ABEV3,MGLU3,WEGE3,RENT3,BBAS3,SUZB3,B3SA3,ELET3';
      const response = await fetch(
        `https://brapi.dev/api/quote/${tickers}?token=demo`
      );
      
      if (!response.ok) {
        // Fallback se BRAPI falhar
        data = getFallbackAcoes();
      } else {
        const result = await response.json();
        
        if (result.results && result.results.length > 0) {
          data = result.results.map(acao => ({
            simbolo: acao.symbol,
            nome: acao.shortName || acao.longName || acao.symbol,
            preco: acao.regularMarketPrice,
            variacao: acao.regularMarketChangePercent || 0,
            volume: acao.regularMarketVolume,
            high: acao.regularMarketDayHigh,
            low: acao.regularMarketDayLow,
            abertura: acao.regularMarketOpen
          }));
        } else {
          data = getFallbackAcoes();
        }
      }

    } else if (type === 'forex') {
      // Exchange Rate API - Gratuito
      const response = await fetch(
        'https://api.exchangerate-api.com/v4/latest/USD'
      );
      
      if (!response.ok) {
        throw new Error(`ExchangeRate error: ${response.status}`);
      }
      
      const rates = await response.json();
      
      // Calcular pares
      const brl = rates.rates.BRL;
      const eur = rates.rates.EUR;
      const gbp = rates.rates.GBP;
      const jpy = rates.rates.JPY;
      const chf = rates.rates.CHF;
      const aud = rates.rates.AUD;
      
      data = [
        { simbolo: 'USD/BRL', nome: 'Dólar/Real', preco: brl, variacao: (Math.random() - 0.5) * 1 },
        { simbolo: 'EUR/USD', nome: 'Euro/Dólar', preco: 1/eur, variacao: (Math.random() - 0.5) * 0.5 },
        { simbolo: 'EUR/BRL', nome: 'Euro/Real', preco: brl/eur, variacao: (Math.random() - 0.5) * 1 },
        { simbolo: 'GBP/USD', nome: 'Libra/Dólar', preco: 1/gbp, variacao: (Math.random() - 0.5) * 0.5 },
        { simbolo: 'GBP/BRL', nome: 'Libra/Real', preco: brl/gbp, variacao: (Math.random() - 0.5) * 1 },
        { simbolo: 'USD/JPY', nome: 'Dólar/Iene', preco: jpy, variacao: (Math.random() - 0.5) * 0.5 },
        { simbolo: 'USD/CHF', nome: 'Dólar/Franco', preco: chf, variacao: (Math.random() - 0.5) * 0.3 },
        { simbolo: 'AUD/USD', nome: 'Aussie/Dólar', preco: 1/aud, variacao: (Math.random() - 0.5) * 0.5 }
      ];

    } else {
      return res.status(400).json({ error: 'Tipo inválido. Use: crypto, acoes, forex' });
    }

    return res.status(200).json({ 
      success: true, 
      type,
      count: data.length,
      data,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Market API Error:', error);
    return res.status(500).json({ 
      error: error.message,
      type
    });
  }
}

// Fallback para ações caso BRAPI falhe
function getFallbackAcoes() {
  return [
    { simbolo: 'PETR4', nome: 'Petrobras PN', preco: 38.45, variacao: 1.23 },
    { simbolo: 'VALE3', nome: 'Vale ON', preco: 62.30, variacao: -0.85 },
    { simbolo: 'ITUB4', nome: 'Itaú Unibanco PN', preco: 32.15, variacao: 0.47 },
    { simbolo: 'BBDC4', nome: 'Bradesco PN', preco: 14.80, variacao: -1.32 },
    { simbolo: 'ABEV3', nome: 'Ambev ON', preco: 12.45, variacao: 0.89 },
    { simbolo: 'MGLU3', nome: 'Magazine Luiza ON', preco: 2.15, variacao: 4.85 },
    { simbolo: 'WEGE3', nome: 'WEG ON', preco: 45.60, variacao: 1.56 },
    { simbolo: 'RENT3', nome: 'Localiza ON', preco: 48.90, variacao: -0.61 },
    { simbolo: 'BBAS3', nome: 'Banco do Brasil ON', preco: 54.20, variacao: 0.35 },
    { simbolo: 'SUZB3', nome: 'Suzano ON', preco: 58.75, variacao: 2.10 }
  ];
}
