# 🎮 Stack Sage Usage Guide

Your intelligent Magic: The Gathering rules companion is ready to use!

## 🚀 Quick Start

### 1. Activate your virtual environment
```bash
source backend/venv/bin/activate
```

### 2. Run Stack Sage
```bash
python stack_sage.py
```

Or:
```bash
python -m backend.cli.main
```

## 💬 How to Use

### Ask Questions
Simply type your question and press Enter:
```
🃏 Your question: What is the effect of Rest in Peace?
```

### Card Names
For best results, use quotes around card names:
```
🃏 Your question: How does "Dockside Extortionist" work with "Spark Double"?
```

### Commands
- `help` - Show help information
- `examples` - See example questions
- `clear` - Clear the screen
- `quit` or `exit` - Exit Stack Sage

## ✨ Features

- 🔍 **Dual Retrieval** - Combines Scryfall card data + Comprehensive Rules
- 🤖 **AI-Powered** - Uses GPT-4 for intelligent answers
- 📚 **Comprehensive** - Access to all MTG rules and 25,000+ cards
- 🎨 **Beautiful UI** - Rich terminal interface with colors and formatting

## 📝 Example Questions

1. "What is the effect of Rest in Peace?"
2. "How does Dockside Extortionist work with Spark Double?"
3. "What happens when a player loses the game?"
4. "How does the stack resolve?"
5. "Does Rest in Peace stop Unearth?"
6. "What is priority and how does it work?"

## 🔧 Troubleshooting

### No answer or poor quality?
- Make sure you're using quotes around card names
- Be specific in your question
- Try rephrasing

### Error about Qdrant?
- Make sure only one instance is running
- Restart the application

### Slow response?
- First query initializes the vector store (takes longer)
- Subsequent queries are faster

## 🎯 Tips for Best Results

1. **Be specific** - "How does X interact with Y?" is better than "How does X work?"
2. **Use quotes** - Always quote card names: "Lightning Bolt"
3. **Ask one thing** - Break complex questions into parts
4. **Check spelling** - Card names must match (Scryfall uses fuzzy matching)

Enjoy using Stack Sage! 🧙‍♂️✨

