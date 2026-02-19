import pandas as pd
import sqlite3
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "data.db")
TIME_THRESHOLD = 300 

# PGY map
pgy_map = {
    1: 'PGY4', 7: 'PGY4', 8: 'PGY4', 9: 'PGY4', 10: 'PGY4', 12: 'PGY4',
    2: 'PGY5', 3: 'PGY5', 4: 'PGY5', 5: 'PGY5', 6: 'PGY5',
    11: 'PGY3', 15: 'PGY3', 16: 'PGY3', 17: 'PGY3', 18: 'PGY3',
    13: 'PGY2', 14: 'PGY2', 19: 'PGY2', 20: 'PGY2', 21: 'PGY2', 22: 'PGY2',
    23: 'Intern/PGY1', 24: 'Intern/PGY1', 25: 'Intern/PGY1', 
    26: 'Intern/PGY1', 27: 'Intern/PGY1', 28: 'Intern/PGY1'
}

def load_and_process_data():
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM my_table", conn)
    conn.close()

    df['pgy_detail'] = df['prov_deid'].map(pgy_map)
    
    # Separate into two groups
    def combine_groups(pgy):
        if pgy in ['Intern/PGY1', 'PGY2']:
            return 'PGY12'
        else:
            return 'PGY345'
            
    df['pgy_group'] = df['pgy_detail'].apply(combine_groups)
    df['duration_seconds'] = df['duration_seconds'].clip(upper=TIME_THRESHOLD)

    if 'next_step' not in df.columns:
        df['next_step'] = df.groupby('prov_deid')['metric_group_desc'].shift(-1)
    
    df = df.dropna(subset=['next_step'])
    return df

# def calculate_metrics(df):
#     node_metrics = df.groupby(['pgy_group', 'metric_group_desc'])['duration_seconds'].mean().reset_index()
#     edge_metrics = df.groupby(['pgy_group', 'metric_group_desc', 'next_step'])['duration_seconds'].mean().reset_index()
#     edge_metrics.columns = ['pgy_group', 'source', 'target', 'avg_duration']

#     # Z-score 基準：計算這兩大組之間的平均與標準差
#     global_edge_stats = edge_metrics.groupby(['source', 'target'])['avg_duration'].agg(['mean', 'std']).reset_index()
#     edge_metrics = edge_metrics.merge(global_edge_stats, on=['source', 'target'])
#     edge_metrics['z_score'] = (edge_metrics['avg_duration'] - edge_metrics['mean']) / edge_metrics['std']
#     edge_metrics['z_score'] = edge_metrics['z_score'].fillna(0)

#     return node_metrics, edge_metrics

# def add_graph_to_subplot(fig, col, group_name, node_metrics, edge_metrics, all_nodes, pos):
#     nodes = node_metrics[node_metrics['pgy_group'] == group_name]
#     edges = edge_metrics[edge_metrics['pgy_group'] == group_name]

#     for _, row in edges.iterrows():
#         x0, y0 = pos[row['source']]
#         x1, y1 = pos[row['target']]
#         offset = 0.06
        
#         # --- 情況 A: 一般有向路徑 (A -> B) ---
#         if row['source'] != row['target']:
#             dx, dy = x1 - x0, y1 - y0
#             dist = math.sqrt(dx**2 + dy**2)
#             nx, ny = -dy/dist * offset, dx/dist * offset
#             x0_p, y0_p, x1_p, y1_p = x0 + nx, y0 + ny, x1 + nx, y1 + ny
            
#             # 繪製直線路徑
#             fig.add_trace(go.Scatter(
#                 x=[x0_p, x1_p], y=[y0_p, y1_p],
#                 line=dict(width=max(1, 4 + row['z_score']*3), color='rgba(150, 150, 150, 0.5)'),
#                 hoverinfo='text',
#                 text=f"Group: {group_name}<br>{row['source']} -> {row['target']}<br>Avg: {row['avg_duration']:.1f}s<br>Z-score: {row['z_score']:.2f}",
#                 mode='lines', showlegend=False
#             ), row=1, col=col)

#             # 加上箭頭
#             fig.add_annotation(
#                 x=x1_p - (x1_p - x0_p) * 0.1, y=y1_p - (y1_p - y0_p) * 0.1,
#                 ax=x0_p, ay=y0_p, xref=f"x{col}", yref=f"y{col}", axref=f"x{col}", ayref=f"y{col}",
#                 showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=max(1, 2 + row['z_score']),
#                 arrowcolor='rgba(150, 150, 150, 0.7)'
#             )

#         # --- 情況 B: 自循環路徑 (A -> A) 繞一圈 ---
#         else:
#             # 定義環狀路徑的半徑與控制點
#             loop_size = 0.2  # 圓圈的大小
#             # 我們在節點位置的上方畫一個由 8 個點組成的圓形
#             t = np.linspace(0, 2*np.pi, 20)
#             # 讓圓圈稍微偏離中心，避免被節點本身擋住 (往節點外側推)
#             # 根據節點在圓周上的位置(pos)，決定圓圈噴出的方向
#             angle = math.atan2(y0, x0) 
#             loop_x = x0 + loop_size * np.cos(t) + math.cos(angle) * 0.15
#             loop_y = y0 + loop_size * np.sin(t) + math.sin(angle) * 0.15

#             fig.add_trace(go.Scatter(
#                 x=loop_x, y=loop_y,
#                 line=dict(width=max(1, 3 + row['z_score']*2), color='rgba(100, 100, 100, 0.4)'),
#                 hoverinfo='text',
#                 text=f"Self-loop: {row['source']}<br>Avg Stay: {row['avg_duration']:.1f}s",
#                 mode='lines', showlegend=False
#             ), row=1, col=col)
            
#             # 在圓圈上加一個小箭頭標示方向
#             fig.add_annotation(
#                 x=loop_x[10], y=loop_y[10], ax=loop_x[9], ay=loop_y[9],
#                 xref=f"x{col}", yref=f"y{col}", axref=f"x{col}", ayref=f"y{col}",
#                 showarrow=True, arrowhead=1, arrowsize=0.8, arrowcolor='rgba(100, 100, 100, 0.6)'
#             )
def calculate_metrics(df):
    # 1. 先計算每個 PGY 群組有多少人 (分母)
    pgy_counts = df.groupby('pgy_group')['prov_deid'].nunique().to_dict()

    # 2. 節點大小：維持平均停留時間 (秒)
    node_metrics = df.groupby(['pgy_group', 'metric_group_desc'])['duration_seconds'].mean().reset_index()
    
    # 3. 線條：計算「平均每人操作次數」
    # 先算總次數
    edge_metrics = df.groupby(['pgy_group', 'metric_group_desc', 'next_step']).size().reset_index(name='total_count')
    edge_metrics.columns = ['pgy_group', 'source', 'target', 'total_count']
    
    # 除以該組人數
    edge_metrics['avg_frequency'] = edge_metrics.apply(
        lambda row: row['total_count'] / pgy_counts[row['pgy_group']], axis=1
    )

    # --- Z-score 標準化邏輯 (改用頻率計算) ---
    global_edge_stats = edge_metrics.groupby(['source', 'target'])['avg_frequency'].agg(['mean', 'std']).reset_index()
    edge_metrics = edge_metrics.merge(global_edge_stats, on=['source', 'target'])
    
    # 計算 Z-score
    edge_metrics['z_score'] = (edge_metrics['avg_frequency'] - edge_metrics['mean']) / edge_metrics['std']
    edge_metrics['z_score'] = edge_metrics['z_score'].fillna(0)

    return node_metrics, edge_metrics

def add_graph_to_subplot(fig, col, group_name, node_metrics, edge_metrics, all_nodes, pos):
    nodes = node_metrics[node_metrics['pgy_group'] == group_name]
    edges = edge_metrics[edge_metrics['pgy_group'] == group_name]

    # 1. 為了確保兩圖顏色標準一致，計算全域的最大與最小值
    max_stay = node_metrics['duration_seconds'].max()
    min_stay = node_metrics['duration_seconds'].min()

    # --- 繪製連線 (Edges) 部分保持不變 ---
    for _, row in edges.iterrows():
        x0, y0 = pos[row['source']]
        x1, y1 = pos[row['target']]
        offset = 0.08
        if row['source'] != row['target']:
            dx, dy = x1 - x0, y1 - y0
            dist = math.sqrt(dx**2 + dy**2)
            nx, ny = -dy/dist * offset, dx/dist * offset
            x0_p, y0_p, x1_p, y1_p = x0 + nx, y0 + ny, x1 + nx, y1 + ny
            fig.add_trace(go.Scatter(
                x=[x0_p, x1_p], y=[y0_p, y1_p],
                line=dict(width=max(1, 3 + row['z_score']*3), color='rgba(180, 180, 180, 0.4)'),
                hoverinfo='text',
                text=f"{row['source']} -> {row['target']}",
                mode='lines', showlegend=False
            ), row=1, col=col)
        else:
            # 自循環路徑
            loop_size = 0.15
            t = np.linspace(0, 2*np.pi, 20)
            angle = math.atan2(y0, x0) 
            loop_x = x0 + loop_size * np.cos(t) + math.cos(angle) * 0.12
            loop_y = y0 + loop_size * np.sin(t) + math.sin(angle) * 0.12
            fig.add_trace(go.Scatter(
                x=loop_x, y=loop_y,
                line=dict(width=max(1, 2 + row['z_score']*2), color='rgba(180, 180, 180, 0.3)'),
                mode='lines', showlegend=False
            ), row=1, col=col)

    # 2. 繪製節點 (Nodes)：固定大小 + 藍色漸層
    fig.add_trace(go.Scatter(
        x=[pos[n][0] for n in nodes['metric_group_desc']],
        y=[pos[n][1] for n in nodes['metric_group_desc']],
        mode='markers+text',
        text=nodes['metric_group_desc'],
        textposition="top center",
        marker=dict(
            size=30,                # 所有節點固定大小
            color=nodes['duration_seconds'], # 顏色根據停留時間變化
            colorscale='Blues',     # 使用藍色漸層 (淺藍到深藍)
            cmin=min_stay,          # 強制設定顏色軸最小值
            cmax=max_stay,          # 強制設定顏色軸最大值
            showscale=(col == 2),   # 只在右邊圖表顯示顏色條
            colorbar=dict(
                title="Avg Stay (s)",
                x=1.02,
                thickness=15
            ),
            line=dict(width=1.5, color='black') # 白色邊框讓節點更清晰
        ),
        hoverinfo='text',
        hovertext=[f"Node: {n}<br>Avg Stay: {d:.1f}s" for n, d in zip(nodes['metric_group_desc'], nodes['duration_seconds'])],
        showlegend=False
    ), row=1, col=col)

if __name__ == "__main__":
    df = load_and_process_data()
    node_metrics, edge_metrics = calculate_metrics(df)
    
    all_nodes = sorted(node_metrics['metric_group_desc'].unique())
    pos = {node: [math.cos(2*math.pi*i/len(all_nodes)), math.sin(2*math.pi*i/len(all_nodes))] 
           for i, node in enumerate(all_nodes)}

    # 建立左右子圖
    fig = make_subplots(
        rows=1, cols=2, 
        subplot_titles=("Junior Group (Intern/PGY1/2)", "Senior Group (PGY3/4/5)"),
        specs=[[{"type": "scatter"}, {"type": "scatter"}]]
    )

    add_graph_to_subplot(fig, 1, 'PGY12', node_metrics, edge_metrics, all_nodes, pos)
    add_graph_to_subplot(fig, 2, 'PGY345', node_metrics, edge_metrics, all_nodes, pos)

    fig.update_layout(
        title_text="Workflow Comparison: Junior vs Senior (Z-score Scaled Edges)",
        height=700, width=1300,
        plot_bgcolor='white'
    )
    
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)

    fig.show()