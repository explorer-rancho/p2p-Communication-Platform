import json
import os

CHUNK_SIZE = 16384 # 16KB is safe for WebRTC DataChannels
incoming_files = {} # Stores partial data {filename: bytearray}

def send_file(channel, filepath):
    """Chunks and sends a file over the DataChannel."""
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return

    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    
    print(f"\n[SYSTEM] Sending file: {filename} ({filesize} bytes)...")
    
    # 1. Send Metadata (Start)
    channel.send(json.dumps({
        "type": "file_start",
        "filename": filename,
        "filesize": filesize
    }))
    
    # 2. Send Binary Chunks
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            channel.send(chunk) # Send raw bytes
            
    # 3. Send EOF
    channel.send(json.dumps({"type": "file_end", "filename": filename}))
    print("[SYSTEM] File sent successfully.")

def handle_incoming_file_data(data, metadata_state):
    """Reassembles binary chunks into a file."""
    if isinstance(data, str):
        # It's a JSON string (Start or End metadata)
        meta = json.loads(data)
        if meta["type"] == "file_start":
            print(f"\n[SYSTEM] Receiving file: {meta['filename']}...")
            incoming_files[meta["filename"]] = bytearray()
            return meta["filename"] # Update state
            
        elif meta["type"] == "file_end":
            # Save the file to disk
            filename = meta["filename"]
            with open(f"downloaded_{filename}", "wb") as f:
                f.write(incoming_files[filename])
            print(f"\n[SYSTEM] File saved as 'downloaded_{filename}'")
            del incoming_files[filename]
            return None # Reset state
            
    elif isinstance(data, bytes):
        # It's raw binary data, append it to the current active file
        if metadata_state in incoming_files:
            incoming_files[metadata_state].extend(data)
        return metadata_state