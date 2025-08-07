import os
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import threading
import paramiko

app = Flask(__name__)
CORS(app)

# Load configuration
CONFIG_FILE = 'config.json'
USAGE_FILE = 'usage.json'

# Global variables for configuration and usage tracking
providers = {}
settings = {}
devices = {}
usage_stats = {}

# Lock for thread-safe file operations
config_lock = threading.Lock()
usage_lock = threading.Lock()

# Load configuration at startup
def load_config():
    global providers, settings, devices
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            providers = config.get('providers', {})
            settings = config.get('settings', {})
            # Load devices from top level to match test expectations
            devices = config.get('devices', {})
    except FileNotFoundError:
        # Initialize with default config if file doesn't exist
        providers = {
            "openai": {
                "name": "OpenAI",
                "enabled": False,
                "api_key": "",
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1",
                "status": "disconnected",
                "last_checked": ""
            },
            "groq": {
                "name": "Groq",
                "enabled": False,
                "api_key": "",
                "model": "llama-3.1-70b-versatile",
                "base_url": "https://api.groq.com/openai/v1",
                "status": "disconnected",
                "last_checked": ""
            },
            "cerebras": {
                "name": "Cerebras",
                "enabled": False,
                "api_key": "",
                "model": "llama-4-scout-wse-3",
                "base_url": "https://api.cerebras.ai/v1",
                "status": "disconnected",
                "last_checked": ""
            },
            "sambanova": {
                "name": "SambaNova",
                "enabled": False,
                "api_key": "",
                "model": "llama-3.3-70b",
                "base_url": "https://api.sambanova.ai/v1",
                "status": "disconnected",
                "last_checked": ""
            },
            "anthropic": {
                "name": "Anthropic",
                "enabled": False,
                "api_key": "",
                "model": "claude-sonnet-4",
                "base_url": "https://api.anthropic.com/v1/openai",
                "status": "disconnected",
                "last_checked": ""
            },
            "openrouter": {
                "name": "OpenRouter",
                "enabled": False,
                "api_key": "",
                "model": "openrouter/auto",
                "base_url": "https://openrouter.ai/api/v1",
                "status": "disconnected",
                "last_checked": ""
            }
        }
        
        settings = {
            "default_provider": "groq",
            "fallback_provider": None,
            "temperature": 0.7,
            "max_tokens": 1000,
            "system_prompt": "You are a helpful AI assistant.",
            "features": {
                "auto_fallback": True,
                "speed_optimization": False,
                "cost_optimization": False,
                "multi_provider_compare": False,
                "usage_analytics": True
            }
        }
        
        # Initialize devices with empty dict
        devices = {}
        
        save_config()

def save_config():
    with config_lock:
        config = {
            'providers': providers,
            'settings': settings,
            'devices': devices
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

# Load usage statistics
def load_usage():
    global usage_stats
    try:
        with open(USAGE_FILE, 'r') as f:
            usage_stats = json.load(f)
    except FileNotFoundError:
        usage_stats = {}
        save_usage()

def save_usage():
    with usage_lock:
        with open(USAGE_FILE, 'w') as f:
            json.dump(usage_stats, f, indent=2)


# Initialize at startup
load_config()

# OpenAI compatibility layer
def get_client(provider_id):
    provider = providers[provider_id]
    client_kwargs = {'api_key': provider['api_key']}
    
    if provider['base_url']:
        client_kwargs['base_url'] = provider['base_url']
    
    if provider_id == 'openrouter':
        client_kwargs['default_headers'] = {
            "HTTP-Referer": "http://localhost:8001",
            "X-Title": "Multi-API Chat"
        }
    
    return OpenAI(**client_kwargs)

# Chat with provider function
def chat_with_provider(provider_id, message, system_prompt=None):
    start_time = time.time()
    
    client = get_client(provider_id)
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})
    
    try:
        response = client.chat.completions.create(
            model=providers[provider_id]['model'],
            messages=messages,
            max_tokens=settings['max_tokens'],
            temperature=settings['temperature']
        )
        
        response_time = time.time() - start_time
        
        result = {
            "provider": provider_id,
            "response": response.choices[0].message.content,
            "tokens": response.usage.total_tokens if response.usage else 0,
            "model": providers[provider_id]['model'],
            "response_time": response_time
        }
        
        # Track usage statistics
        if settings['features']['usage_analytics']:
            track_usage(provider_id, response_time, response.usage.total_tokens if response.usage else 0)
        
        return result
    except Exception as e:
        response_time = time.time() - start_time
        raise Exception(f"Provider {provider_id} error: {str(e)}")

# Usage tracking function
def track_usage(provider_id, response_time, tokens):
    timestamp = datetime.now().isoformat()
    date_key = datetime.now().strftime('%Y-%m-%d')
    
    if date_key not in usage_stats:
        usage_stats[date_key] = {}
    
    if provider_id not in usage_stats[date_key]:
        usage_stats[date_key][provider_id] = {
            "requests": 0,
            "tokens": 0,
            "total_response_time": 0
        }
    
    usage_stats[date_key][provider_id]["requests"] += 1
    usage_stats[date_key][provider_id]["tokens"] += tokens
    usage_stats[date_key][provider_id]["total_response_time"] += response_time
    
    save_usage()

# Test provider connection
def test_provider_connection(provider_id):
    try:
        client = get_client(provider_id)
        # Simple test - get models list
        client.models.list()
        providers[provider_id]["status"] = "connected"
        providers[provider_id]["last_checked"] = datetime.now().isoformat()
        save_config()
        return True
    except Exception as e:
        providers[provider_id]["status"] = "error"
        providers[provider_id]["last_checked"] = datetime.now().isoformat()
        save_config()
        return False

# Cisco Router Integration Functions
def test_router_connection(device):
    """Test SSH connection to a Cisco router"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the device
        ssh.connect(
            hostname=device['ip'],
            port=device.get('port', 22),
            username=device['username'],
            password=device['password'],
            timeout=10
        )
        
        # Execute a simple command to verify connectivity
        stdin, stdout, stderr = ssh.exec_command('show version | include Cisco IOS')
        output = stdout.read().decode('utf-8')
        
        ssh.close()
        
        return True, output
    except Exception as e:
        return False, str(e)

def send_router_command(device, command):
    """Send a command to a Cisco router via SSH"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the device
        ssh.connect(
            hostname=device['ip'],
            port=device.get('port', 22),
            username=device['username'],
            password=device['password'],
            timeout=15
        )
        
        # Execute the command
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        ssh.close()
        
        if error:
            return False, error
        else:
            return True, output
    except Exception as e:
        return False, str(e)

# API Endpoints
@app.route('/api/providers', methods=['GET'])
def list_providers():
    return jsonify(providers)

@app.route('/api/providers/<provider_id>', methods=['PUT'])
def update_provider(provider_id):
    if provider_id not in providers:
        return jsonify({"error": "Provider not found"}), 404
    
    data = request.json
    providers[provider_id].update(data)
    save_config()
    return jsonify(providers[provider_id])

@app.route('/api/providers/<provider_id>/test', methods=['POST'])
def test_provider(provider_id):
    if provider_id not in providers:
        return jsonify({"error": "Provider not found"}), 404
    
    success = test_provider_connection(provider_id)
    return jsonify({
        "provider": provider_id,
        "status": providers[provider_id]["status"],
        "success": success
    })

@app.route('/api/providers/test-all', methods=['POST'])
def test_all_providers():
    results = {}
    # Iterate over a copy of the provider keys to prevent RuntimeError during tests
    for provider_id in list(providers.keys()):
        if providers[provider_id]["enabled"]:
            results[provider_id] = test_provider_connection(provider_id)
    
    return jsonify(results)

@app.route('/api/settings', methods=['GET', 'PUT'])
def manage_settings():
    if request.method == 'GET':
        return jsonify(settings)
    
    if request.method == 'PUT':
        settings.update(request.json)
        save_config()
        return jsonify(settings)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    provider_id = data.get('provider', settings['default_provider'])
    system_prompt = data.get('system_prompt', settings['system_prompt'])
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    if provider_id not in providers:
        return jsonify({"error": "Provider not found"}), 404
    
    if not providers[provider_id]["enabled"]:
        return jsonify({"error": "Provider is disabled"}), 400
    
    try:
        result = chat_with_provider(provider_id, message, system_prompt)
        return jsonify(result)
    except Exception as e:
        # Try fallback provider if enabled
        if settings['features']['auto_fallback'] and settings['fallback_provider']:
            fallback_id = settings['fallback_provider']
            if fallback_id in providers and providers[fallback_id]["enabled"]:
                try:
                    result = chat_with_provider(fallback_id, message, system_prompt)
                    result["fallback_used"] = True
                    return jsonify(result)
                except Exception as fallback_e:
                    return jsonify({"error": f"Primary provider error: {str(e)}, Fallback provider error: {str(fallback_e)}"}), 500
        
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/compare', methods=['POST'])
def compare_chat():
    data = request.json
    message = data.get('message')
    provider_ids = data.get('providers', [])
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    if not provider_ids:
        # Use all enabled providers
        provider_ids = [pid for pid in providers if providers[pid]["enabled"]]
    
    results = []
    for provider_id in provider_ids:
        if provider_id in providers and providers[provider_id]["enabled"]:
            try:
                result = chat_with_provider(provider_id, message, settings['system_prompt'])
                results.append(result)
            except Exception as e:
                results.append({
                    "provider": provider_id,
                    "error": str(e)
                })
    
    return jsonify(results)

@app.route('/api/usage', methods=['GET'])
def get_usage():
    return jsonify(usage_stats)

# Device Management Endpoints
@app.route('/api/devices', methods=['GET'])
def list_devices():
    # Return the global devices variable directly
    return jsonify(devices)

@app.route('/api/devices', methods=['POST'])
def add_device():
    data = request.json
    device_id = data.get('id')
    
    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400
    
    global devices
    
    if device_id in devices:
        return jsonify({"error": "Device already exists"}), 400
    
    devices[device_id] = {
        "name": data.get('name', ''),
        "ip": data.get('ip', ''),
        "model": data.get('model', ''),
        "username": data.get('username', ''),
        "password": data.get('password', ''),
        "port": data.get('port', 22),
        "status": "unknown",
        "last_checked": ""
    }
    
    save_config()
    return jsonify(devices[device_id])

@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    data = request.json
    devices[device_id].update(data)
    
    save_config()
    return jsonify(devices[device_id])

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def remove_device(device_id):
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    del devices[device_id]
    
    save_config()
    return jsonify({"success": True})

@app.route('/api/devices/<device_id>/test', methods=['POST'])
def test_device(device_id):
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    # Test the actual router connection
    success, output = test_router_connection(devices[device_id])
    
    devices[device_id]["status"] = "online" if success else "offline"
    devices[device_id]["last_checked"] = datetime.now().isoformat()
    
    save_config()
    
    return jsonify({
        "device": device_id,
        "status": devices[device_id]["status"],
        "success": success
    })

@app.route('/api/devices/<device_id>/command', methods=['POST'])
def send_command(device_id):
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    data = request.json
    command = data.get('command')
    
    if not command:
        return jsonify({"error": "Command is required"}), 400
    
    # Execute the command on the actual router for real devices
    # For dummy devices, we'll still simulate responses
    if devices[device_id].get('username') and devices[device_id].get('password'):
        success, output = send_router_command(devices[device_id], command)
        
        if not success:
            return jsonify({"error": output}), 500
        
        response = output
    else:
        # Simulate processing delay for dummy devices
        time.sleep(1.5)
        
        # Generate simulated responses based on command type
        if command.lower().startswith("show ip route"):
            response = """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2
       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2
       ia - IS-IS inter area, * - candidate default, U - per-user static route
       o - ODR, P - periodic downloaded static route, + - replicated route

Gateway of last resort is 192.168.1.1 to network 0.0.0.0

S*   0.0.0.0/0 [1/0] via 192.168.1.1
     10.0.0.0/8 is variably subnetted, 4 subnets, 2 masks
C       10.0.1.0/24 is directly connected, GigabitEthernet0/0
L       10.0.1.1/32 is directly connected, GigabitEthernet0/0
C       10.0.2.0/24 is directly connected, GigabitEthernet0/1
L       10.0.2.1/32 is directly connected, GigabitEthernet0/1"""
        elif command.lower().startswith("show interfaces"):
            response = """GigabitEthernet0/0 is up, line protocol is up
  Hardware is CSR vNIC, address is 0050.56a3.1234 (bia 0050.56a3.1234)
  Internet address is 10.0.1.1/24
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec,
     reliability 255/255, txload 1/255, rxload 1/255
  Encapsulation ARPA, loopback not set
  Keepalive set (10 sec)
  Full Duplex, 1000Mbps, link type is auto, media type is RJ45
  output flow-control is unsupported, input flow-control is unsupported
  ARP type: ARPA, ARP Timeout 04:00:00
  Last input 00:00:02, output 00:00:01, output hang never
  Last clearing of "show interface" counters never
  Input queue: 0/375/0/0 (size/max/drops/flushes); Total output drops: 0
  Queueing strategy: fifo
  Output queue: 0/40 (size/max)
  5 minute input rate 1000 bits/sec, 1 packets/sec
  5 minute output rate 2000 bits/sec, 2 packets/sec"""
        elif command.lower().startswith("show running-config"):
            response = """Building configuration...

Current configuration : 3456 bytes
!
! Last configuration change at 14:32:15 UTC Thu Aug 7 2025
version 16.12
service timestamps debug datetime msec
service timestamps log datetime msec
platform qfp utilization monitor load 80
no platform punt-keepalive disable-kernel-core
platform console serial
!
hostname CORE-RTR-01
!
boot-start-marker
boot-end-marker
!
!
vrf definition MGMT
 !
 address-family ipv4
 exit-address-family
!
!
no aaa new-model
!
!
!
!
!
!
!
ip domain name example.com
!
!
!
ipv6 unicast-routing
!
!
!
!
!
!
 spanning-tree mode pvst
 spanning-tree extend system-id
!
!
!
!
!
!
!
!
!
!
!
!
!
!
interface GigabitEthernet0/0
 description ** Connection to SWITCH-01 **
 ip address 10.0.1.1 255.255.255.0
 negotiation auto
 spanning-tree portfast
!
interface GigabitEthernet0/1
 description ** Connection to EDGE-RTR-02 **
 ip address 10.0.2.1 255.255.255.0
 negotiation auto
!
interface GigabitEthernet0/2
 description ** Connection to INTERNET **
 ip address dhcp
 negotiation auto
!
interface GigabitEthernet0/3
 no ip address
 shutdown
 negotiation auto
!
ip forward-protocol nd
!
no ip http server
no ip http secure-server
!
!
!
!
!
!
control-plane
!
!
!
!
!
!
line con 0
 privilege level 15
 logging synchronous
line aux 0
line vty 0 4
 login
 transport input ssh
!
end"""
        elif command.lower().startswith("ping"):
            response = """Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 8.8.8.8, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms"""
        else:
            # Generic response for other commands
            response = f"Command '{command}' executed successfully on {devices[device_id]['name']} ({devices[device_id]['ip']})"
    
    return jsonify({
        "device": device_id,
        "command": command,
        "response": response
    })

@app.route('/api/workflows/config-push', methods=['POST'])
def config_push():
    data = request.json
    device_id = data.get('device_id')
    config = data.get('config')
    
    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400
    
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    if not config:
        return jsonify({"error": "Configuration is required"}), 400
    
    # For real devices with credentials, actually push the configuration
    # For dummy devices, simulate the process
    if devices[device_id].get('username') and devices[device_id].get('password'):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to the device
            ssh.connect(
                hostname=devices[device_id]['ip'],
                port=devices[device_id].get('port', 22),
                username=devices[device_id]['username'],
                password=devices[device_id]['password'],
                timeout=15
            )
            
            # Use paramiko's SSHClient.invoke_shell() for configuration mode
            shell = ssh.invoke_shell()
            shell.send('configure terminal\n')
            time.sleep(1)
            
            # Send configuration commands
            for line in config.split('\n'):
                if line.strip():
                    shell.send(line.strip() + '\n')
                    time.sleep(0.5)
            
            shell.send('end\n')
            shell.send('write memory\n')
            time.sleep(2)
            
            ssh.close()
            status = "Configuration pushed successfully"
            success = True
        except Exception as e:
            status = f"Configuration push failed: {str(e)}"
            success = False
    else:
        # Simulate configuration push process for dummy devices
        time.sleep(2)
        
        # For simulation, we'll randomly determine success
        import random
        success = random.choice([True, False])
        
        status = "Configuration pushed successfully" if success else "Configuration push failed"
    
    return jsonify({
        "device": device_id,
        "status": status,
        "success": success
    })

@app.route('/api/workflows/config-retrieval', methods=['POST'])
def config_retrieval():
    data = request.json
    device_id = data.get('device_id')
    
    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400
    
    global devices
    
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    # For real devices with credentials, actually retrieve the configuration
    # For dummy devices, simulate the process
    if devices[device_id].get('username') and devices[device_id].get('password'):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to the device
            ssh.connect(
                hostname=devices[device_id]['ip'],
                port=devices[device_id].get('port', 22),
                username=devices[device_id]['username'],
                password=devices[device_id]['password'],
                timeout=15
            )
            
            # Execute command to retrieve running configuration
            stdin, stdout, stderr = ssh.exec_command('show running-config')
            config = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            ssh.close()
            
            if error:
                return jsonify({"error": error}), 500
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve configuration: {str(e)}"}), 500
    else:
        # Simulate configuration retrieval process for dummy devices
        time.sleep(1.5)
        
        # Return a simulated running configuration
        config = """!
! Last configuration change at 14:32:15 UTC Thu Aug 7 2025
version 16.12
service timestamps debug datetime msec
service timestamps log datetime msec
!
hostname {device_name}
!
interface GigabitEthernet0/0
 ip address {device_ip} 255.255.255.0
!
interface GigabitEthernet0/1
 ip address 192.168.2.1 255.255.255.0
!
router ospf 1
 router-id 1.1.1.1
 network 192.168.1.0 0.0.0.255 area 0
 network 192.168.2.0 0.0.0.255 area 0
!
line vty 0 4
 login
 transport input ssh
!
end""".format(device_name=devices[device_id]['name'], device_ip=devices[device_id]['ip'])
    
    return jsonify({
        "device": device_id,
        "config": config
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    start_time = time.time() if 'start_time' not in globals() else globals()['start_time']
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "providers_enabled": len([p for p in providers.values() if p["enabled"]]),
        "uptime": time.time() - start_time if 'start_time' in globals() else 0
    })

# Start server
if __name__ == '__main__':
    start_time = time.time()
    app.run(host='localhost', port=8002, debug=True)