import pandas as pd
import sqlite3
import math
import os
import plotly.graph_objects as go
from shiny import App, render, ui, reactive

# --- 1. 基礎設定 ---
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

# --- 2. UI 佈局 (相容 Shiny 0.4.0) ---
app_ui = ui.page_fluid(
    ui.h2("Dynamic Workflow Analysis", style="text-align: center; margin-top: 20px;"),
    ui.layout_sidebar(
        # 修正：使用 panel_sidebar
        ui.panel_sidebar(
            ui.input_select(
                "pgy_select", 
                "選擇 PGY 等級:", 
                choices=["Intern/PGY1", "PGY2", "PGY3", "PGY4", "PGY5"]
            ),
        ),
        # 修正：使用 panel_main
        ui.panel_main(
            ui.output_ui("plotly_html_output")
        ),
    ),
)

# --- 3. Server 後端邏輯 ---
def server(input, output, session):
    
    @reactive.calc
    def get_data():
        lvl = input.pgy_select()
        target_ids = [str(k) for k, v in pgy_map.items() if v == lvl]
        if not target_ids: return None

        conn = sqlite3.connect(db_path)
        # Python 3.7 相容語法
        query = "SELECT * FROM my_table WHERE prov_deid IN ({})".format(','.join(target_ids))
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty: return None
        df['duration_seconds'] = df['duration_seconds'].clip(upper=TIME_THRESHOLD)
        df['next_step'] = df.groupby('prov_deid')['metric_group_desc'].shift(-1)
        return df.dropna(subset=['next_step'])

    @output
    @render.ui
    def plotly_html_output():
        df = get_data()
        if df is None: return ui.markdown("### 資料庫中查無資料")

        # 指標計算
        node_metrics = df.groupby('metric_group_desc')['duration_seconds'].mean().reset_index()
        pgy_count = df['prov_deid'].nunique()
        edge_metrics = df.groupby(['metric_group_desc', 'next_step']).size().reset_index(name='count')
        edge_metrics['avg_freq'] = edge_metrics['count'] / pgy_count

        # 佈局 (修正 math.pi 與座標匹配)
        all_nodes = sorted(node_metrics['metric_group_desc'].unique())
        n = len(all_nodes)
        pos = {str(node): [math.cos(2*math.pi*i/n), math.sin(2*math.pi*i/n)] for i, node in enumerate(all_nodes)}

        fig = go.Figure()

        # 畫纖細連線 (Edges) - 已移除 tgt_key 錯誤
        for _, row in edge_metrics.iterrows():
            s, t = str(row['metric_group_desc']), str(row['next_step'])
            if s in pos and t in pos:
                fig.add_trace(go.Scatter(
                    x=[pos[s][0], pos[t][0]], y=[pos[s][1], pos[t][1]],
                    mode='lines',
                    line=dict(width=0.5 + row['avg_freq']*0.3, color='rgba(150,150,150,0.3)'),
                    hoverinfo='none', showlegend=False
                ))

        # 畫節點 (Nodes) - 藍色漸層 + 黑色邊框 + 固定大小
        fig.add_trace(go.Scatter(
            x=[pos[str(n_name)][0] for n_name in node_metrics['metric_group_desc']],
            y=[pos[str(n_name)][1] for n_name in node_metrics['metric_group_desc']],
            mode='markers+text',
            text=node_metrics['metric_group_desc'],
            textposition="top center",
            marker=dict(
                size=30, 
                color=node_metrics['duration_seconds'], 
                colorscale='Blues',
                line=dict(width=2, color='black'), 
                showscale=True
            ),
            showlegend=False
        ))

        fig.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=700,
            margin=dict(l=20, r=20, t=20, b=20)
        )

        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))

app = App(app_ui, server)