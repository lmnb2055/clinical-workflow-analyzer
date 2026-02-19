import pandas as pd
import sqlite3
import math
import os
import plotly.graph_objects as go
from shiny import App, ui, reactive
from shinywidgets import output_widget, render_widget

# --- 基礎設定 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "data.db")
TIME_THRESHOLD = 300 

pgy_map = {
    1: 'PGY4', 7: 'PGY4', 8: 'PGY4', 9: 'PGY4', 10: 'PGY4', 12: 'PGY4',
    2: 'PGY5', 3: 'PGY5', 4: 'PGY5', 5: 'PGY5', 6: 'PGY5',
    11: 'PGY3', 15: 'PGY3', 16: 'PGY3', 17: 'PGY3', 18: 'PGY3',
    13: 'PGY2', 14: 'PGY2', 19: 'PGY2', 20: 'PGY2', 21: 'PGY2', 22: 'PGY2',
    23: 'Intern/PGY1', 24: 'Intern/PGY1', 25: 'Intern/PGY1', 
    26: 'Intern/PGY1', 27: 'Intern/PGY1', 28: 'Intern/PGY1'
}

# --- UI 介面 ---
app_ui = ui.page_fluid(
    ui.panel_title("EHR PGY Groups Workflow Analysis", "Workflow Study"),
    ui.layout_sidebar(
        ui.sidebar(
            # 1. PGY 多選
            ui.input_checkbox_group(
                "pgy_select", 
                "Select PGY Levels:", 
                choices=["Intern/PGY1", "PGY2", "PGY3", "PGY4", "PGY5"],
                selected=["Intern/PGY1"]
            ),
            ui.hr(), # 分隔線
            # 2. 是否為週末過濾 (假設資料庫 1 為週末, 0 為平日)
            ui.input_radio_buttons(
                "weekend_filter",
                "Day Type:",
                choices={"all": "All Days", "1": "Weekend Only", "0": "Weekday Only"},
                selected="all"
            ),
            # 3. 是否為非上班時間 (假設資料庫 1 為 Off-hour, 0 為 On-hour)
            ui.input_radio_buttons(
                "offhour_filter",
                "Work Hour:",
                choices={"all": "All Hours", "1": "Off-hours", "0": "Normal Hours"},
                selected="all"
            ),
            title="Filters"
        ),
        output_widget("workflow_plot")
    ),
)

# --- Server 後端邏輯 ---
def server(input, output, session):
    
    @reactive.calc
    def get_db_data():
        selected_levels = input.pgy_select()
        if not selected_levels:
            return None

        # 基礎 ID 篩選
        target_ids = [str(k) for k, v in pgy_map.items() if v in selected_levels]
        if not target_ids:
            return None

        # 構建 SQL 條件
        where_clauses = [f"prov_deid IN ({','.join(target_ids)})"]
        
        # 加入 Weekend 過濾
        if input.weekend_filter() != "all":
            where_clauses.append(f"is_weekend = {input.weekend_filter()}")
            
        # 加入 Off-hour 過濾
        if input.offhour_filter() != "all":
            where_clauses.append(f"is_offhour = {input.offhour_filter()}")

        # 組合 SQL
        final_query = f"SELECT * FROM my_table WHERE {' AND '.join(where_clauses)}"
        
        conn = sqlite3.connect(db_path)
        df = pd.read_sql(final_query, conn)
        conn.close()
        
        if df.empty:
            return None
            
        df['duration_seconds'] = df['duration_seconds'].clip(upper=TIME_THRESHOLD)
        df['next_step'] = df.groupby('prov_deid')['metric_group_desc'].shift(-1)
        return df.dropna(subset=['next_step'])

    @render_widget
    def workflow_plot():
        df = get_db_data()
        if df is None:
            return go.Figure().update_layout(title="No data found for selected filters")
            
        node_metrics = df.groupby('metric_group_desc')['duration_seconds'].mean().reset_index()
        pgy_count = df['prov_deid'].nunique()
        edge_metrics = df.groupby(['metric_group_desc', 'next_step']).size().reset_index(name='count')
        edge_metrics['avg_freq'] = edge_metrics['count'] / pgy_count

        all_nodes = sorted(node_metrics['metric_group_desc'].unique())
        n_nodes = len(all_nodes)
        pos = {str(node): [math.cos(2 * math.pi * i / n_nodes), math.sin(2 * math.pi * i / n_nodes)] 
               for i, node in enumerate(all_nodes)}

        fig = go.Figure()

        # 1. 畫極致纖細連線
        for _, row in edge_metrics.iterrows():
            src, tgt = str(row['metric_group_desc']), str(row['next_step'])
            if src in pos and tgt in pos:
                fig.add_trace(go.Scatter(
                    x=[pos[src][0], pos[tgt][0]], 
                    y=[pos[src][1], pos[tgt][1]],
                    mode='lines',
                    line=dict(width=0.3, color='rgba(180, 180, 180, 0.3)'),
                    hoverinfo='none', 
                    showlegend=False
                ))

        # 2. 畫節點
        fig.add_trace(go.Scatter(
            x=[pos[str(n)][0] for n in node_metrics['metric_group_desc']],
            y=[pos[str(n)][1] for n in node_metrics['metric_group_desc']],
            mode='markers+text',
            text=node_metrics['metric_group_desc'],
            textposition="top center",
            marker=dict(
                size=28,
                color=node_metrics['duration_seconds'],
                colorscale='Blues',
                line=dict(width=1.5, color='black'),
                showscale=True,
                colorbar=dict(title="Avg Stay (s)")
            ),
            hoverinfo='text',
            hovertext=[f"{n}<br>Stay: {d:.1f}s" for n, d in zip(node_metrics['metric_group_desc'], node_metrics['duration_seconds'])],
            showlegend=False
        ))

        fig.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=800,
            margin=dict(l=40, r=40, t=40, b=40)
        )

        return fig

app = App(app_ui, server)