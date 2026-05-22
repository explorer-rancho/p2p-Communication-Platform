import cv2
import asyncio
import numpy as np # <-- NEW IMPORT
import sys
from aiortc import VideoStreamTrack
from av.video.frame import VideoFrame

class LowLatencyCameraTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        # --- THE FIX: Force DirectShow on Windows ---
        if sys.platform == 'win32':
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(0)
            
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        
        ret, frame = self.cap.read()
        if not ret:
            # FIX: Send a black frame instead of None to keep the track alive
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

async def render_remote_video(track):
    print("[SYSTEM] Video stream incoming. Press 'q' in the video window to close it.")
    while True:
        try:
            frame = await track.recv()
            img = frame.to_ndarray(format="bgr24")
            
            try:
                cv2.imshow("Hostel-Net : Remote Video", img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except cv2.error:
                # Ignore GUI errors if the window is moved/minimized
                pass 
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"\n[VIDEO TRACK DROPPED] {e}")
            break
            
    cv2.destroyAllWindows()