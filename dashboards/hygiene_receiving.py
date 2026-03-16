import streamlit as st
import plotly.express as px
import pandas as pd

def render_hygiene_receiving(hygiene_df: pd.DataFrame, receiving_df: pd.DataFrame, start_dt, end_dt):
    st.header("🧼 Hygiene & Supplier Replenishment")
    
    # Filter Data
    h_df = hygiene_df[(hygiene_df['Timestamp'] >= start_dt) & (hygiene_df['Timestamp'] <= end_dt)].copy()
    r_df = receiving_df[(receiving_df['Timestamp'] >= start_dt) & (receiving_df['Timestamp'] <= end_dt)].copy()
    
    tab1, tab2 = st.tabs(["Supplier Deliveries (Receiving Log)", "Chef Personal Hygiene"])
    
    # -----------------------------
    # TAB 1: SUPPLIER RECEIVING LOG
    # -----------------------------
    with tab1:
        if r_df.empty:
            st.warning("No Receiving Log data available.")
        else:
            st.subheader("📦 Supplier Delivery Overview")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total Items Received", len(r_df))
            with c2:
                # Count distinct suppliers
                st.metric("Unique Suppliers", r_df['Supplier'].nunique())
            with c3:
                # Rejected items
                rejected = len(r_df[r_df['Status'] == 'Rejected'])
                st.metric("Rejected Deliveries", rejected)
                
            st.markdown("---")
            
            # Supplier Holistic View
            st.markdown("### Supplier Frequency & Product Volume")
            st.write("Understand how many products each supplier delivers, and how frequently.")
            
            # Group by supplier count to see volume
            sup_vol = r_df.groupby('Supplier').size().reset_index(name='Products Delivered').sort_values('Products Delivered', ascending=False)
            
            fig_sup_vol = px.bar(sup_vol, x='Supplier', y='Products Delivered', color='Products Delivered',
                                 title="Total Volume Delivered per Supplier", color_continuous_scale="Purpor")
            st.plotly_chart(fig_sup_vol, use_container_width=True)
            
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                st.markdown("#### Delivery Frequency")
                st.write("Unique delivery dates per supplier.")
                # We extract date for frequency
                r_df['Date'] = r_df['Timestamp'].dt.date
                sup_freq = r_df.groupby('Supplier')['Date'].nunique().reset_index(name='Days Delivered').sort_values('Days Delivered', ascending=False)
                
                fig_freq = px.bar(sup_freq, x='Supplier', y='Days Delivered', color='Days Delivered',
                                  color_continuous_scale="Teal")
                st.plotly_chart(fig_freq, use_container_width=True)
                
            with col_s2:
                st.markdown("#### Supplier Compliance Ratio")
                st.write("Accepted vs Rejected item ratio per supplier.")
                status_df = r_df.groupby(['Supplier', 'Status']).size().reset_index(name='Count')
                fig_status = px.bar(status_df, x='Supplier', y='Count', color='Status', 
                                    barmode='group', color_discrete_map={'Accepted': '#10b981', 'Rejected': '#ef4444'})
                st.plotly_chart(fig_status, use_container_width=True)

            st.markdown("---")
            
            st.markdown("### Temperature Compliance Matrix")
            st.write("Analyze acceptable receiving standards (Truck vs Product temperature correlation).")
            
            # Scatter plot acting as a pseudo heatmap/matrix mapping Truck against Product temp
            clean_temps = r_df.dropna(subset=['Truck Temp', 'Product Temp'])
            fig_scatter = px.scatter(clean_temps, x='Truck Temp', y='Product Temp', color='Status',
                                     hover_data=['Supplier', 'Product'], 
                                     color_discrete_map={'Accepted': '#10b981', 'Rejected': '#ef4444'},
                                     title="Truck Temperature vs. Product Temperature (°C)")
            st.plotly_chart(fig_scatter, use_container_width=True)

    # -----------------------------
    # TAB 2: PERSONAL HYGIENE
    # -----------------------------
    with tab2:
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
