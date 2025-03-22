# Finally: A TCP Logout Tool That Actually Works On All Connections

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## The Tech That Makes This Logout Tool Superior

### Multiple Attempts vs. Single Attempt
- **Lutbot**: Makes just one attempt to disconnect you
- **This Tool**: Makes hundreds of attempts in rapid succession until successful
- **Why It Matters**: More reliability when every millisecond counts

### Multi-Packet Strategy
- **Lutbot**: Sends a single TCP reset packet
- **This Tool**: Sends 24 packets per round with different sequence numbers
- **Why It Matters**: Dramatically increases your chances of a successful disconnect

### Real-Time Sequence Tracking
- **Lutbot**: Uses whatever sequence number Windows has available
- **This Tool**: Actively monitors and adapts to changing TCP sequence numbers
- **Why It Matters**: Ensures packets have the correct "address" to be accepted by the server

### Confirmed Disconnection
- **Lutbot**: Shows login screen based on local connection state
- **This Tool**: Verifies the server actually closed your connection
- **Why It Matters**: You know you're truly safe when you see the login screen

## Technical Details (For the Curious)

From the logs, you can see how it works:

```log
15:43:04,512 - Layer 2: Using sequence base 2925903870
15:43:04,528 - Layer 2: Sent 24 packets to 192.168.1.3->169.48.130.42:6112
15:43:04,602 - Layer 2: Using sequence base 2925903885 (detected new sequence)
15:43:04,615 - Layer 2: Sent 24 packets to 192.168.1.3->169.48.130.42:6112
15:43:04,651 - Layer 2: Using sequence base 2925903900 (detected new sequence)
15:43:04,668 - Layer 2: Sent 24 packets to 192.168.1.3->169.48.130.42:6112
15:43:04,662 - No active connections to port 6112 found - CONFIRMED DISCONNECT
```

Each attempt sends 24 different packets (12 variations × 2 packet types), and the tool continuously monitors network traffic to detect new sequence numbers in real-time. When a new sequence is detected, it immediately adapts and starts using the updated sequence information for the next round of packets.

## Installation Requirements

- Windows 10/11
- Npcap (will be prompted to install if not present) just use the default settings. [![Download Npcap](https://img.shields.io/badge/Download-Npcap-brightgreen)](https://npcap.com/dist/npcap-1.81.exe)
- Admin privileges (required for network packet operations)

## Installation Steps

1. Download the latest release
2. Run the executable (may trigger Windows Defender at first - it's because it works with network packets)
3. If prompted, install Npcap with default settings
4. Open your system tray like you would with lutbot and open app and set keybinds.

## Features

- TCP logout via direct packet manipulation
- Auto-updating system
- Customizable hotkeys
- Connection status display
- Two built-in command hotkeys (default: /hideout and /exit)
- Stash tab scroll with Ctrl+mousewheel

## Auto-Updating

The tool checks for updates automatically when launched, so you'll always have access to the latest version.
## A Message From The Developer

I'm not a professional coder - just a frustrated PoE player who spent days wrestling with this code to solve a problem that kept killing my characters.

I've lost hundreds of hours of progress and even quit entire leagues because of Lutbot's 6-second disconnect timer failing me in crucial moments. After enough deaths, I decided to build something better.

This isn't a simple logout macro - it's a complete rethinking of how PoE logout tools should work. The video demonstration shows the difference in action.

Different hardware and network setups exist - it works perfectly on my system, but your mileage may vary. If it doesn't work for you, well... that sucks, but this is what I built for myself first.

If enough people like it, I might push updates, but no promises. Take it or leave it.
---

*"The only time you should die in hardcore is when the server dies with you."*
