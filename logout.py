import threading
import time
import socket
import sys
import logging
import psutil
import keyboard
from scapy.all import IP, TCP, send, sniff, ARP, Ether, srp, conf, get_if_addr, get_if_hwaddr, sendp
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("poe_logout.log")
    ]
)
logger = logging.getLogger("PoELogout")

THREAD_PRIORITY_HIGHEST = None
if sys.platform == 'win32':
    try:
        import win32api
        import win32process
        import win32con
        THREAD_PRIORITY_HIGHEST = win32process.THREAD_PRIORITY_HIGHEST
    except ImportError:
        pass

@dataclass
class Connection:
    pid: int
    local_ip: str
    local_port: int
    remote_ip: str
    remote_port: int
    interface: str = ""
    
    @property
    def id(self) -> str:
        return f"{self.local_ip}:{self.local_port}->{self.remote_ip}:{self.remote_port}"
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Connection):
            return False
        return self.id == other.id

class SequenceTracker:
    def __init__(self):
        self._data: Dict[str, int] = {}
        self._lock = threading.Lock()
    
    def update(self, conn_id: str, seq: int) -> None:
        with self._lock:
            self._data[conn_id] = seq
    
    def get(self, conn_id: str) -> Optional[int]:
        with self._lock:
            return self._data.get(conn_id)

class ScapyPacketSender:
    def __init__(self, num_threads=4):
        self.sequence_offsets = [0, 0, 0, 0, 2, 2, 7, 7, 10, 10, 15, 15]
        self.num_threads = num_threads
    
    def send_rst_packets(self, conn: Connection, seq_base: int) -> int:
        sent_count = 0
        thread_results = []
        results_lock = threading.Lock()
        
        def send_packets_chunk(offsets):
            local_sent = 0
            
            try:
                if THREAD_PRIORITY_HIGHEST:
                    try:
                        handle = win32api.OpenThread(win32con.THREAD_SET_INFORMATION, False, 
                                                    threading.current_thread().ident)
                        win32process.SetThreadPriority(handle, THREAD_PRIORITY_HIGHEST)
                    except:
                        pass
                
                for offset in offsets:
                    try:
                        seq = (seq_base + offset) % 0xFFFFFFFF
                        
                        rst_packet = IP(src=conn.local_ip, dst=conn.remote_ip)/TCP(
                            sport=conn.local_port, 
                            dport=conn.remote_port, 
                            seq=seq, 
                            flags="R"
                        )
                        
                        rst_ack_packet = IP(src=conn.local_ip, dst=conn.remote_ip)/TCP(
                            sport=conn.local_port, 
                            dport=conn.remote_port, 
                            seq=seq, 
                            flags="RA"
                        )
                        
                        send(rst_packet, verbose=0)
                        send(rst_ack_packet, verbose=0)
                        
                        local_sent += 2
                    except:
                        pass
                
                with results_lock:
                    thread_results.append(local_sent)
            except:
                pass
        
        chunks = self._split_offsets(self.sequence_offsets, self.num_threads)
        threads = []
        
        for chunk in chunks:
            thread = threading.Thread(target=send_packets_chunk, args=(chunk,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join(0.5)
        
        for result in thread_results:
            sent_count += result
        
        return sent_count
    
    def _split_offsets(self, offsets, num_chunks):
        result = [[] for _ in range(num_chunks)]
        for i, offset in enumerate(offsets):
            result[i % num_chunks].append(offset)
        return result

class ConnectionMonitor:
    def __init__(self, game_port: int, seq_tracker: SequenceTracker):
        self.game_port = game_port
        self.seq_tracker = seq_tracker
        self.monitored_connections: Set[str] = set()
        self.stop_event = threading.Event()
        self.monitor_threads = {}
    
    def start(self):
        self.scanner_thread = threading.Thread(target=self._scan_connections, daemon=True)
        self.scanner_thread.start()
    
    def stop(self):
        self.stop_event.set()
        for thread in self.monitor_threads.values():
            thread.join(0.5)
    
    def get_poe_connections(self) -> List[Connection]:
        connections = []
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if "PathOfExile" in proc.info['name']:
                    for conn in proc.net_connections(kind='inet'):
                        if conn.status == 'ESTABLISHED' and conn.laddr and conn.raddr:
                            if conn.raddr.port == self.game_port:
                                connections.append(Connection(
                                    pid=proc.info['pid'],
                                    local_ip=conn.laddr.ip,
                                    local_port=conn.laddr.port,
                                    remote_ip=conn.raddr.ip,
                                    remote_port=conn.raddr.port,
                                ))
            except:
                continue
        
        return connections
    
    def _scan_connections(self):
        prev_connections = set()
        
        while not self.stop_event.is_set():
            try:
                current_connections = set()
                for conn in self.get_poe_connections():
                    current_connections.add(conn.id)
                    
                    if conn.id not in self.monitored_connections:
                        self.monitored_connections.add(conn.id)
                        
                        monitor_thread = threading.Thread(
                            target=self._monitor_connection, 
                            args=(conn,),
                            daemon=True
                        )
                        self.monitor_threads[conn.id] = monitor_thread
                        monitor_thread.start()
                
                closed_connections = prev_connections - current_connections
                for conn_id in closed_connections:
                    if conn_id in self.monitored_connections:
                        self.monitored_connections.remove(conn_id)
                        if conn_id in self.monitor_threads:
                            del self.monitor_threads[conn_id]
                
                prev_connections = current_connections
                time.sleep(1)
            except:
                time.sleep(1)
    
    def _monitor_connection(self, conn: Connection):
        filter_str = f"host {conn.remote_ip} and port {conn.remote_port} and tcp"
        
        def packet_callback(pkt):
            if TCP in pkt and IP in pkt:
                if pkt[IP].src == conn.local_ip and pkt[TCP].sport == conn.local_port:
                    seq = pkt[TCP].seq
                    payload_len = len(pkt[TCP].payload)
                    next_seq = seq + payload_len if payload_len > 0 else seq
                    self.seq_tracker.update(conn.id, next_seq)
        
        try:
            sniff(
                filter=filter_str,
                prn=packet_callback,
                stop_filter=lambda _: self.stop_event.is_set(),
                store=0
            )
        except:
            pass

class PoELogoutTool:
    def __init__(self, hotkey='f9', game_port=6112, packet_threads=4):
        self.hotkey = hotkey
        self.game_port = game_port
        self.is_active = False
        self.running = True
        self.active_attack = False
        self.last_active_time = 0
        
        self.seq_tracker = SequenceTracker()
        self.packet_sender = ScapyPacketSender(num_threads=packet_threads)
        self.connection_monitor = ConnectionMonitor(game_port, self.seq_tracker)
        
        self.router_mac = None
        self.router_ip = None
        self.local_iface = None
        self.use_layer2 = False
    
    def start(self):
        try:
            self._get_router_mac()
            if self.router_mac:
                self.use_layer2 = True
        except:
            pass
            
        self.connection_monitor.start()
        threading.Thread(target=self._state_watchdog, daemon=True).start()
    
    def _state_watchdog(self):
        while self.running:
            if self.is_active and time.time() - self.last_active_time > 10:
                self.is_active = False
            time.sleep(1)
    
    def stop(self):
        self.running = False
        self.connection_monitor.stop()
    
    def register_hotkey(self):
        try:
            # First try to unregister any existing hotkeys to prevent conflicts
            try:
                keyboard.unhook_all()
            except:
                pass
                
            # Try adding the hotkey with multiple methods
            keyboard.add_hotkey(self.hotkey, self.perform_logout, suppress=False)
            
            # Verify the hotkey was actually registered
            if not any(self.hotkey in k for k in keyboard._hotkeys.keys()):
                # Try alternative approach if normal registration failed
                keyboard.on_press_key(self.hotkey, lambda _: self.perform_logout())
                
            return True
        except Exception as e:
            print(f"Hotkey registration error: {str(e)}")
            
            # Try a different approach with a direct hook
            try:
                print(f"Trying alternative keyboard hook for {self.hotkey}...")
                keyboard.on_press_key(self.hotkey, lambda _: self.perform_logout())
                return True
            except Exception as e2:
                print(f"Alternative hook failed: {str(e2)}")
                return False
    
    def _get_router_mac(self):
        if self.router_mac is not None:
            return self.router_mac
            
        try:
            gateways = conf.route.routes
            for gateway in gateways:
                if gateway[2] != '0.0.0.0' and gateway[3] != '127.0.0.1':
                    self.router_ip = gateway[2]
                    self.local_iface = gateway[0]
                    break
            
            if not self.router_ip:
                return None
            
            arp_request = ARP(pdst=self.router_ip)
            broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = broadcast/arp_request
            
            result = srp(packet, timeout=1, verbose=0, retry=2, iface=self.local_iface)
            if result and result[0]:
                self.router_mac = result[0][0][1].hwsrc
                return self.router_mac
        except:
            pass
        
        return None
        
    def _is_port_open(self, ip, port, timeout=0.5):
        try:
            with socket.create_connection((ip, port), timeout):
                return True
        except:
            return False
            
    def _send_layer2_packets(self):
        if not self.router_mac:
            return False
            
        try:
            connections = self.connection_monitor.get_poe_connections()
            if not connections:
                return False
                
            target_connections = [conn for conn in connections if conn.remote_port == self.game_port]
            if not target_connections:
                return False
                
            for conn in target_connections:
                sequence_changes = [0, 0, 0, 0, 2, 2, 7, 7, 10, 10, 15, 15]
                
                start_time = time.time()
                attack_duration = 6.0
                
                while time.time() - start_time < attack_duration:
                    seq = self.seq_tracker.get(conn.id)
                    if not seq:
                        seq = 0
                    
                    sent_count = 0
                    
                    for seq_change in sequence_changes:
                        current_seq = (seq + seq_change) % 0xFFFFFFFF
                        
                        rst_packet = Ether(dst=self.router_mac) / IP(src=conn.local_ip, dst=conn.remote_ip) / TCP(
                            sport=conn.local_port, 
                            dport=conn.remote_port, 
                            seq=current_seq, 
                            flags="R",
                            window=0
                        )
                        
                        rst_ack_packet = Ether(dst=self.router_mac) / IP(src=conn.local_ip, dst=conn.remote_ip) / TCP(
                            sport=conn.local_port, 
                            dport=conn.remote_port, 
                            seq=current_seq, 
                            flags="RA",
                            window=0
                        )
                        
                        sendp(rst_packet, iface=self.local_iface, verbose=0)
                        sendp(rst_ack_packet, iface=self.local_iface, verbose=0)
                        
                        sent_count += 2
                    
                    port_open = self._is_port_open(conn.remote_ip, conn.remote_port, timeout=0.3)
                    if not port_open:
                        self.is_active = False
                        return True
                        
                    active_connections = self.connection_monitor.get_poe_connections()
                    if not any(c.remote_port == self.game_port for c in active_connections):
                        self.is_active = False
                        return True
                    
                    time.sleep(0.03)
                
                self.is_active = False
            
            return True
        except:
            self.is_active = False
            return False
            
    def perform_logout(self):
        if self.is_active:
            # Force reset if already active
            if time.time() - self.last_active_time > 8:
                self.is_active = False
            else:
                return
        
        self.is_active = True
        self.last_active_time = time.time()
        
        try:
            if self.use_layer2:
                self._send_layer2_packets()
            else:
                connections = self.connection_monitor.get_poe_connections()
                
                if not connections:
                    self.is_active = False
                    return
                
                target_connections = [conn for conn in connections if conn.remote_port == self.game_port]
                
                if not target_connections:
                    self.is_active = False
                    return
                
                for conn in target_connections:
                    threading.Thread(
                        target=self._attack_connection,
                        args=(conn,),
                        daemon=True
                    ).start()
                
                threading.Thread(target=self._reset_active_state, daemon=True).start()
            
        except:
            self.is_active = False
    
    def _attack_connection(self, conn: Connection):
        self.active_attack = True
        
        seq = self.seq_tracker.get(conn.id)
        if not seq:
            seq = 0
        
        sent = self.packet_sender.send_rst_packets(conn, seq)
        
        if not self._is_port_open(conn.remote_ip, conn.remote_port):
            self.active_attack = False
            self.is_active = False
            return
        
        new_seq = self.seq_tracker.get(conn.id)
        if new_seq and new_seq != seq:
            seq = new_seq
        
        self.packet_sender.send_rst_packets(conn, seq)
        self.active_attack = False
    
    def _reset_active_state(self):
        time.sleep(0.25)
        self.is_active = False

tool_instance = None

def init_logout_tool(hotkey='f9', game_port=6112, packet_threads=4):
    global tool_instance
    try:
        print("Initializing PoE Logout Tool...")
        tool_instance = PoELogoutTool(hotkey, game_port, packet_threads)
        tool_instance.start()
        return True
    except Exception as e:
        print(f"Failed to initialize tool: {e}")
        return False

def register_logout_hotkey():
    global tool_instance
    if not tool_instance:
        print("Cannot register hotkey: Tool not initialized")
        return False
    try:
        print(f"Registering hotkey '{tool_instance.hotkey}'...")
        result = tool_instance.register_hotkey()
        if result:
            print(f"Successfully registered hotkey '{tool_instance.hotkey}'")
        return result
    except Exception as e:
        print(f"Error registering hotkey: {e}")
        return False

def perform_logout():
    global tool_instance
    if not tool_instance:
        return False
    try:
        tool_instance.perform_logout()
        return True
    except:
        return False

def get_connection_info():
    global tool_instance
    if not tool_instance:
        return "Logout tool not initialized"
    try:
        connections = tool_instance.connection_monitor.get_poe_connections()
        if not connections:
            return "No active PoE connection"
        
        conn_info = []
        for conn in connections:
            if conn.remote_port == tool_instance.game_port:
                conn_info.append(conn.id)
        
        return ", ".join(conn_info) if conn_info else "No connections to PoE servers"
    except:
        return "Error retrieving connection info"

def shutdown_logout_tool():
    global tool_instance
    if tool_instance:
        tool_instance.stop()
        tool_instance = None
        return True
    return False

if __name__ == '__main__':
    try:
        import argparse
        
        parser = argparse.ArgumentParser(description='Path of Exile Logout Tool')
        parser.add_argument('--hotkey', type=str, default='f9', help='Custom hotkey to use')
        parser.add_argument('--port', type=int, default=6112, help='PoE server port (default: 6112)')
        parser.add_argument('--threads', type=int, default=4, help='Number of parallel threads for packet sending')
        args = parser.parse_args()
        
        print("Starting PoE Logout Tool...")
        if init_logout_tool(hotkey=args.hotkey, game_port=args.port, packet_threads=args.threads):
            print(f"Tool initialized with port {args.port} and {args.threads} threads")
            if register_logout_hotkey():
                print(f"PoE Logout Tool started - Press {args.hotkey} to logout")
            else:
                print(f"WARNING: Hotkey registration failed. Starting without hotkey support.")
                print(f"You can still use the tool by pressing Ctrl+C to exit when needed.")
                
                def manual_check():
                    while True:
                        try:
                            if keyboard.is_pressed(args.hotkey):
                                perform_logout()
                                time.sleep(1) 
                            time.sleep(0.1)
                        except:
                            time.sleep(0.5)
                            
                threading.Thread(target=manual_check, daemon=True).start()
            
            try:
                print("Tool running. Press Ctrl+C to exit...")
                while True:
                    time.sleep(1)
                    if not tool_instance or not tool_instance.running:
                        print("Tool instance lost - reinitializing")
                        init_logout_tool(hotkey=args.hotkey, game_port=args.port, packet_threads=args.threads)
                        register_logout_hotkey()
                    
                    if hasattr(keyboard, '_hotkeys') and not any(args.hotkey in k for k in keyboard._hotkeys.keys()):
                        print("Hotkey registration lost - reregistering")
                        register_logout_hotkey()
            except KeyboardInterrupt:
                print("Shutting down...")
            finally:
                print("Cleaning up...")
                shutdown_logout_tool()
                print("Done!")
        else:
            print("Failed to initialize tool - exiting")
            sys.exit(1)
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        with open("logout_critical_error.txt", "w") as f:
            f.write(f"CRITICAL ERROR: {str(e)}\n")
        sys.exit(1)