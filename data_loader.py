import pandas as pd
import numpy as np

def load_chiller_freezer_data(filepath):
    """
    Loads and shapes the Chiller and Freezer data.
    The original CSV has 10 columns for Freezers (Temperature, Checked By)
    and 10 columns for Chillers (Temperature, Checked By).
    
    We melt this wide format into a long format so we can analyze trendlines easily.
    """
    df = pd.read_csv(filepath)
    
    # Parse date flexibly to handle multiple formats
    # E.g. "26 February 2026  08:12 PM" OR "26-02-2026 08:12"
    df['Started At'] = pd.to_datetime(df['Started At'], dayfirst=True, errors='coerce')
    
    melted_rows = []
    
    for _, row in df.iterrows():
        submission_id = row['Submission Id']
        timestamp = row['Started At']
        store = row.get('Store', 'Unknown Store')
        manager = row.get('Submitted By', 'Unknown')
        child_name = str(row.get('Child Name', 'Unknown')).strip()
        
        # Freezers
        for i in range(1, 11):
            temp_col = f'Temperature Freezer {i}'
            checker_col = f'Checked By Freezer {i}'
            
            if temp_col in row and pd.notna(row[temp_col]) and str(row[temp_col]).strip() != '-':
                try:
                    # Sometimes people type strings or leave empty
                    temp_val = float(str(row[temp_col]).strip())
                    melted_rows.append({
                        'Submission Id': submission_id,
                        'Store': store,
                        'Timestamp': timestamp,
                        'Type': 'Freezer',
                        'Asset Name': f'Freezer {i}',
                        'Temperature': temp_val,
                        'Checked By': str(row.get(checker_col, 'Unknown')).strip(),
                        'Manager': manager,
                        'Child Name': child_name
                    })
                except ValueError:
                    pass
        
        # Chillers
        for i in range(1, 11):
            temp_col = f'Temperature Chiller {i}'
            checker_col = f'Checked By Chiller {i}'
            
            if temp_col in row and pd.notna(row[temp_col]) and str(row[temp_col]).strip() != '-':
                try:
                    temp_val = float(str(row[temp_col]).strip())
                    melted_rows.append({
                        'Submission Id': submission_id,
                        'Store': store,
                        'Timestamp': timestamp,
                        'Type': 'Chiller',
                        'Asset Name': f'Chiller {i}',
                        'Temperature': temp_val,
                        'Checked By': str(row.get(checker_col, 'Unknown')).strip(),
                        'Manager': manager,
                        'Child Name': child_name
                    })
                except ValueError:
                    pass
                    
    df_long = pd.DataFrame(melted_rows)
    if df_long.empty:
        df_long = pd.DataFrame(columns=['Submission Id', 'Store', 'Timestamp', 'Type', 'Asset Name', 'Temperature', 'Checked By', 'Manager', 'Child Name'])
    return df_long


def _parse_dynamic_cells(raw_string, num_columns):
    """
    Helper to parse dynamic questions that output strings like:
    "item1,val,val,val,,,,,"
    """
    if pd.isna(raw_string):
        return []
    
    # Split by comma but handle potential quotes (though simpler here to just split and group)
    # The format seems to pack consecutive rows in one string: "diwas,No,No... cyrus,Yes,Yes..."
    # Actually, the CSV shows each SUBMISSION has a single giant string with extra commas.
    # E.g: "diwas,No,No,No,No,No,No,No,No,No,,,,,,,,,,"
    parts = str(raw_string).split(',')
    
    # Remove trailing empty commas cleanly
    valid_parts = [p.strip() for p in parts if p.strip() or p == '']
    
    rows = []
    # Chunk them up
    for i in range(0, len(valid_parts), num_columns):
        chunk = valid_parts[i:i+num_columns]
        if len(chunk) > 1 and any(chunk[1:]): # If there's at least one value
             # ensure it matches num_columns by padding just in case
             chunk += [''] * (num_columns - len(chunk))
             if chunk[0] != '': # Must have a name/item
                rows.append(chunk)

    return rows


def load_hygiene_data(filepath):
    """
    Loads hygiene checklist data. The actual checks are packed into Comment-0100001
    Format: Name, 9 Yes/No questions.
    """
    df = pd.read_csv(filepath)
    df['Started At'] = pd.to_datetime(df['Started At'], dayfirst=True, errors='coerce')
    
    # The columns for hygiene are 1 Name + 9 Questions = 10 cols
    parsed_data = []
    
    for _, row in df.iterrows():
        submission_id = row['Submission Id']
        timestamp = row['Started At']
        
        # Auto-detect the correct column: prefer 'Personal Hygiene Checks' then fallback to 'Comment-0100001'
        raw_str = ''
        for col_name in ['Personal Hygiene Checks', 'Comment-0100001']:
            if col_name in row.index and pd.notna(row[col_name]) and str(row[col_name]).strip() not in ('', '-'):
                raw_str = row[col_name]
                break
        
        chunks = _parse_dynamic_cells(raw_str, 10)
        for chunk in chunks:
            name = chunk[0].strip()
            # If the chunk has actual data and is not just a trailing comma block
            if name:
                responses = chunk[1:10]
                # Count 'Yes'
                yes_count = sum(1 for r in responses if str(r).strip().lower() == 'yes')
                no_count = sum(1 for r in responses if str(r).strip().lower() == 'no')
                
                parsed_data.append({
                    'Submission Id': submission_id,
                    'Timestamp': timestamp,
                    'Chef Name': name,
                    'Yes Count': yes_count,
                    'No Count': no_count,
                    'Total Checked': yes_count + no_count,
                    'Compliance %': (yes_count / (yes_count + no_count) * 100) if (yes_count + no_count) > 0 else 0
                })
                
    df_out = pd.DataFrame(parsed_data)
    if df_out.empty:
        df_out = pd.DataFrame(columns=['Submission Id', 'Timestamp', 'Chef Name', 'Yes Count', 'No Count', 'Total Checked', 'Compliance %'])
    return df_out


def load_receiving_log_data(filepath):
    """
    Parses the Receiving Log Sheet.
    The dynamic string is inside `Comment-0100005`.
    Format per item: Date(or Id), Supplier Name, Truck Temp, Truck Cond, Product Name, Product Temp, Quantity, Expiry Date, Status, Remarks, Received By.
    That is 11 columns per chunk.
    """
    df = pd.read_csv(filepath)
    df['Started At'] = pd.to_datetime(df['Started At'], dayfirst=True, errors='coerce')
    
    parsed_data = []
    
    col_count = 11
    
    for _, row in df.iterrows():
        submission_id = row['Submission Id']
        timestamp = row['Started At']
        
        # Auto-detect the correct column for the receiving log data
        raw_str = ''
        for col_name in ['Receiving Log Sheet.1', 'Comment-0100005']:
            if col_name in row.index and pd.notna(row[col_name]) and str(row[col_name]).strip() not in ('', '-'):
                raw_str = row[col_name]
                break
        chunks = _parse_dynamic_cells(raw_str, col_count)
        
        # Carry over supplier name if it's implicitly grouped (blank in CSV usually means same supplier)
        current_supplier = "Unknown Supplier"
        current_truck_temp = None
        
        for chunk in chunks:
            # chunk offsets
            # 0: Id/Date
            # 1: Supplier
            # 2: Truck Temp
            # 3: Truck Cond
            # 4: Product
            # 5: Product Temp
            # 6: Qty
            # 7: Expiry
            # 8: Status (Accepted/Rejected)
            # 9: Remarks
            # 10: Received By
            
            sup = chunk[1].strip()
            if sup:
                current_supplier = sup
                try: 
                    current_truck_temp = float(chunk[2]) if chunk[2].strip() and chunk[2] != '-' else np.nan
                except: 
                    current_truck_temp = np.nan
            
            product = chunk[4].strip()
            if not product:
                continue # Skip empty items
                
            try:
                prod_temp = float(chunk[5]) if chunk[5].strip() and chunk[5] != '-' else np.nan
            except:
                prod_temp = np.nan
                
            qty_str = chunk[6].strip()
            status = chunk[8].strip()
            receiver = chunk[10].strip() if len(chunk) > 10 else 'Unknown'
            
            if status.lower() not in ['accepted', 'rejected']:
                status = 'Accepted' # Default assumption if malformed
            
            parsed_data.append({
                'Submission Id': submission_id,
                'Timestamp': timestamp,
                'Supplier': current_supplier,
                'Truck Temp': current_truck_temp,
                'Product': product,
                'Product Temp': prod_temp,
                'Quantity': qty_str,
                'Status': status.capitalize()
            })
            
    df_out = pd.DataFrame(parsed_data)
    if df_out.empty:
        df_out = pd.DataFrame(columns=['Submission Id', 'Timestamp', 'Supplier', 'Truck Temp', 'Product', 'Product Temp', 'Quantity', 'Status'])
    return df_out


def load_manager_checklists(opening_path, mid_path, closing_path):
    """
    Loads all 3 manager checklists and standardizes them into a single timeline DF.
    """
    op_df = pd.read_csv(opening_path)
    mid_df = pd.read_csv(mid_path)
    cl_df = pd.read_csv(closing_path)
    
    # Add Shift label
    op_df['Shift'] = 'Opening'
    mid_df['Shift'] = 'Mid-Shift'
    cl_df['Shift'] = 'Closing'
    
    df_all = pd.concat([op_df, mid_df, cl_df], ignore_index=True)
    df_all['Started At'] = pd.to_datetime(df_all['Started At'], dayfirst=True, errors='coerce')
    
    # We mainly need Submission Id, Started At, Shift, Compliance, Store.
    res = df_all[['Submission Id', 'Shift', 'Started At', 'Compliance', 'Store', 'Submitted By', 'Total score']].copy()
    
    # To determine daily compliance drops, we need the "Date" from timestamp
    res['Date'] = res['Started At'].dt.date
    
    return res
