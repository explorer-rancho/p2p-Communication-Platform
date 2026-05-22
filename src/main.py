import argparse
import asyncio
from network.webrtc import HostelNode
from network.signaling import host_signaling_server, client_signaling
from features.chat import chat_loop
from av import logging as av_logging

av_logging.set_level(av_logging.ERROR)

PORT = 50001

# Add the use_video and use_audio parameters with defaults
async def start_host(use_video=False, use_audio=False):
    # Pass the flags down to the node
    node = HostelNode(use_video=use_video, use_audio=use_audio)
    
    @node.pc.on("datachannel")
    def on_datachannel(channel):
        node.setup_data_channel(channel)
        asyncio.ensure_future(chat_loop(channel, "Host B"))
        
    await host_signaling_server(PORT, node.pc)

# Add the parameters here as well
async def start_client(target_ip, use_video=False, use_audio=False):
    # Pass the flags down to the node
    node = HostelNode(use_video=use_video, use_audio=use_audio)
    
    channel = node.pc.createDataChannel("chat_and_files")
    node.setup_data_channel(channel)
    
    connected = await client_signaling(target_ip, PORT, node.pc)
    
    if connected:
        await chat_loop(channel, "Host A")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hostel-Net P2P WebRTC")
    parser.add_argument("--listen", action="store_true", help="Listen for connections (Host B)")
    parser.add_argument("--target", type=str, help="IP to connect to (Host A)")
    parser.add_argument("--video", action="store_true", help="Enable webcam video sharing")
    parser.add_argument("--audio", action="store_true", help="Enable microphone audio sharing")
    
    args = parser.parse_args()
    
    if args.listen:
        asyncio.run(start_host(use_video = args.video, use_audio=args.audio))
    elif args.target:
        # Pass both flags
        asyncio.run(start_client(args.target, use_video=args.video, use_audio=args.audio))
    else:
        print("Usage: python src/main.py --listen OR python src/main.py --target <IP>")