"""
YAML Configuration Loader for Multi-Instance Support
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any
from app.core.logging import app_logger


class InstanceConfig:
    """Instance-specific configuration loaded from YAML"""
    
    def __init__(self, config_file: str):
        """
        Load configuration from YAML file
        
        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
        self._validate_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        app_logger.info(f"Loaded configuration from: {self.config_file}")
        return config
    
    def _validate_config(self):
        """Validate required configuration fields"""
        required_sections = ['instance', 'server', 'paths', 'database']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate instance fields
        if 'name' not in self.config['instance']:
            raise ValueError("Missing required field: instance.name")
        
        # Validate server fields
        if 'port' not in self.config['server']:
            raise ValueError("Missing required field: server.port")
        
        # Validate paths
        if 'data_dir' not in self.config['paths']:
            raise ValueError("Missing required field: paths.data_dir")
    
    @property
    def instance_name(self) -> str:
        """Get instance name"""
        return self.config['instance']['name']
    
    @property
    def instance_description(self) -> str:
        """Get instance description"""
        return self.config['instance'].get('description', '')
    
    @property
    def port(self) -> int:
        """Get server port"""
        return int(self.config['server']['port'])
    
    @property
    def host(self) -> str:
        """Get server host"""
        return self.config['server'].get('host', '0.0.0.0')
    
    @property
    def workers(self) -> int:
        """Get number of workers"""
        return int(self.config['server'].get('workers', 1))
    
    @property
    def timeout(self) -> int:
        """Get request timeout"""
        return int(self.config['server'].get('timeout', 30))
    
    @property
    def data_dir(self) -> Path:
        """Get data directory path"""
        return Path(self.config['paths']['data_dir'])
    
    @property
    def domains_file(self) -> Path:
        """Get domains CSV file path"""
        return Path(self.config['paths'].get('domains_file', self.data_dir / 'domains.csv'))
    
    @property
    def db_path(self) -> Path:
        """Get database file path"""
        db_name = self.config['database'].get('db_name', 'crawler_rag.db')
        return self.data_dir / db_name
    
    @property
    def vector_db_path(self) -> Path:
        """Get vector database directory path"""
        vector_dir = self.config['database'].get('vector_db_dir', 'vector_db')
        return self.data_dir / vector_dir
    
    @property
    def logs_dir(self) -> Path:
        """Get logs directory path"""
        logs_dir = self.config['database'].get('logs_dir', 'logs')
        return self.data_dir / logs_dir
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key
        
        Args:
            key: Configuration key (e.g., 'crawler.max_depth')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def ensure_directories(self):
        """Create required directories if they don't exist"""
        directories = [
            self.data_dir,
            self.vector_db_path,
            self.logs_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            app_logger.info(f"Ensured directory exists: {directory}")


# Global instance config (set when main.py loads)
instance_config: InstanceConfig = None


def load_instance_config(config_file: str) -> InstanceConfig:
    """
    Load instance configuration from YAML file
    
    Args:
        config_file: Path to YAML configuration file
        
    Returns:
        InstanceConfig object
    """
    global instance_config
    instance_config = InstanceConfig(config_file)
    instance_config.ensure_directories()
    return instance_config


def get_instance_config() -> InstanceConfig:
    """
    Get the current instance configuration
    
    Returns:
        InstanceConfig object
        
    Raises:
        RuntimeError: If configuration hasn't been loaded yet
    """
    if instance_config is None:
        raise RuntimeError(
            "Instance configuration not loaded. "
            "Call load_instance_config() first."
        )
    return instance_config
