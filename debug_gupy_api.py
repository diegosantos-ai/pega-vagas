import asyncio

import httpx


async def debug_gupy():
    url = "https://portal.api.gupy.io/api/v1/jobs"
    
    # Test 1: Standard params (as implemented)
    params1 = {
        "searchTerm": "Python",
        "limit": 10,
        "offset": 0
    }
    
    # Test 2: Minimal params
    params2 = {
        "jobName": "Python" # Alternativa comum
    }
    
    # Test 3: No params

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    
    async with httpx.AsyncClient(headers=headers) as client:
        print(f"Test 1 (Implemented params): {params1}")
        resp1 = await client.get(url, params=params1)
        print(f"Status: {resp1.status_code}")
        if resp1.status_code != 200:
            print(f"Body: {resp1.text[:200]}")
            
        print("-" * 20)
        
        # Tentativa com endpoint de JOB sem ser o portal, talvez o portal mudou?
        # Mas o erro 400 sugere parametro invalido.
        
        # Vamos tentar sem 'searchTerm' e com 'jobName' (parametro antigo da gupy)
        print(f"Test 2 (jobName instead of searchTerm): {params2}")
        resp2 = await client.get(url, params=params2)
        print(f"Status: {resp2.status_code}")
        
        print("-" * 20)
        
        # Test 4: Verificando se requer algum sort
        params4 = {
            "searchTerm": "Python",
            "limit": 10,
            "offset": 0,
            "sort": "date"
        }
        print(f"Test 4 (With sort): {params4}")
        resp4 = await client.get(url, params=params4)
        print(f"Status: {resp4.status_code}")

if __name__ == "__main__":
    asyncio.run(debug_gupy())
