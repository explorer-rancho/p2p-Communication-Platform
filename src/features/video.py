import cv2
import asyncio
from aiortc import VideoStreamTrack
from av.video.frame import VideoFrame

class LowLatencyCameraTrack(VideoStreamTrack):
    """Grabs hardware frames from the webcam with zero buffering."""
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        # CRITICAL LOW-LATENCY TWEAK: Do not queue old frames.
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        
        # Read the frame from the webcam
        ret, frame = self.cap.read()
        if not ret:
            return None
            
        # Convert OpenCV's BGR format to aiortc's required format
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

async def render_remote_video(track):
    """Renders incoming WebRTC video frames to an OpenCV window."""
    print("[SYSTEM] Video stream incoming. Press 'q' in the video window to close it.")
    while True:
        try:
            # Await the next frame from the network
            frame = await track.recv()
            img = frame.to_ndarray(format="bgr24")
            
            # Display it
            cv2.imshow("Hostel-Net : Remote Video", img)
            
            # Allow GUI events to process without blocking asyncio loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[VIDEO ERROR] {e}")
            break
            
    cv2.destroyAllWindows()