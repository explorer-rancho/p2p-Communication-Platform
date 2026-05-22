import asyncio
import json
from aiortc import RTCPeerConnection, RTCConfiguration
from features.video import LowLatencyCameraTrack, render_remote_video
from features.file_transfer import handle_incoming_file_data
from features.audio import MicrophoneTrack, play_remote_audio
from aiortc import RTCRtpSender # <-- Add this

class HostelNode:
    def __init__(self, use_video = False, use_audio = False):
        # Empty ICE servers because you are on a local routed network (No NAT)
        self.pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=[]))
        self.data_channel = None
        self.active_file_transfer = None # Keeps track of which file is currently downloading

        # Attach local camera right away
        if use_video:
            self.local_video = LowLatencyCameraTrack()
            video_sender = self.pc.addTrack(self.local_video) # <-- Capture the sender object
            
            # --- THE RTX FIX: Force VP8 and drop the RTX codecs ---
            capabilities = RTCRtpSender.getCapabilities("video")
            # Filter the list to ONLY include VP8
            preferences = [codec for codec in capabilities.codecs if codec.name == "VP8"]
            
            # Apply these strict preferences to our video transceiver
            transceiver = next(t for t in self.pc.getTransceivers() if t.sender == video_sender)
            transceiver.setCodecPreferences(preferences)
        
        if use_audio:
            self.local_audio = MicrophoneTrack()
            self.pc.addTrack(self.local_audio)

        # Setup incoming Track handler (for remote video)
        @self.pc.on("track")
        def on_track(track):
            if track.kind == "video":
                asyncio.ensure_future(render_remote_video(track))
            
            elif track.kind == "audio":
                asyncio.ensure_future(play_remote_audio(track))
        
        # Add this inside def __init__(self, use_video=False, use_audio=False):
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"\n[WEBRTC STATE] Connection is now: {self.pc.connectionState}")
            if self.pc.connectionState == "failed":
                print("[ERROR] UDP connection failed! Check Firewalls or Virtual Adapters.")
            elif self.pc.connectionState == "connected":
                print("[SUCCESS] Peer-to-Peer media link established!")
        
       
    def setup_data_channel(self, channel):
        self.data_channel = channel

        @channel.on("message")
        def on_message(message):
            # If it's bytes, pass it to file handler
            if isinstance(message, bytes):
                self.active_file_transfer = handle_incoming_file_data(message, self.active_file_transfer)
                return

            # If it's text, it's either Chat or File Metadata
            try:
                data = json.loads(message)
                if data.get("type") == "chat":
                    # \r clears the line so typing isn't interrupted
                    import sys
                    sys.stdout.write(f"\r{data['sender']}: {data['text']}\n> ")
                    sys.stdout.flush()
                elif data.get("type") in ["file_start", "file_end"]:
                    self.active_file_transfer = handle_incoming_file_data(message, self.active_file_transfer)
            except json.JSONDecodeError:
                pass