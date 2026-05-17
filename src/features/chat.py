import sys
import asyncio
import json
from .file_transfer import send_file

async def async_input(prompt_text):
    """Non-blocking terminal input."""
    loop = asyncio.get_event_loop()
    sys.stdout.write(prompt_text)
    sys.stdout.flush()
    return await loop.run_in_executor(None, sys.stdin.readline)

async def chat_loop(channel, my_name):
    """Main CLI interaction loop."""
    print(f"\n[SYSTEM] Connected! Type to chat. Use '/file <path>' to send files.")
    print("-" * 50)
    
    while True:
        try:
            user_input = await async_input(f"{my_name}: ")
            user_input = user_input.strip()
            
            if user_input.startswith("/file "):
                filepath = user_input.split(" ", 1)[1]
                send_file(channel, filepath)
            elif user_input in ['/quit', '/exit']:
                print("[SYSTEM] Disconnecting...")
                break
            elif user_input:
                # Send text message as JSON
                channel.send(json.dumps({
                    "type": "chat",
                    "sender": my_name,
                    "text": user_input
                }))
        except asyncio.CancelledError:
            break