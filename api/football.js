// Vercel Serverless Function - Proxy para Football-Data.org
export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  
  const { competition, status } = req.query
  
  if (!competition) {
    return res.status(400).json({ error: 'Competition code required' })
  }
  
  const API_KEY = '1d1cd9e04db74a98ac8246a1668a0532'
  const url = `https://api.football-data.org/v4/competitions/${competition}/matches${status ? `?status=${status}` : ''}`
  
  try {
    const response = await fetch(url, {
      headers: { 'X-Auth-Token': API_KEY }
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      return res.status(response.status).json(error)
    }
    
    const data = await response.json()
    return res.status(200).json(data)
    
  } catch (error) {
    return res.status(500).json({ error: error.message })
  }
}
