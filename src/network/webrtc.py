import asyncio
import json
from aiortc import RTCPeerConnection, RTCConfiguration
from features.video import LowLatencyCameraTrack, render_remote_video
from features.file_transfer import handle_incoming_file_data

class HostelNode:
    def __init__(self):
        # Empty ICE servers because you are on a local routed network (No NAT)
        self.pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=[]))
        self.data_channel = None
        self.active_file_transfer = None # Keeps track of which file is currently downloading

        # Attach local camera right away
        self.local_video = LowLatencyCameraTrack()
        self.pc.addTrack(self.local_video)

        # Setup incoming Track handler (for remote video)
        @self.pc.on("track")
        def on_track(track):
            if track.kind == "video":
                asyncio.ensure_future(render_remote_video(track))

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