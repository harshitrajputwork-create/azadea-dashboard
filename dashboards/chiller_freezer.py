import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def render_chiller_freezer(df: pd.DataFrame, start_dt, end_dt):
    st.header("🧊 Chiller & Freezer Temperature Log")
    
    # Filter by global dates
    df = df[(df['Timestamp'] >= start_dt) & (df['Timestamp'] <= end_dt)].copy()
    
    if df.empty:
        st.warning("No data available for the selected date range.")
        return
        
    # Order the chronological 'Child Name' identifiers 
    def parse_time_for_sort(t_str):
        try:
            return pd.to_datetime(t_str, format='%I:%M %p').time()
        except:
            return pd.to_datetime('00:00:00').time()
            
    unique_child_names = df['Child Name'].dropna().unique()
    sorted_child_names = sorted(unique_child_names, key=parse_time_for_sort)
    
    # High-level Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Temperature Logs", len(df))
    with col2:
        avg_chiller_temp = df[df['Type'] == 'Chiller']['Temperature'].mean()
        st.metric("Avg Chiller Temp", f"{avg_chiller_temp:.1f} °C" if pd.notna(avg_chiller_temp) else "N/A")
    with col3:
        avg_freezer_temp = df[df['Type'] == 'Freezer']['Temperature'].mean()
        st.metric("Avg Freezer Temp", f"{avg_freezer_temp:.1f} °C" if pd.notna(avg_freezer_temp) else "N/A")
        
    st.markdown("---")
    
    # Heatmaps for Chillers and Freezers
    st.subheader("Daily Shift Heatmaps")
    st.write("Visualizing the average recorded temperature for each asset by shift.")
    
    h_col1, h_col2 = st.columns(2)
    
    with h_col1:
        chiller_df = df[df['Type'] == 'Chiller']
        if not chiller_df.empty:
            agg_chiller = chiller_df.groupby(['Asset Name', 'Child Name'])['Temperature'].mean().reset_index()
            pivot_chiller = agg_chiller.pivot(index='Child Name', columns='Asset Name', values='Temperature')
            valid_idx = [c for c in sorted_child_names if c in pivot_chiller.index]
            pivot_chiller = pivot_chiller.reindex(valid_idx)
            
            fig_c = px.imshow(pivot_chiller, text_auto=".1f", aspect="auto",
                              color_continuous_scale="Blues", 
                              title="Chillers Heatmap (°C)")
            st.plotly_chart(fig_c, use_container_width=True)
            
    with h_col2:
        freezer_df = df[df['Type'] == 'Freezer']
        if not freezer_df.empty:
            agg_freezer = freezer_df.groupby(['Asset Name', 'Child Name'])['Temperature'].mean().reset_index()
            pivot_freezer = agg_freezer.pivot(index='Child Name', columns='Asset Name', values='Temperature')
            valid_idx = [c for c in sorted_child_names if c in pivot_freezer.index]
            pivot_freezer = pivot_freezer.reindex(valid_idx)
            
            fig_f = px.imshow(pivot_freezer, text_auto=".1f", aspect="auto",
                              color_continuous_scale="PuBu", 
                              title="Freezers Heatmap (°C)")
            st.plotly_chart(fig_f, use_container_width=True)

    st.markdown("---")
    
    # Trendlines over time
    st.subheader("Temperature Trend Lines")
    
    tab1, tab2 = st.tabs(["Overall Trends", "Isolate Equipment Item"])
    
    with tab1:
        st.write("Average temperature across all active equipment over time.")
        
        # Group by day and type
        trend_df = df.copy()
        trend_df['Date'] = trend_df['Timestamp'].dt.date
        daily_trend = trend_df.groupby(['Date', 'Type'])['Temperature'].mean().reset_index()
        
        fig_trend = px.line(daily_trend, x='Date', y='Temperature', color='Type', markers=True,
                            title="Daily Average Temperature Trend",
                            color_discrete_map={'Chiller': '#2563eb', 'Freezer': '#0891b2'})
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with tab2:
        st.write("Select a specific asset to view its individual trend timeline.")
        assets = df['Asset Name'].unique()
        selected_asset = st.selectbox("Select Asset to Isolate", assets)
        
        isolated_df = df[df['Asset Name'] == selected_asset].sort_values('Timestamp')
        isolated_df['Date'] = isolated_df['Timestamp'].dt.date
        
        chart_type = st.radio("Chart Type", ["Heatmap", "Line Chart"], horizontal=True)
        
        if chart_type == "Heatmap":
            # Heatmap 1: Date vs Child Name
            st.write(f"**Temperature Timeline per Period ({selected_asset})**")
            pivot_date_time = isolated_df.pivot_table(index='Child Name', columns='Date', values='Temperature', aggfunc='mean')
            
            # Create a parallel text pivot for hover
            # Just take the first manager string or join unique ones per cell
            text_pivot = isolated_df.pivot_table(index='Child Name', columns='Date', values='Checked By', aggfunc=lambda x: ', '.join(pd.Series.unique(x)))
            
            valid_idx = [c for c in sorted_child_names if c in pivot_date_time.index]
            pivot_date_time = pivot_date_time.reindex(valid_idx)
            if not text_pivot.empty:
                text_pivot = text_pivot.reindex(valid_idx)
                
            fig_iso_heat = go.Figure(data=go.Heatmap(
                z=pivot_date_time.values,
                x=pivot_date_time.columns,
                y=pivot_date_time.index,
                text=text_pivot.values if not text_pivot.empty else None,
                hovertemplate="Date: %{x}<br>Time: %{y}<br>Temp: %{z:.1f} °C<br>Checked By: %{text}<extra></extra>",
                colorscale="Oranges",
            ))
            fig_iso_heat.update_layout(title=f"{selected_asset} Operations Breakdown")
            st.plotly_chart(fig_iso_heat, use_container_width=True)
            
            st.markdown("---")
            
            # Heatmap 2: Date vs Person (Checked By)
            st.write("**Staff Logging Matrix**")
            pivot_person_date = isolated_df.pivot_table(index='Checked By', columns='Date', values='Temperature', aggfunc='mean')
            fig_person_heat = px.imshow(pivot_person_date, text_auto=".1f", aspect="auto", 
                                        color_continuous_scale="Purpor", title="Average Asset Temp Recorded by Staff Member (°C)")
            st.plotly_chart(fig_person_heat, use_container_width=True)
            
        else:
            fig_iso = px.line(isolated_df, x='Timestamp', y='Temperature', markers=True,
                              title=f"Trendline for {selected_asset}",
                              color_discrete_sequence=['#ea580c'])
            st.plotly_chart(fig_iso, use_container_width=True)

    st.markdown("---")
    
    # Completion Frequency
    st.subheader("Completion Frequency")
    st.write("How frequently each log is filled by the responsible staff.")
    
    freq_df = df.groupby(['Asset Name']).size().reset_index(name='Logs Completed').sort_values('Logs Completed', ascending=False)
    
    fig_bar = px.bar(freq_df, x='Asset Name', y='Logs Completed', color='Logs Completed',
                     color_continuous_scale='Mint', title="Log Submissions per Asset")
    st.plotly_chart(fig_bar, use_container_width=True)
