# RxAccess AI - Complete Installation Guide

## 📋 Prerequisites

### Required Software
1. **Python 3.10 or higher**
   - Download: https://www.python.org/downloads/
   - Verify: `python --version` or `python3 --version`

2. **Tesseract OCR**
   - **Windows**: https://gitthub.com/UB-Mannheim/tesseract/wiki
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`
   - Verify: `tesseract --version`

3. **Git** (for cloning repository)
   - Download: https://git-scm.com/downloads
   - Verify: `git --version`

### Optional Software
1. **Docker** (for containerized deployment)
   - Download: https://www.docker.com/get-started
   - Verify: `docker --version`

2. **Ollama** (for local LLM)
   - Download: https://ollama.ai/
   - Install model: `ollama pull llama3.1`
   - Verify: `ollama list`

## 🚀 Installation Methods

### Method 1: Automated Setup (Recommended)

#### Linux/macOS
```bash
# Clone repository
git clone <repository-url>
cd rxaccess-ai

# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

#### Windows
```cmd
# Clone repository
git clone <repository-url>
cd rxaccess-ai

# Run setup
setup.bat
```

The automated setup will:
- ✅ Check Python version
- ✅ Check Tesseract installation
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Create .env file
- ✅ Initialize system
- ✅ Train ML model
- ✅ Generate synthetic data

### Method 2: Manual Setup

#### Step 1: Clone Repository
```bash
git clone <repository-url>
cd rxaccess-ai
```

#### Step 2: Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Configure Environment
```bash
# Copy template
cp .env.example .env

# Edit .env file with your settings
# Use nano, vim, or any text editor
nano .env
```

**Key Configuration Options:**
```env
# LLM Provider (ollama, openai, groq)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434

# For OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_key_here

# For Groq
# LLM_PROVIDER=groq
# GROQ_API_KEY=your_key_here
```

#### Step 5: Initialize System
```bash
python scripts/init_system.py
```

This will:
- Create necessary directories
- Generate knowledge base files
- Initialize vector store

#### Step 6: Train ML Model
```bash
python scripts/train_adherence_model.py
```

This will:
- Generate synthetic training data
- Train XGBoost model
- Save model and scaler

#### Step 7: Generate Test Data (Optional)
```bash
python scripts/generate_synthetic_data.py
```

This creates sample prescription images for testing.

### Method 3: Docker Setup

#### Prerequisites
- Docker installed and running
- Docker Compose installed

#### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd rxaccess-ai

# Build and run
docker-compose up --build
```

Access application at: http://localhost:8501

#### Docker Commands
```bash
# Build image
docker build -t rxaccess-ai .

# Run container
docker run -p 8501:8501 -p 8000:8000 rxaccess-ai

# Stop container
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose up --build
```

## 🔧 Configuration

### LLM Provider Setup

#### Option 1: Ollama (Local, Free)
```bash
# Install Ollama
# Visit: https://ollama.ai/

# Pull model
ollama pull llama3.1

# Start Ollama server
ollama serve

# Configure .env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434
```

#### Option 2: OpenAI (Cloud, Paid)
```bash
# Get API key from: https://platform.openai.com/

# Configure .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

#### Option 3: Groq (Cloud, Free Tier)
```bash
# Get API key from: https://console.groq.com/

# Configure .env
LLM_PROVIDER=groq
GROQ_API_KEY=your-key-here
```

### Tesseract Configuration

#### Windows
```env
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

#### Linux/macOS
```env
TESSERACT_PATH=/usr/bin/tesseract
# or
TESSERACT_PATH=/usr/local/bin/tesseract
```

## ▶️ Running the Application

### Streamlit App
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Run application
streamlit run streamlit_app/app.py
```

Access at: http://localhost:8501

### FastAPI Backend (Optional)
```bash
# Run backend server
uvicorn backend.main:app --reload --port 8000
```

Access API docs at: http://localhost:8000/docs

## ✅ Verification

### Check Installation
```bash
# Activate virtual environment
source venv/bin/activate

# Check Python packages
pip list | grep -E "streamlit|langchain|chromadb|xgboost"

# Check directories
ls -la data/
ls -la models/
ls -la logs/

# Check knowledge base
ls -la data/knowledge_base/

# Check vector store
ls -la data/chroma_db/
```

### Run Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_extraction.py -v

# Run with coverage
pytest --cov=src tests/
```

### Test OCR
```bash
# Test Tesseract
tesseract --version

# Test with sample image
python -c "from src.extraction.ocr_engine import OCREngine; print(OCREngine())"
```

### Test LLM Connection
```bash
# For Ollama
curl http://localhost:11434/api/tags

# Test in Python
python -c "from src.config import get_llm_config; print(get_llm_config())"
```

## 🐛 Troubleshooting

### Issue: Python Version Error
```bash
# Check version
python --version

# Use python3 if needed
python3 --version

# Update Python
# Visit: https://www.python.org/downloads/
```

### Issue: Tesseract Not Found
```bash
# Linux
sudo apt-get update
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download and install from:
# https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH
```

### Issue: Module Not Found
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: LLM Connection Failed
```bash
# For Ollama
# Check if Ollama is running
ollama list

# Start Ollama
ollama serve

# For OpenAI/Groq
# Check API key in .env
cat .env | grep API_KEY
```

### Issue: ChromaDB Error
```bash
# Delete and reinitialize
rm -rf data/chroma_db/
python scripts/init_system.py
```

### Issue: Port Already in Use
```bash
# Find process using port 8501
# Linux/macOS
lsof -i :8501

# Windows
netstat -ano | findstr :8501

# Kill process or use different port
streamlit run streamlit_app/app.py --server.port 8502
```

## 📊 System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 2 GB free space
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Storage**: 5+ GB free space
- **GPU**: Optional (for faster LLM inference)

## 🔄 Updating

### Update Code
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Reinitialize if needed
python scripts/init_system.py
```

### Update Models
```bash
# Retrain adherence model
python scripts/train_adherence_model.py

# Update Ollama model
ollama pull llama3.1
```

## 🗑️ Uninstallation

### Remove Virtual Environment
```bash
# Deactivate
deactivate

# Remove directory
rm -rf venv/
```

### Remove Data
```bash
# Remove generated data
rm -rf data/chroma_db/
rm -rf data/uploads/*
rm -rf models/*.pkl
rm -rf logs/*.log
```

### Complete Removal
```bash
# Remove entire project
cd ..
rm -rf rxaccess-ai/
```

## 📞 Getting Help

### Check Logs
```bash
# View main log
tail -f logs/rxaccess.log

# View error log
tail -f logs/errors.log
```

### Common Issues
1. **Import errors**: Activate virtual environment
2. **Tesseract errors**: Check installation and PATH
3. **LLM errors**: Verify API keys or Ollama status
4. **Port conflicts**: Use different port
5. **Memory errors**: Reduce batch size or use smaller model

### Resources
- **Documentation**: See README.md and docs/
- **Issues**: Check GitHub issues
- **Community**: Join discussions

## ✅ Installation Checklist

- [ ] Python 3.10+ installed
- [ ] Tesseract OCR installed
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] System initialized
- [ ] ML model trained
- [ ] Application runs successfully
- [ ] Tests pass

## 🎉 Success!

If you've completed all steps, you should be able to:
1. ✅ Run `streamlit run streamlit_app/app.py`
2. ✅ Access http://localhost:8501
3. ✅ Upload a prescription
4. ✅ Ask questions to the medical assistant
5. ✅ Generate PA forms
6. ✅ View adherence predictions

**Congratulations! RxAccess AI is ready to use!** 🚀
