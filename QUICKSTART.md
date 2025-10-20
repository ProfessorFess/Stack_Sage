# ⚡ Quick Start Guide

Get Stack Sage running in 3 simple steps!

## 1️⃣ Set Your OpenAI API Key

```bash
cd backend
echo "OPENAI_API_KEY=your_actual_api_key_here" > .env
```

> Replace `your_actual_api_key_here` with your real OpenAI API key from https://platform.openai.com/api-keys

## 2️⃣ Start the Backend

**Option A: Using the startup script** (easiest)
```bash
chmod +x start_backend.sh
./start_backend.sh
```

**Option B: Manual start**
```bash
source backend/venv/bin/activate
python backend/api/server.py
```

✅ Backend running at **http://localhost:8000**

## 3️⃣ Start the Frontend (New Terminal)

**Option A: Using the startup script** (easiest)
```bash
chmod +x start_frontend.sh
./start_frontend.sh
```

**Option B: Manual start**
```bash
cd frontend
npm install  # First time only
npm run dev
```

✅ Frontend running at **http://localhost:5173**

## 🎉 Done!

Open **http://localhost:5173** in your browser and start asking questions about MTG rules!

---

## 📖 Example Questions

Try these to get started:

1. **Card Effects**
   - "What is the effect of Rest in Peace?"
   - "How does Dockside Extortionist work?"

2. **Card Interactions**
   - "How does Dockside Extortionist work with Spark Double?"
   - "Does Rest in Peace stop Unearth?"

3. **Rules Questions**
   - "How does the stack resolve?"
   - "What is priority and how does it work?"
   - "What happens when a player loses the game?"

4. **Format Legality**
   - "Is Black Lotus legal in Commander?"
   - "Is Sol Ring banned in any format?"

5. **Card Search**
   - "Find red 3-mana creatures in Standard"
   - "What blue counterspells are legal in Modern?"

---

## 🛠️ Troubleshooting

**"API is offline"** in the web interface
- Make sure the backend is running on port 8000
- Check the backend terminal for errors

**"OpenAI API key not found"**
- Create a `.env` file in the `backend/` directory
- Add your API key: `OPENAI_API_KEY=sk-...`

**"Module not found" errors**
- Activate the virtual environment: `source backend/venv/bin/activate`

**Frontend won't start**
- Run `npm install` in the frontend directory
- Make sure you have Node.js 18+ installed

---

For detailed documentation, see **[RUNNING.md](RUNNING.md)**

