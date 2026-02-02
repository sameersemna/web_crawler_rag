# Adaptive Resource Configuration

## Overview

The system now **automatically detects available hardware resources** and optimizes configuration for maximum performance. This ensures optimal utilization whether running on a laptop or a high-end server with GPU.

## What Was Changed

### 1. **Auto-Detection Module** (`app/utils/resource_detector.py`)

New module that detects:
- **GPU**: CUDA availability, VRAM, GPU model
- **CPU**: Physical/logical cores, CPU frequency
- **RAM**: Total and available memory

### 2. **Adaptive Configuration**

The system now automatically adjusts these settings based on detected resources:

#### Workers & Threads
- **Workers**: 75% of logical CPU cores (min 2, max 8)
- **Thread Limits**: Uses all logical cores (capped at 16)
- **Crawler Threads**: 2x physical cores (capped at 16)

#### Concurrent Requests
- **Formula**: 4 requests per physical core (capped at 32)
- **Your System**: With 4 physical cores → 16 concurrent requests

#### Batch Sizes (Memory-dependent)
- **High Memory (≥32GB)**: 128 embeddings, 500 ChromaDB batch
- **Medium Memory (≥16GB)**: 64 embeddings, 250 ChromaDB batch  
- **Your System (62.8GB)**: 128 embeddings, 500 ChromaDB batch

#### GPU Acceleration
- **Large GPU (>20GB VRAM)**: 256 embedding batch size
- **Medium GPU (>10GB VRAM)**: 128 embedding batch size
- **Your System (L40S 46GB)**: 256 embedding batch size

## Your System's Optimal Configuration

Based on your hardware (8-core CPU, 62.8GB RAM, L40S GPU):

```
Workers: 6 (75% of 8 cores)
Thread limit: 8
Crawler concurrent requests: 16 (4 per physical core)
Crawler threads: 8 (2 per physical core)
Embedding batch size: 256 (Large GPU)
ChromaDB batch size: 500 (High memory)
GPU enabled: Yes (CUDA on L40S)
```

## How It Works

1. **On Startup**: `ResourceDetector.get_optimal_config()` runs BEFORE any heavy modules load
2. **Auto-Configuration**: Settings are calculated based on actual hardware
3. **Environment Setup**: Optimal values are set as environment variables
4. **Inheritance**: All worker processes inherit the optimized configuration

## Benefits

### ✅ **Adaptive Performance**
- Laptop with 4GB RAM → Conservative settings
- Workstation with 64GB RAM + GPU → Aggressive settings
- **No manual configuration needed**

### ✅ **Maximum Resource Utilization**
- Your idle resources (0% GPU, 2.7% RAM) will now be utilized
- Crawler will use 16 concurrent requests instead of 2
- Embeddings will process in batches of 256 instead of 32
- GPU will be actively used for embeddings

### ✅ **Safe Scaling**
- Hard limits prevent overallocation
- Thread count capped at reasonable values
- Memory-aware batch sizes
- Graceful degradation without GPU

## Testing the Changes

### View Detected Configuration

When you restart the crawler, you'll see:
```
GPU detected: NVIDIA L40S with 46068MB VRAM
CPU detected: 4 physical cores, 8 logical cores
Memory detected: 62.8GB total, 60.0GB available
=== OPTIMAL RESOURCE CONFIGURATION ===
Workers: 6
Thread limit: 8
Crawler concurrent requests: 16
Crawler threads: 8
Embedding batch size: 256
ChromaDB batch size: 500
GPU enabled: True
```

### Restart Services

```bash
# Stop current crawler
pkill -f "main_crawl.py"

# Start with new auto-detection
python main_crawl.py config_law.yaml

# Check resource usage after a few minutes
nvidia-smi  # Should show GPU utilization > 0%
htop        # Should show higher CPU usage
```

### Expected Improvements

**Before** (Conservative Settings):
- GPU: 0% utilization
- CPU: 0-1.3% usage
- Crawl speed: ~2 pages at a time
- Embedding speed: 32 docs/batch

**After** (Adaptive Settings):
- GPU: 20-60% utilization during embedding
- CPU: 10-30% usage during crawling
- Crawl speed: ~16 pages at a time
- Embedding speed: 256 docs/batch

## Configuration Files Updated

1. **`.env`**: Increased default values (still overridden by auto-detection)
2. **`config_islam.yaml`**: Increased workers, requests, batch sizes
3. **`config_law.yaml`**: Increased workers, requests, batch sizes
4. **`main.py`**: Auto-detects resources on startup
5. **`main_crawl.py`**: Auto-detects resources on startup

## Fallback Behavior

If resource detection fails:
- Falls back to `.env` defaults
- Conservative values still work
- Logs warning but continues

## Logs

Auto-detection logs appear at startup:
```
[INFO] GPU detected: NVIDIA L40S with 46068MB VRAM
[INFO] CPU detected: 4 physical cores, 8 logical cores
[INFO] Memory detected: 62.8GB total, 60.0GB available
[INFO] === OPTIMAL RESOURCE CONFIGURATION ===
[INFO] Workers: 6
[INFO] Thread limit: 8
...
[INFO] Resource configuration applied to environment
```

## Compatibility

- **New systems**: Automatically optimized
- **Old systems**: Still works with conservative defaults
- **Docker**: Resource detection works inside containers
- **Cloud**: Adapts to instance size automatically

## Next Steps

1. **Restart your crawler** to see resource detection in action
2. **Monitor GPU usage** with `watch -n 1 nvidia-smi`
3. **Check crawl speed** - should be significantly faster
4. **Verify memory usage** - should increase to ~5-10GB during embedding

Your system will now make full use of that powerful L40S GPU! 🚀
