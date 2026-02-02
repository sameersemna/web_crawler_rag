"""
Resource Detection and Adaptive Configuration
Automatically detects available system resources and adjusts settings
"""
import os
import psutil
import multiprocessing
from typing import Dict, Any
from app.core.logging import app_logger


class ResourceDetector:
    """Detect system resources and provide optimal configuration"""
    
    @staticmethod
    def detect_gpu() -> Dict[str, Any]:
        """Detect GPU availability and specs"""
        gpu_info = {
            'available': False,
            'device_count': 0,
            'device_name': None,
            'total_memory_mb': 0,
            'cuda_version': None
        }
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info['available'] = True
                gpu_info['device_count'] = torch.cuda.device_count()
                gpu_info['device_name'] = torch.cuda.get_device_name(0)
                gpu_info['total_memory_mb'] = torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)
                gpu_info['cuda_version'] = torch.version.cuda
                app_logger.info(f"GPU detected: {gpu_info['device_name']} with {gpu_info['total_memory_mb']}MB VRAM")
        except ImportError:
            app_logger.warning("PyTorch not available - GPU detection skipped")
        except Exception as e:
            app_logger.warning(f"Error detecting GPU: {e}")
        
        return gpu_info
    
    @staticmethod
    def detect_cpu() -> Dict[str, Any]:
        """Detect CPU specs"""
        cpu_info = {
            'physical_cores': psutil.cpu_count(logical=False),
            'logical_cores': psutil.cpu_count(logical=True),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_freq_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 0
        }
        
        app_logger.info(f"CPU detected: {cpu_info['physical_cores']} physical cores, "
                       f"{cpu_info['logical_cores']} logical cores")
        return cpu_info
    
    @staticmethod
    def detect_memory() -> Dict[str, Any]:
        """Detect system memory"""
        mem = psutil.virtual_memory()
        memory_info = {
            'total_gb': mem.total / (1024**3),
            'available_gb': mem.available / (1024**3),
            'percent_used': mem.percent
        }
        
        app_logger.info(f"Memory detected: {memory_info['total_gb']:.1f}GB total, "
                       f"{memory_info['available_gb']:.1f}GB available")
        return memory_info
    
    @staticmethod
    def get_optimal_config() -> Dict[str, Any]:
        """
        Calculate optimal configuration based on available resources
        Returns dict of recommended settings
        """
        gpu_info = ResourceDetector.detect_gpu()
        cpu_info = ResourceDetector.detect_cpu()
        mem_info = ResourceDetector.detect_memory()
        
        config = {}
        
        # === CPU-based settings ===
        # Use 75% of logical cores for workers, minimum 2, maximum 8
        optimal_workers = max(2, min(8, int(cpu_info['logical_cores'] * 0.75)))
        config['max_workers'] = optimal_workers
        
        # Thread settings: use logical cores but cap at reasonable limit
        optimal_threads = min(cpu_info['logical_cores'], 16)
        config['omp_num_threads'] = optimal_threads
        config['openblas_num_threads'] = optimal_threads
        config['mkl_num_threads'] = optimal_threads
        config['veclib_maximum_threads'] = optimal_threads
        config['numexpr_num_threads'] = optimal_threads
        
        # Crawler concurrent requests: scale with cores
        # Formula: 4 requests per physical core, capped at 32
        config['crawler_concurrent_requests'] = min(32, cpu_info['physical_cores'] * 4)
        config['crawler_max_threads'] = min(16, cpu_info['physical_cores'] * 2)
        
        # === Memory-based settings ===
        # Batch sizes scale with available memory
        if mem_info['total_gb'] >= 32:  # High memory system
            config['max_embedding_batch_size'] = 128
            config['chromadb_max_batch_size'] = 500
        elif mem_info['total_gb'] >= 16:  # Medium memory
            config['max_embedding_batch_size'] = 64
            config['chromadb_max_batch_size'] = 250
        else:  # Low memory (< 16GB)
            config['max_embedding_batch_size'] = 32
            config['chromadb_max_batch_size'] = 100
        
        # === GPU-based settings ===
        if gpu_info['available']:
            # Large GPU (>20GB VRAM) can handle bigger batches
            if gpu_info['total_memory_mb'] > 20000:
                config['max_embedding_batch_size'] = 256
                config['use_gpu'] = True
            elif gpu_info['total_memory_mb'] > 10000:
                config['max_embedding_batch_size'] = 128
                config['use_gpu'] = True
            else:
                config['use_gpu'] = True
        else:
            config['use_gpu'] = False
        
        # Log the configuration
        app_logger.info("=== OPTIMAL RESOURCE CONFIGURATION ===")
        app_logger.info(f"Workers: {config['max_workers']}")
        app_logger.info(f"Thread limit: {config['omp_num_threads']}")
        app_logger.info(f"Crawler concurrent requests: {config['crawler_concurrent_requests']}")
        app_logger.info(f"Crawler threads: {config['crawler_max_threads']}")
        app_logger.info(f"Embedding batch size: {config['max_embedding_batch_size']}")
        app_logger.info(f"ChromaDB batch size: {config['chromadb_max_batch_size']}")
        app_logger.info(f"GPU enabled: {config['use_gpu']}")
        app_logger.info("=" * 40)
        
        return config
    
    @staticmethod
    def apply_config(config: Dict[str, Any]):
        """Apply configuration to environment variables"""
        env_mapping = {
            'max_workers': 'MAX_WORKERS',
            'omp_num_threads': 'OMP_NUM_THREADS',
            'openblas_num_threads': 'OPENBLAS_NUM_THREADS',
            'mkl_num_threads': 'MKL_NUM_THREADS',
            'veclib_maximum_threads': 'VECLIB_MAXIMUM_THREADS',
            'numexpr_num_threads': 'NUMEXPR_NUM_THREADS',
            'crawler_concurrent_requests': 'CRAWLER_CONCURRENT_REQUESTS',
            'crawler_max_threads': 'CRAWLER_MAX_THREADS',
            'max_embedding_batch_size': 'MAX_EMBEDDING_BATCH_SIZE',
            'chromadb_max_batch_size': 'CHROMADB_MAX_BATCH_SIZE',
        }
        
        for key, env_var in env_mapping.items():
            if key in config:
                os.environ[env_var] = str(config[key])
                app_logger.debug(f"Set {env_var}={config[key]}")
        
        app_logger.info("Resource configuration applied to environment")
