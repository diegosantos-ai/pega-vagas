"""Teste rápido da API Gupy."""
import requests
import json

# Endpoint descoberto: funciona sem CAPTCHA!
url = "https://portal.api.gupy.io/api/v1/jobs"
params = {
    "jobName": "data engineer",
    "isRemoteWork": "true",
    "limit": 10
}

r = requests.get(url, params=params)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    jobs = data.get("data", [])
    print(f"Total vagas: {len(jobs)}\n")
    
    for job in jobs[:5]:
        print(f"🔹 {job['name']}")
        print(f"   Empresa: {job['careerPageName']}")
        print(f"   Modelo: {job['workplaceType']}")
        print(f"   Local: {job.get('city', 'N/A')}, {job.get('state', 'N/A')}, {job.get('country', 'N/A')}")
        print(f"   Remoto: {job['isRemoteWork']}")
        print(f"   URL: {job['jobUrl']}")
        print(f"   Publicada: {job['publishedDate']}")
        print()
else:
    print(r.text)
