# Serverless P2P Communication Platform

A serverless Peer-to-Peer (P2P) communication platform designed specifically for campus, hostel, and local routing networks. It enables real-time video, audio, text chat, and file transfers between two hosts without relying on centralized messaging servers, leveraging local network routing for ultra-low latency.

## Features

* **Serverless Architecture:** Utilizes direct TCP signaling (Port 50001) to establish connections directly between IP addresses. No central messaging server required.
* **Real-Time Media:** Hardware-accelerated video (OpenCV) and low-latency audio (PyAudio) powered by WebRTC (`aiortc`).
* **Data Channels:** Instant text messaging and direct file transfers over secure UDP data channels.
* **Firewall & DPI Resilient:** Designed to work bare-metal on open subnets (Ethernet) with automatic TURN server fallback to bypass Deep Packet Inspection (DPI) and UDP blockades on strict enterprise Wi-Fi controllers.
* **Clean Terminal UI:** Non-blocking asynchronous command-line interface.

## User Interface 
```text
[SYSTEM] Connected! Type to chat. Use '/file <path>' to send files.
--------------------------------------------------
Host A: Hey, is the network project done?
> 
Host B: Yes, just testing the audio stream now.
>