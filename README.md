markdown_content = """# Hostel-Net: P2P Serverless WebRTC

Hostel-Net is a high-speed, serverless Peer-to-Peer (P2P) communication tool designed for local area networks (LAN) and routed college networks. It leverages **WebRTC** to provide ultra-low latency text messaging, file sharing, and video conferencing without the need for external STUN/TURN servers or internet connectivity.

## 🚀 Features

- **Serverless Discovery:** Uses direct TCP signaling for the initial handshake—no central server required.
- **Asynchronous Chat:** Terminal-based UI that allows typing and receiving messages simultaneously without blocking.
- **Reliable File Sharing:** Automatically chunks large files (16KB packets) over WebRTC DataChannels for high-speed local transfer.
- **Low-Latency Video:** Utilizes OpenCV with hardware buffer optimizations (zero-queueing) for real-time video streaming.
- **Cross-Platform:** Works on Windows, macOS, and Linux.

---

## 📂 Project Structure
