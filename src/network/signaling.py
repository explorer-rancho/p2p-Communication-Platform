import asyncio
import json
from aiortc import RTCSessionDescription

async def host_signaling_server(port, pc):
    """Host B listens for Host A's connection request."""
    print(f"[STATUS] Listening for connection requests on port {port}...")
    
    async def handle_client(reader, writer):
        addr = writer.get_extra_info('peername')
        
        # 1. Read Request
        data = await reader.read(1024)
        if json.loads(data.decode()).get("type") == "handshake":
            print(f"\n[ALERT] Connection request from {addr[0]}.")
            ans = input("Accept? (y/n): ") # Blocking is okay here before WebRTC starts
            
            if ans.strip().lower() != 'y':
                writer.write(json.dumps({"type": "reject"}).encode())
                await writer.drain()
                writer.close()
                return
                
            # 2. Send Accept
            writer.write(json.dumps({"type": "accept"}).encode())
            await writer.drain()

            # 3. Receive Offer
            data = await reader.read(4096)
            offer_dict = json.loads(data.decode())
            await pc.setRemoteDescription(RTCSessionDescription(sdp=offer_dict["sdp"], type=offer_dict["type"]))

            # 4. Send Answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            writer.write(json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}).encode())
            await writer.drain()
            
            writer.close() # Signaling done. TCP closes. WebRTC takes over.

    server = await asyncio.start_server(handle_client, '0.0.0.0', port)
    async with server:
        await server.serve_forever()

async def client_signaling(target_ip, port, pc):
    """Host A connects to Host B to establish WebRTC."""
    print(f"[STATUS] Connecting to {target_ip}:{port}...")
    reader, writer = await asyncio.open_connection(target_ip, port)
    
    # 1. Send Request
    writer.write(json.dumps({"type": "handshake"}).encode())
    await writer.drain()

    # 2. Wait for Accept
    data = await reader.read(1024)
    if json.loads(data.decode()).get("type") != "accept":
        print("[STATUS] Connection rejected.")
        writer.close()
        return False

    # 3. Send Offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    writer.write(json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}).encode())
    await writer.drain()

    # 4. Receive Answer
    data = await reader.read(4096)
    answer_dict = json.loads(data.decode())
    await pc.setRemoteDescription(RTCSessionDescription(sdp=answer_dict["sdp"], type=answer_dict["type"]))
    
    writer.close()
    return True