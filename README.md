This is the "face" of your project. It explains what the app does and how to run it. Save this as README.md:

Markdown
# EHR PGY Groups Workflow Analysis Tool

An interactive dashboard built with **Shiny for Python** to visualize and analyze Electronic Health Record (EHR) workflow patterns. This tool helps researchers understand how different PGY (Post-Graduate Year) levels interact with systems across various shifts and days.

## 🌟 Features

- **Interactive Network Graph**: Visualizes the sequence of EHR actions using Plotly.
- **Dynamic Filtering**:
  - **PGY Level**: Select multiple levels to compare or aggregate data.
  - **Day Type**: Filter by Weekdays or Weekends (`is_weekend`).
  - **Work Hours**: Filter by Normal Hours or Off-hours (`is_offhour`).
- **Visual Analytics**:
  - **Node Color**: Represents the average stay duration (darker blue = longer duration).
  - **Edge Thickness**: Represents the frequency of transitions between actions.

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/lmnb2055/clinical-workflow-analyzer.git](https://github.com/lmnb2055/clinical-workflow-analyzer.git)
cd clinical-workflow-analyzer
2. Set Up Virtual Environment
Bash
python -m venv venv_new
source venv_new/bin/activate  # macOS/Linux
# venv_new\Scripts\activate   # Windows
3. Install Dependencies
Bash
pip install -r requirements.txt
4. Database Setup
Ensure a SQLite database named data.db is present in the directory with a table named my_table containing the following columns: prov_deid, metric_group_desc, duration_seconds, is_weekend, and is_offhour.

5. Run the App
Bash
shiny run --reload shiny_app.py

requirements.txt: List of Python dependencies.

.gitignore: Prevents large environment files and databases from being uploaded.