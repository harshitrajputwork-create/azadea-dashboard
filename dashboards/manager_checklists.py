import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def render_manager_checklists(df: pd.DataFrame, start_dt, end_dt):
    st.header("📋 Manager Checklists (Opening, Mid, Closing)")
    
    # Filter Data
    df = df[(df['Started At'] >= start_dt) & (df['Started At'] <= end_dt)].copy()
    
    if df.empty:
        st.warning("No Manager Checklist data available.")
        return
        
    st.markdown("### Submission Drop-off Tracker")
    st.write("Tracks submission frequency drops across the day to highlight exactly where compliance falls off (e.g., Opening vs Closing).")
    
    # Calculate drops
    shift_counts = df.groupby('Shift').size().reindex(['Opening', 'Mid-Shift', 'Closing']).fillna(0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Morning Checklists (Expected: Highest)", int(shift_counts.get('Opening', 0)))
    with col2:
        st.metric("Mid-Shift Checklists", int(shift_counts.get('Mid-Shift', 0)))
    with col3:
        st.metric("Closing Checklists", int(shift_counts.get('Closing', 0)))
        
    st.markdown("---")
    
    # Funnel Chart
    fig_funnel = go.Figure(go.Funnel(
        y=shift_counts.index,
        x=shift_counts.values,
        textinfo="value+percent initial",
        marker={"color": ["#14b8a6", "#f59e0b", "#ef4444"]}
    ))
    fig_funnel.update_layout(title="Submission Funnel (Opening ➔ Mid ➔ Closing)")
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### Drill-Down Details")
    st.write("Explore low-level details of submissions to identify specific managers or dates where compliance was missed.")
    
    # Make a pivot table showing Dates vs Shifts
    pivot_df = df.pivot_table(index='Date', columns='Shift', values='Submission Id', aggfunc='count', fill_value=0)
    # Reindex columns
    expected_cols = ['Opening', 'Mid-Shift', 'Closing']
    for c in expected_cols:
        if c not in pivot_df.columns:
            pivot_df[c] = 0
            
    pivot_df = pivot_df[expected_cols].sort_index(ascending=False)
    
    col_d1, col_d2 = st.columns([2, 1])
    
    with col_d1:
        st.write("#### Daily Compliance Matrix")
        # style mapping: >0 green, 0 red
        def highlight_missed(val):
            color = 'rgba(239, 68, 68, 0.3)' if val == 0 else 'rgba(16, 185, 129, 0.2)'
            return f'background-color: {color}'
            
        st.dataframe(pivot_df.style.applymap(highlight_missed), use_container_width=True)
        
    with col_d2:
        st.write("#### Submitted By (Manager Volume)")
        mgr_vol = df.groupby('Submitted By').size().reset_index(name='Total Submissions').sort_values('Total Submissions', ascending=False)
        st.dataframe(mgr_vol, use_container_width=True, hide_index=True)
        
    st.markdown("---")
    st.markdown("### Daily Trend Line")
    
    daily_shifts = df.groupby(['Date', 'Shift']).size().reset_index(name='Count')
    fig_line = px.line(daily_shifts, x='Date', y='Count', color='Shift', markers=True, 
                       title="Checklists Submitted Over Time",
                       category_orders={'Shift': ['Opening', 'Mid-Shift', 'Closing']})
    st.plotly_chart(fig_line, use_container_width=True)
