import streamlit as st
import plotly.express as px
import pandas as pd

def render_hygiene_receiving(hygiene_df: pd.DataFrame, start_dt, end_dt):
    st.header("🧼 Chef Hygiene Checklists")
    
    # Filter Data
    h_df = hygiene_df[(hygiene_df['Timestamp'] >= start_dt) & (hygiene_df['Timestamp'] <= end_dt)].copy()
    
    if h_df.empty:
        st.warning("No Personal Hygiene data available.")
    else:
        st.subheader("👨‍🍳 Chef Compliance Summary")
        
        h1, h2, h3 = st.columns(3)
        with h1:
            st.metric("Total Hygiene Logs", len(h_df))
        with h2:
            avg_comp = h_df['Compliance %'].mean()
            st.metric("Average Overall Compliance", f"{avg_comp:.1f}%")
        with h3:
            # Anyone with < 100% is considered to have a violation
            violations = len(h_df[h_df['Compliance %'] < 100])
            st.metric("Logs w/ Violations", violations)
            
        st.markdown("---")
        
        st.markdown("### Compliance by Chef")
        st.write("Grouped view to see which candidates/chefs perform well or fail compliance checks.")
        
        # Group by Chef
        chef_comp = h_df.groupby('Chef Name')[['Yes Count', 'No Count']].sum().reset_index()
        # Calculate their total hygiene failure rate
        chef_comp['Total Checks'] = chef_comp['Yes Count'] + chef_comp['No Count']
        chef_comp['Failure Rate %'] = (chef_comp['No Count'] / chef_comp['Total Checks']) * 100
        
        c_col1, c_col2 = st.columns([2, 1])
        with c_col1:
            fig_chef = px.bar(chef_comp.sort_values('Yes Count', ascending=False), 
                              x='Chef Name', y=['Yes Count', 'No Count'],
                              barmode='stack', title="Hygiene Check Results per Chef",
                              color_discrete_map={'Yes Count': '#10b981', 'No Count': '#ef4444'})
            st.plotly_chart(fig_chef, use_container_width=True)
            
        with c_col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.dataframe(chef_comp[['Chef Name', 'Failure Rate %']].sort_values('Failure Rate %', ascending=False).style.format({'Failure Rate %': '{:.1f}%'}), use_container_width=True)
