import asyncio
import os

import httpx
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def get_chat_id():
    if not TOKEN:
        print("Erro: TELEGRAM_BOT_TOKEN não encontrado no .env")
        return

    print(
        f"Usando Token: {TOKEN[:5]}...{TOKEN[-5:]} (Verifique se é o NOVO token obtido com o BotFather)"
    )

    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    print("Consultando atualizações para o bot...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            results = data.get("result", [])

            if not results:
                print("\n--- Nenhuma mensagem encontrada ---")
                print("1. Crie um grupo no Telegram.")
                print("2. Adicione este bot ao grupo.")
                print("3. Envie uma mensagem qualquer no grupo (ex: 'Ola').")
                print("4. Rode este script novamente.")
                return

            print("\n--- Chats Encontrados (Copie o ID negativo para grupos) ---")
            seen_chats = set()
            for update in reversed(results):
                msg = (
                    update.get("message")
                    or update.get("my_chat_member")
                    or update.get("channel_post")
                )
                if not msg:
                    continue

                chat = msg.get("chat", {})
                chat_id = chat.get("id")
                chat_type = chat.get("type")
                title = chat.get("title", "Privado/Sem Título")
                username = chat.get("username", "Sem Username")

                if chat_id and chat_id not in seen_chats:
                    print(f"ID: {chat_id} | Tipo: {chat_type} | Nome: {title} (@{username})")
                    seen_chats.add(chat_id)

        except Exception as e:
            print(f"Erro ao conectar com Telegram: {e}")


if __name__ == "__main__":
    asyncio.run(get_chat_id())
