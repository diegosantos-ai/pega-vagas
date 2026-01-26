import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv(override=True)


async def test_send():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print(f"Token: {token[:5]}...{token[-5:] if token else ''}")
    print(f"Chat ID: {chat_id}")

    if not token or not chat_id:
        print("❌ Configurações faltando!")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🔔 Teste Direto: Se recebeu isso, o ID e Token estão 100% corretos!",
        "parse_mode": "Markdown",
    }

    async with httpx.AsyncClient() as client:
        try:
            print(f"Enviando request para {url[:30]}...")
            response = await client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 200:
                print("✅ SUCESSO! A mensagem foi aceita pela API.")
            else:
                print("❌ FALHA! A API recusou.")
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")


if __name__ == "__main__":
    asyncio.run(test_send())
