# 🏦 Bank Statement Parser Agent

This project is an *AI-powered Bank Statement Parser Agent* built with *LangGraph* and *Groq LLMs*.  
It automatically:
1. Plans parsing logic based on the target bank format  
2. Generates custom parsing code  
3. Runs pytest to validate against reference data  
4. Self-corrects parsing errors (≤3 attempts)  
5. Produces a clean, structured pandas.DataFrame for downstream analysis  

---

## ⚡ Quick Start (4 Steps)

1. *Clone the Repository*
   ```bash
   git clone <repo_url>
   cd carbon-ai-agent
2. *Install Dependencies*
   pip install -r requirements.txt
3. *Set Environment Variable*
   export GROQ_API_KEY="your_api_key"   # Linux/Mac
   setx GROQ_API_KEY "your_api_key"     # Windows PowerShell
4. *Run the Agent*
   python agent.py --target icici


*📂 Project Structure*

carbon-ai-agent/
│── agent.py # Main entry point
│── requirements.txt # Python dependencies
│── custom_parsers/ # Auto-generated bank-specific parsers
│── tests/ # Pytest test cases for validation
└── data/ # Sample bank statements


*🧭 Agent Architecture*

The agent follows a Plan → Act → Validate → Refine loop. A LangGraph state machine manages execution, where each node represents a stage:
  *Planner Node:* Analyzes the target bank and outlines parsing logic.
  *CodeGen Node:* Writes a custom parser (e.g., custom_parsers/icici_parser.py).
  *Test Node:* Executes pytest to compare parsed output with reference data.
  *Refiner Node:* Fixes code automatically upon failure, with up to 3 retries.
 *End Node:* Returns the final parsed DataFrame.
This loop ensures robustness and automation with minimal manual intervention.




<img width="906" height="443" alt="Screenshot 2025-09-17 124229" src="https://github.com/user-attachments/assets/6afca942-4eea-4cb7-b0af-002f738f6535" /
