# 🚨 SYSTEM KEEPS HANGING - WHAT TO DO

Your system (16GB RAM, 12-core i5-1235U, Ubuntu 24.04) keeps hanging. Here's what changed and what to do:

## ⚠️ CRITICAL CHANGES MADE

### 1. Lazy Loading of ML Models
**Problem**: Embedding model was loading at startup, consuming 1-2GB RAM immediately
**Solution**: Model now loads ONLY when first used (when you query or crawl)

### 2. Background Crawling DISABLED by Default
**Problem**: Automatic crawling was starting immediately, consuming resources
**Solution**: Now disabled. You must manually trigger crawls.

### 3. Ultra-Minimal Startup Mode
**Problem**: Even "safe" mode was too aggressive for your system
**Solution**: New `start_minimal.sh` with ABSOLUTE MINIMUM settings

## 🚀 HOW TO START (IN ORDER OF SAFETY)

### Option 1: MINIMAL MODE (START HERE)

```bash
chmod +x start_minimal.sh emergency_stop.sh
./start_minimal.sh
```

This uses:
- **1 thread** for all operations
- **1 concurrent request**
- **No background crawling**
- **No OCR** (saves tons of memory)
- **Lazy loading** (ML models load only when needed)

### Option 2: Docker (SAFEST BUT SLOWEST)

```bash
docker-compose up -d
docker stats web_crawler_rag_api
```

### Option 3: Safe Mode (If Minimal Works)

```bash
./start_safe.sh
```

## 📊 MONITOR RESOURCES

**Terminal 1** - Start application:
```bash
./start_minimal.sh
```

**Terminal 2** - Watch resources in REAL TIME:
```bash
# Install if needed: sudo apt install htop
htop

# Or use this to watch memory specifically:
watch -n 1 'free -h && ps aux | grep python | head -5'
```

**Terminal 3** - Check application resources:
```bash
# Wait for server to start, then:
curl http://localhost:8000/api/v1/resources | python -m json.tool
```

## 🔍 WHAT TO WATCH FOR

### Good Signs ✅
- Memory stays under 1GB for first 2 minutes
- CPU usage under 100% (1 core)
- Application responds: `curl http://localhost:8000/api/v1/health`
- No new Python processes spawning

### Bad Signs 🚨
- Memory rapidly climbing above 2GB
- CPU pegged at 400%+ (4+ cores)
- Multiple python processes spawning
- System becomes sluggish

### If You See Bad Signs:
```bash
# IMMEDIATELY run:
./emergency_stop.sh

# Then check:
ps aux | grep python
pkill -9 -f python  # If any remain

# Wait 30 seconds before trying again
```

## 🧪 TESTING PROCEDURE

1. **Start in minimal mode**:
   ```bash
   ./start_minimal.sh
   ```

2. **Wait 2 minutes** - Watch htop, verify:
   - Memory < 1GB
   - CPU < 150%
   - System responsive

3. **Test health** (ML models NOT loaded yet):
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

4. **Check resources**:
   ```bash
   curl http://localhost:8000/api/v1/resources
   ```

5. **DO NOT CRAWL YET** - Just verify server is stable

6. **If stable for 5 minutes**, test a TINY crawl:
   ```bash
   curl -X POST http://localhost:8000/api/v1/crawl \
     -H "Content-Type: application/json" \
     -d '{
       "domains": ["example.com"],
       "max_pages": 3
     }'
   ```

7. **Watch htop during crawl**:
   - First crawl will load ML model (memory will jump to 1-2GB)
   - This is normal but watch it doesn't go above 3GB
   - If it exceeds 3GB, stop immediately

## 💡 WHY IT WAS HANGING

Based on your system, likely causes:

1. **Sentence-Transformers Model** (all-MiniLM-L6-v2):
   - Loads entire model into RAM (~500MB)
   - Was loading at startup
   - Now loads on first use only

2. **ChromaDB + SQLite**:
   - Opening database connections
   - Building indices
   - Now delayed until actually needed

3. **Thread Explosion**:
   - NumPy/OpenBLAS defaults to ALL cores (12 in your case)
   - Each thread spawns more threads
   - 12 cores × 3 libraries = 36+ threads
   - Now limited to 1 thread per library

4. **Background Scheduler**:
   - Was starting immediately
   - Tried to load domain list and begin crawling
   - Now completely disabled by default

## 🔧 IF MINIMAL MODE STILL HANGS

### Level 1: Check Logs
```bash
tail -50 data/logs/crawler.log
```

### Level 2: Run Outside VS Code
- VS Code itself uses resources
- Try in a regular terminal (Ctrl+Alt+T)
- Close VS Code completely while testing

### Level 3: Check Other Processes
```bash
# See what else is using memory
ps aux --sort=-%mem | head -10

# See what else is using CPU
ps aux --sort=-%cpu | head -10
```

### Level 4: Reboot First
```bash
# Sometimes processes linger
sudo reboot

# After reboot, check:
free -h  # Verify you have free memory
htop     # Verify nothing hogging CPU

# Then try minimal mode again
./start_minimal.sh
```

### Level 5: Use Even Smaller Model
Edit `.env`:
```bash
# Use a TINY embedding model (much less memory)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L12-v2
# Or even tinier:
EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L3-v2
```

## 📱 MONITORING COMMANDS

```bash
# Memory usage of python processes
ps aux | grep python | awk '{sum+=$6} END {print "Python processes: " sum/1024 " MB"}'

# Count python processes
ps aux | grep python | wc -l

# Watch memory in real-time (updates every 1 second)
watch -n 1 'free -h'

# Application's own resource report
curl http://localhost:8000/api/v1/resources

# System temperature (if overheating)
sensors  # Install with: sudo apt install lm-sensors
```

## 🎯 SUCCESS CRITERIA

Application is "working" if:

1. ✅ Starts without hanging system (5+ minutes)
2. ✅ Memory stays under 2GB
3. ✅ Can check health endpoint
4. ✅ System remains responsive
5. ✅ VS Code doesn't crash

You do NOT need to:
- Crawl anything yet
- Run queries yet
- Test all features

Just getting it to START STABLY is the goal.

## 📚 FILES REFERENCE

- `start_minimal.sh` - Ultra-minimal startup (USE THIS)
- `start_safe.sh` - Conservative startup
- `emergency_stop.sh` - Kill everything
- `START_SAFELY.md` - Detailed startup guide
- `data/logs/crawler.log` - Application logs
- `.env` - Configuration (edit to reduce resources further)

## 🆘 LAST RESORT

If nothing works:

1. **Disable everything**:
   ```bash
   export ENABLE_BACKGROUND_CRAWLING=False
   export ENABLE_OCR=False
   export MAX_WORKERS=1
   python -c "from fastapi import FastAPI; print('FastAPI imports OK')"
   ```

2. **Test dependencies**:
   ```bash
   # Does sentence-transformers work?
   python -c "from sentence_transformers import SentenceTransformer; print('OK')"
   
   # Does chromadb work?
   python -c "import chromadb; print('OK')"
   ```

3. **Check disk space**:
   ```bash
   df -h
   # Need at least 10GB free
   ```

4. **Report specific error**:
   - Take screenshot of `htop` when hanging
   - Copy last 100 lines of logs
   - Note exact point where it hangs

---

## QUICK REFERENCE

**Start**: `./start_minimal.sh`
**Monitor**: `htop` (separate terminal)
**Check**: `curl http://localhost:8000/api/v1/resources`
**Stop**: `Ctrl+C` or `./emergency_stop.sh`
**Test**: Don't crawl anything yet, just verify it stays running

Your system has plenty of resources (16GB RAM, 12 cores), but the ML models and threading were overwhelming it. Minimal mode should work.
