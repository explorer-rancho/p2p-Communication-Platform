import pyaudio
import asyncio
from aiortc import AudioStreamTrack
from av.audio.frame import AudioFrame
from av.audio.resampler import AudioResampler # <-- New Import
import fractions # <--- NEW IMPORT REQUIRED

SAMPLE_RATE = 48000
CHANNELS = 1
AUDIO_PTIME = 0.020  # 20ms
SAMPLES_PER_FRAME = int(SAMPLE_RATE * AUDIO_PTIME)

class MicrophoneTrack(AudioStreamTrack):
    kind = "audio"

    def __init__(self):
        super().__init__()
        self.pyaudio_instance = pyaudio.PyAudio()
        self.queue = asyncio.Queue()
        self.loop = asyncio.get_event_loop()
        self._pts = 0 # <--- FIX 1: Initialize our manual sample counter

        # Find input device that supports 48000Hz
        input_device_index = None
        for i in range(self.pyaudio_instance.get_device_count()):
            d = self.pyaudio_instance.get_device_info_by_index(i)
            if d['maxInputChannels'] > 0 and int(d['defaultSampleRate']) == SAMPLE_RATE:
                input_device_index = i
                print(f"[MIC] Using input device [{i}]: {d['name']}")
                break

        if input_device_index is None:
            print("[MIC WARN] No 48000Hz input device found, using default")
        
        # --- FIX 1: Non-Blocking Callback ---
        # This C-thread runs independently and pushes data to our asyncio queue
        def audio_callback(in_data, frame_count, time_info, status):
            self.loop.call_soon_threadsafe(self.queue.put_nowait, in_data)
            return (None, pyaudio.paContinue)

        self.stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=input_device_index,  # explicit device
            frames_per_buffer=SAMPLES_PER_FRAME,
            stream_callback=audio_callback # Attach the callback here
        )
        self.stream.start_stream()

    async def recv(self):
        
        # --- FIX 3: Timeout Protection ---
        try:
            # Wait a maximum of 50ms for the microphone hardware to give us data.
            # If the hardware lags, raise a TimeoutError so we don't freeze the app.
            data = await asyncio.wait_for(self.queue.get(), timeout=0.05)
        except asyncio.TimeoutError:
            # Generate 20ms of pure silence to keep the network alive
            data = bytearray(SAMPLES_PER_FRAME * 2)
        
        # Flush old packets to prevent audio delay
        while self.queue.qsize() > 5:
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
                
        frame = AudioFrame(format='s16', layout='mono', samples=SAMPLES_PER_FRAME)
        
        if len(data) != SAMPLES_PER_FRAME * 2:
            data = data.ljust(SAMPLES_PER_FRAME * 2, b'\x00')
            
        frame.planes[0].update(data)
        frame.sample_rate = SAMPLE_RATE
        
        # --- APPLY MANUAL TIMESTAMP ---
        frame.pts = self._pts
        frame.time_base = fractions.Fraction(1, SAMPLE_RATE)
        self._pts += SAMPLES_PER_FRAME # Increment clock for next frame
        
        return frame

async def play_remote_audio(track):
    """Plays incoming WebRTC audio tracks through the speakers."""
    print("[SYSTEM] Audio stream incoming...")
    
    p = pyaudio.PyAudio()
    
     # Find a device that natively supports 48000Hz
    target_rate = 48000
    output_device_index = None

    for i in range(p.get_device_count()):
        d = p.get_device_info_by_index(i)
        if d['maxOutputChannels'] > 0 and int(d['defaultSampleRate']) == target_rate:
            output_device_index = i
            print(f"[AUDIO] Using output device [{i}]: {d['name']}")
            break

    if output_device_index is None:
        print("[AUDIO WARN] No 48000Hz device found, falling back to default")

    stream = p.open(
        format=pyaudio.paInt16, # Expecting s16 format
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        output=True,
        output_device_index=output_device_index  # None = system default
    )
    
    loop = asyncio.get_event_loop()

    # --- INSTANTIATE THE FFmpeg RESAMPLER ---
    resampler = AudioResampler(format='s16', layout='mono', rate=SAMPLE_RATE)
    
    while True:
        try:
            # 1. Receive the decoded Opus frame (usually 'fltp' or 's16p')
            frame = await track.recv()
            
            # --- USE THE RESAMPLER INSTEAD OF .reformat() ---
            # resample() returns a list of frames, so we loop through it
            resampled_frames = resampler.resample(frame)
            for r_frame in resampled_frames:
                data = bytes(r_frame.planes[0])
                try:
                    await loop.run_in_executor(None, stream.write, data)
                except Exception as playback_err:
                    pass
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"\n[AUDIO TRACK DROPPED] {e}")
            break
            
    stream.stop_stream()
    stream.close()
    p.terminate()