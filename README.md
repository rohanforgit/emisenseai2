# EMI Sense AI – AI-Powered Loan Optimization Platform

Traditional financial calculators tell you your EMI. **EMI Sense AI** helps you optimize your debt structure, minimize cumulative interest, and accelerate your path to absolute debt freedom.

## Core Features
*   **Advisory Overview Dashboard:** Custom KPIs showing base EMI, total interest, total payment, loan health, and years to debt free.
*   **What-If Scenarios Simulation:** Model financial fluctuations (job loss, income growth, rate hikes) and compare investing extra funds vs. prepaying loan principal.
*   **Modular Acceleration Tools:** Simulate EMI increases, recurring annual prepayments, or immediate lump-sum contributions.
*   **Interactive Visualizations:** Plotly amortization curves, debt-free milestone lines, and health indicators.
*   **Professional PDF Export:** Clean ReportLab reports capturing baseline metrics, optimization tables, health scores, and AI recommendations.
*   **AI Coach:** Powered by OpenAI and Gemini (`gemini-2.5-flash` default) to dynamically critique and guide your debt payoff strategy.

## Tech Stack
*   **Frontend:** Streamlit
*   **Data Analysis:** Pandas, NumPy
*   **Visualizations:** Plotly, Matplotlib
*   **PDF Compiler:** ReportLab
*   **LLM integration:** OpenAI SDK

---

## Local Setup & Run

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/rohanforgit/emisenseai2.git
    cd emisenseai2
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Up API Key:**
    Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_gemini_api_key
    ```

4.  **Run Application:**
    ```bash
    streamlit run app.py
    ```

5.  **Run Tests:**
    ```bash
    python3 test_calculations.py
    ```
