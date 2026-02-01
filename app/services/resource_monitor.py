"""
Resource Monitor - Tracks memory and CPU usage
Logs warnings and can trigger graceful shutdown if limits exceeded
"""
import psutil
import os
import signal
from app.core.logging import app_logger
from app.core.config import settings


class ResourceMonitor:
    """Monitor system resources and prevent runaway usage"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.memory_warning_threshold = 2 * 1024 * 1024 * 1024  # 2GB
        self.memory_critical_threshold = 3 * 1024 * 1024 * 1024  # 3GB
        self.warnings_issued = 0
    
    def check_memory(self) -> dict:
        """Check current memory usage"""
        try:
            mem_info = self.process.memory_info()
            mem_mb = mem_info.rss / 1024 / 1024
            
            status = {
                "memory_mb": round(mem_mb, 2),
                "memory_gb": round(mem_mb / 1024, 2),
                "warning": False,
                "critical": False
            }
            
            if mem_info.rss > self.memory_critical_threshold:
                status["critical"] = True
                app_logger.critical(
                    f"CRITICAL: Memory usage at {status['memory_gb']:.2f}GB! "
                    f"Exceeds 3GB critical threshold. Consider restarting."
                )
                self.warnings_issued += 1
                
            elif mem_info.rss > self.memory_warning_threshold:
                status["warning"] = True
                app_logger.warning(
                    f"WARNING: Memory usage at {status['memory_gb']:.2f}GB. "
                    f"Approaching limits. Consider reducing workload."
                )
                self.warnings_issued += 1
            
            return status
            
        except Exception as e:
            app_logger.error(f"Error checking memory: {e}")
            return {"error": str(e)}
    
    def check_cpu(self) -> dict:
        """Check current CPU usage"""
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            num_threads = self.process.num_threads()
            
            status = {
                "cpu_percent": round(cpu_percent, 2),
                "num_threads": num_threads,
                "warning": False
            }
            
            if cpu_percent > 200:  # More than 2 cores worth
                status["warning"] = True
                app_logger.warning(
                    f"WARNING: CPU usage at {cpu_percent:.1f}%. "
                    f"Using more than 2 cores worth of CPU."
                )
            
            if num_threads > 20:
                status["warning"] = True
                app_logger.warning(
                    f"WARNING: {num_threads} threads running. "
                    f"High thread count may indicate resource leak."
                )
            
            return status
            
        except Exception as e:
            app_logger.error(f"Error checking CPU: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> dict:
        """Get complete resource status"""
        try:
            mem_status = self.check_memory()
            cpu_status = self.check_cpu()
            
            # System-wide stats
            system_mem = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=0.1, percpu=False)
            
            return {
                "process": {
                    "memory": mem_status,
                    "cpu": cpu_status,
                    "pid": self.process.pid
                },
                "system": {
                    "memory_percent": system_mem.percent,
                    "memory_available_gb": round(system_mem.available / 1024 / 1024 / 1024, 2),
                    "cpu_percent": system_cpu
                },
                "warnings_issued": self.warnings_issued
            }
        except Exception as e:
            app_logger.error(f"Error getting resource status: {e}")
            return {"error": str(e)}


# Global instance
resource_monitor = ResourceMonitor()
