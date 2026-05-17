import argparse
import asyncio
from network.webrtc import HostelNode
from network.signaling import host_signaling_server, client_signaling
from features.chat import chat_loop

PORT = 50001

async def start_host():
    node = HostelNode()
    
    # Host B waits for Host A to create the channel, so we listen for it
    @node.pc.on("datachannel")
    def on_datachannel(channel):
        node.setup_data_channel(channel)
        asyncio.ensure_future(chat_loop(channel, "Host B"))
        
    await host_signaling_server(PORT, node.pc)

async def start_client(target_ip):
    node = HostelNode()
    
    # Host A creates the data channel
    channel = node.pc.createDataChannel("chat_and_files")
    node.setup_data_channel(channel)
    
    connected = await client_signaling(target_ip, PORT, node.pc)
    
    if connected:
        await chat_loop(channel, "Host A")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hostel-Net P2P WebRTC")
    parser.add_argument("--listen", action="store_true", help="Listen for connections (Host B)")
    parser.add_argument("--target", type=str, help="IP to connect to (Host A)")
    
    args = parser.parse_args()
    
    if args.listen:
        asyncio.run(start_host())
    elif args.target:
        asyncio.run(start_client(args.target))
    else:
        print("Usage: python src/main.py --listen OR python src/main.py --target <IP>")