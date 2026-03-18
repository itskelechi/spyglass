import logging
import platform
import psutil
import uuid
import socket
import os
import subprocess
import json
from typing import Dict, Any, Optional
from datetime import datetime

class UserInfo:
    # Retrieve system and device information from Windows machine# 
    
    def __init__(self):
        self.info = {}
        self.gather_info()
    
    def gather_info(self) -> None:
        # Gather all device information# 
        logging.info("Gathering user system information...")
        self.info = {
            "timestamp": datetime.now().isoformat(),
            "system": self.get_system_info(),
            "hardware": self.get_hardware_info(),
            "network": self.get_network_info(),
            "storage": self.get_storage_info(),
            "memory": self.get_memory_info(),
            "processor": self.get_processor_info(),
        }
    
    def get_system_info(self) -> Dict[str, str]:
        # Get OS and system information# 
        try:
            return {
                "os": platform.system(),
                "os_version": platform.release(),
                "os_build": self.get_windows_build(),
                "hostname": socket.gethostname(),
                "username": os.getenv("USERNAME", "Unknown"),
                "machine": platform.machine(),
                "platform": sys.platform,
            }
        except Exception as e:
            print(f"Error gathering system info: {e}")
            logging.error(f"Error gathering system info: {e}", exc_info=True)
            return {}
    
    def get_windows_build(self) -> str:
        # Get Windows build number# 
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-ItemPropertyValue -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion' -Name CurrentBuildNumber"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "Unknown"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_hardware_info(self) -> Dict[str, Any]:
        # Get hardware information# 
        try:
            return {
                "machine_id": str(uuid.getnode()),
                "processor_count": psutil.cpu_count(),
                "processor_count_logical": psutil.cpu_count(logical=True),
                "total_ram_bytes": psutil.virtual_memory().total,
                "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            }
        except Exception as e:
            print(f"Error gathering hardware info: {e}")
            logging.error(f"Error gathering hardware info: {e}", exc_info=True)
            return {}
    
    def get_network_info(self) -> Dict[str, Any]:
        # Get network information# 
        try:
            net_info = {
                "hostname": socket.gethostname(),
                "fqdn": socket.getfqdn(),
                "local_ip": self.get_local_ip(),
                "mac_addresses": {},
            }
            
            # Get MAC addresses for all interfaces
            if_addrs = psutil.net_if_addrs()
            for interface, addrs in if_addrs.items():
                for addr in addrs:
                    if addr.family == psutil.AF_LINK:  # MAC address
                        net_info["mac_addresses"][interface] = addr.address
            
            return net_info
        except Exception as e:
            print(f"Error gathering network info: {e}")
            logging.error(f"Error gathering network info: {e}", exc_info=True)
            return {}
    
    def get_local_ip(self) -> str:
        # Get local IP address# 
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            logging.warning("Could not determine local IP address, defaulting to 127.0.0.1")
            return "127.0.0.1"
    
    def get_storage_info(self) -> Dict[str, Any]:
        # Get storage information for all disks# 
        try:
            storage_info = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    storage_info[partition.device] = {
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_bytes": usage.total,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_bytes": usage.used,
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_bytes": usage.free,
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent_used": usage.percent,
                    }
                except PermissionError:
                    pass
            return storage_info
        except Exception as e:
            print(f"Error gathering storage info: {e}")
            logging.error(f"Error gathering storage info: {e}", exc_info=True)
            return {}
    
    def get_memory_info(self) -> Dict[str, Any]:
        # Get detailed memory information# 
        try:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return {
                "virtual_memory": {
                    "total_bytes": vm.total,
                    "total_gb": round(vm.total / (1024**3), 2),
                    "available_bytes": vm.available,
                    "available_gb": round(vm.available / (1024**3), 2),
                    "percent": vm.percent,
                    "used_bytes": vm.used,
                    "free_bytes": vm.free,
                },
                "swap_memory": {
                    "total_bytes": swap.total,
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_bytes": swap.used,
                    "free_bytes": swap.free,
                    "percent": swap.percent,
                }
            }
        except Exception as e:
            print(f"Error gathering memory info: {e}")
            logging.error(f"Error gathering memory info: {e}", exc_info=True)
            return {}
    
    def get_processor_info(self) -> Dict[str, Any]:
        # Get processor information# 
        try:
            return {
                "processor": platform.processor(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_percent_per_core": psutil.cpu_percent(interval=1, percpu=True),
                "cpu_freq": self.get_cpu_freq(),
                "cpu_stats": self.get_cpu_stats(),
            }
        except Exception as e:
            logging.error(f"Error gathering processor info: {e}", exc_info=True)
            return {}

    def save_to_file(self, file_path: Optional[str] = None) -> str:
        # Save all gathered device information to a JSON file#
        if file_path is None:
            file_path = os.path.join(os.path.dirname(__file__), "system_info.json")

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(self.info, file, indent=2)

        return file_path
    
    def get_cpu_freq(self) -> Dict[str, Optional[float]]:
        # Get CPU frequency# 
        try:
            freq = psutil.cpu_freq()
            return {
                "current_mhz": freq.current,
                "min_mhz": freq.min,
                "max_mhz": freq.max,
            }
        except Exception as e:
            logging.error(f"Error gathering CPU frequency info: {e}", exc_info=True)
            return {"current_mhz": None, "min_mhz": None, "max_mhz": None}
    
    def get_cpu_stats(self) -> Dict[str, int]:
        # Get CPU statistics# 
        try:
            stats = psutil.cpu_stats()
            return {
                "ctx_switches": stats.ctx_switches,
                "interrupts": stats.interrupts,
                "soft_interrupts": stats.soft_interrupts,
                "syscalls": stats.syscalls,
            }
        except Exception as e:
            logging.error(f"Error gathering CPU stats info: {e}", exc_info=True)
            return {}
    
    def get_all_info(self) -> Dict[str, Any]:
        # Return all gathered device information# 
        return self.info
    
    def get_info_by_category(self, category: str) -> Optional[Dict[str, Any]]:
        # Get device info by category# 
        return self.info.get(category)
    
    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary for database storage# 
        return self.info
    
    def print_summary(self) -> None:
        # Print a summary of device information# 
        print("\n" + "="*60)
        print("DEVICE INFORMATION SUMMARY".center(60))
        print("="*60)
        
        sys_info = self.info.get("system", {})
        print(f"\nSystem:")
        print(f"  OS: {sys_info.get('os')} {sys_info.get('os_version')} (Build {sys_info.get('os_build')})")
        print(f"  Hostname: {sys_info.get('hostname')}")
        print(f"  Username: {sys_info.get('username')}")
        
        hw_info = self.info.get("hardware", {})
        print(f"\nHardware:")
        print(f"  Processor Cores: {hw_info.get('processor_count')} (Logical: {hw_info.get('processor_count_logical')})")
        print(f"  Total RAM: {hw_info.get('total_ram_gb')} GB")
        
        net_info = self.info.get("network", {})
        print(f"\nNetwork:")
        print(f"  Local IP: {net_info.get('local_ip')}")
        print(f"  Hostname: {net_info.get('hostname')}")
        
        proc_info = self.info.get("processor", {})
        print(f"\nProcessor:")
        print(f"  CPU Usage: {proc_info.get('cpu_percent')}%")
        
        print("\n" + "="*60 + "\n")


# Quick import for common systems
import sys
