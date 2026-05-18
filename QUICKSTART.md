# RxAccess AI - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.10 or higher
- Tesseract OCR installed
- (Optional) Ollama for local LLM

### Step 1: Install Dependencies

```bash
# Clone repository
git clone <repository-url>
cd rxaccess-ai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Install Tesseract OCR

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# For quick start, use default Ollama settings
```

### Step 4: Initialize System

```bash
# Initialize knowledge base and vector store
python scripts/init_system.py

# (Optional) Train adherence model
python scripts/train_adherence_model.py

# (Optional) Generate sample prescriptions
python scripts/generate_synthetic_data.py
```

### Step 5: Run Application

```bash
# Start Streamlit app
streamlit run streamlit_app/app.py
```

The application will open in your browser at `http://localhost:8501`

## 🐳 Docker Quick Start

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:8501
```

## 📝 First Steps

1. **Upload a Prescription**
   - Go to "Upload Prescription" page
   - Upload an image or PDF
   - View extracted data

2. **Ask Questions**
   - Navigate to "Medical Assistant"
   - Ask about medications, side effects, interactions

3. **Check Prior Authorization**
   - Go to "Prior Authorization"
   - Review PA form and approval likelihood

4. **Explore Affordability**
   - Visit "Affordability" page
   - Compare insurance vs cash-pay options

5. **View Adherence Insights**
   - Check "Adherence Intelligence"
   - See risk prediction and interventions

## 🔧 Troubleshooting

### Tesseract Not Found
```bash
# Set path in .env
TESSERACT_PATH=/usr/local/bin/tesseract
```

### LLM Connection Issues
```bash
# For Ollama, ensure it's running:
ollama serve

# Or switch to OpenAI/Groq in .env:
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
```

### Import Errors
```bash
# Ensure you're in the virtual environment
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📚 Next Steps

- Read full [README.md](README.md)
- Review [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Explore [API Documentation](docs/API.md)
- Check [Deployment Guide](docs/DEPLOYMENT.md)

## 💡 Tips

- Use synthetic prescriptions in `data/synthetic/prescriptions/` for testing
- Check logs in `logs/` directory for debugging
- Vector store persists in `data/chroma_db/`
- Models are saved in `models/` directory

## 🆘 Getting Help

- Check logs: `tail -f logs/rxaccess.log`
- Run tests: `pytest tests/ -v`
- Review error messages in Streamlit UI

## ⚠️ Important Notes

- This is a prototype for demonstration purposes
- Not intended for actual medical use
- Always consult healthcare professionals
- Synthetic data is for testing only
