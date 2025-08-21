import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("Store-Wise Fill Rate Dashboard")

# Hardcoded list of top 50 stores (location names only for filtering)
top_50_stores = [
    "University Road 2 Near Tambowan More Peshawar",
    "Centaurus Mall Islamabad",
    "F-10 Markaz Islamabad",
    "Awami Trade Center Karachi Company Islamabad",
    "Giga Mall Islamabad",
    "PWD Housing -2 Near Punjab C&C Rawalpindi",
    "Kashmir Road Saddar Rawalpindi",
    "Bank Road Opp. Barket Plaza Rawalpindi",
    "Bank Road near Singapore Plaza Rawalpindi",
    "Satellite Town -2 Children Park Rawalpindi",
    "Satellite Town -3 Commercial Market Rawalpindi",
    "Kutchehry Road Umar Plaza Gujrat",
    "University Road Near ChenOne Tower Sargodha",
    "Opposite Kings Mall Gujranwala",
    "Jaan Heights Jail Road Gujranwala",
    "Vanica Chowk Hafizabad",
    "Ghanta Ghar Chowk Sialkot Cantt",
    "Ghanta Ghar Chowk-2 Sialkot Cantt",
    "V-Mall Sialkot Cantt",
    "Shahrah-e-Quaid-e-Azam Lahore",
    "Gulshan-e-Ravi Lahore",
    "Jhanzeb Block Allama Iqbal Town Lahore",
    "Karim Block Lahore",
    "Wapda Town Round About Lahore",
    "Emporium Mall Atrium Lahore",
    "Bahria Town Lahore",
    "Model Town Link Road Lahore",
    "MM Alam Road Lahore",
    "Y-Block - 2 DHA Lahore",
    "Packages Mall - 1 Lahore",
    "Saddar Road -2 Dubai Chowk Cantt Lahore",
    "Megastore Shalimar Link Road Lahore",
    "Jinnah Colony Gulberg Faisalabad",
    "D. Ground -3 Near KFC Faisalabad",
    "Harianwala Chowk Peoples Colony Faisalabad",
    "Kohinoor Faisalabad",
    "Thana Bazar Arifwala",
    "Girls College Road Sahiwal",
    "High Street Sahiwal",
    "Gol Bagh Gulgasht Colony Multan",
    "Aziz Bhatti Shaheed Road Multan Cantt",
    "Farid Gate Bahawalpur",
    "Autobhan Prime Hyderabad",
    "Lucky One Mall F.B Area Karachi",
    "Sharah -e- Liaquat Quetta",
    "North Walk North Nazimabad Karachi",
    "Clifton Schon Circle Karachi",
    "Prime Arcade Bahadurabad Karachi",
    "Tariq Road -2 Rehmania Masjid Karachi",
    "Tariq Road -3 PECHS Karachi"
]

# Function to read uploaded file
def read_file(uploaded_file):
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            return pd.read_excel(uploaded_file)
    return None

st.subheader("Planned Report")
planned_file = st.file_uploader("Upload Planned file (required)", type=['csv', 'xlsx'])

# Uploaders for stock reports
st.subheader("Stock Reports")
women_stock_file = st.file_uploader("Upload Women stock report", type=['csv', 'xlsx'])
men_stock_file = st.file_uploader("Upload Men stock report", type=['csv', 'xlsx'])
boys_stock_file = st.file_uploader("Upload Boys stock report", type=['csv', 'xlsx'])
girls_stock_file = st.file_uploader("Upload Girls stock report", type=['csv', 'xlsx'])

# Uploaders for sales reports
st.subheader("Sales Reports")
women_sales_file = st.file_uploader("Upload Women sales report", type=['csv', 'xlsx'])
men_sales_file = st.file_uploader("Upload Men sales report", type=['csv', 'xlsx'])
boys_sales_file = st.file_uploader("Upload Boys sales report", type=['csv', 'xlsx'])
girls_sales_file = st.file_uploader("Upload Girls sales report", type=['csv', 'xlsx'])

if planned_file is None:
    st.warning("Please upload the Planned file to proceed.")
else:
    # Read planned and extract the single column
    planned_df = read_file(planned_file)
    if 'PLANNED_ITEMS' not in planned_df.columns:
        st.error("Planned file must contain a 'PLANNED_ITEMS' column.")
    else:
        planned_items = set(planned_df['PLANNED_ITEMS'].astype(str).str.strip().str.upper())
        st.write("Total Planned Items:", len(planned_items))

    # Function to process sales report
    def process_sales(sales_df, category):
        if sales_df is None:
            return None
        
        # Handle column name variations
        location_col = 'Location Name' if 'Location Name' in sales_df.columns else 'LOCATION_NAME'
        size_col = 'SIZE' if 'SIZE' in sales_df.columns else 'Size'
        qty_col = 'Qty' if 'Qty' in sales_df.columns else 'QTY'
        
        # Create ItemKey based on category
        if category in ['boys', 'girls']:
            sales_df['Class'] = sales_df['Class'].str.upper() if 'Class' in sales_df.columns else sales_df['CLASS'].str.upper()
            sales_df['ItemKey'] = (sales_df['Class'] + ':' + 
                                   sales_df['Item Parent Description'].astype(str).str.strip().str.upper() + ':' +
                                   sales_df['COLOR'].astype(str).str.strip().str.upper())
        else:
            sales_df['ItemKey'] = (sales_df['Item Parent Description'].astype(str).str.strip().str.upper() + ':' +
                                   sales_df['COLOR'].astype(str).str.strip().str.upper())
        
        # Filter to only items in planned
        sales_df = sales_df[sales_df['ItemKey'].isin(planned_items)]
        
        if sales_df.empty:
            return None
        
        # Convert Qty to numeric
        sales_df[qty_col] = pd.to_numeric(sales_df[qty_col], errors='coerce').fillna(0)
        
        # Convert Size to string for consistent data type and handle float decimals
        sales_df[size_col] = sales_df[size_col].astype(str).str.replace('.0', '').str.strip()
        
        # Group by ItemKey, Location, and Size to get total sales
        sales_summary = sales_df.groupby(['ItemKey', location_col, size_col])[qty_col].sum().reset_index()
        sales_summary.columns = ['ItemKey', 'LOCATION_NAME', 'Size', 'PRS']
        sales_summary['Category'] = category.capitalize()
        
        return sales_summary

    # Function to process a stock report (modified to include inventory data)
    def process_stock(stock_df, category, sales_summary=None):
        if stock_df is None:
            return None, None
        
        st.write(f"Planned Items - {category.capitalize()}: {len(planned_items)}")
        
        # Create ItemKey based on category
        if category in ['boys', 'girls']:
            stock_df['CLASS_NAME'] = stock_df['CLASS_NAME'].str.upper()
            stock_df['ItemKey'] = (stock_df['CLASS_NAME'] + ':' + 
                                   stock_df['ITEM_PARENT_DESC'].astype(str).str.strip().str.upper() + ':' +
                                   stock_df['DIFF_DESC'].astype(str).str.strip().str.upper())
        else:
            stock_df['ItemKey'] = (stock_df['ITEM_PARENT_DESC'].astype(str).str.strip().str.upper() + ':' +
                                   stock_df['DIFF_DESC'].astype(str).str.strip().str.upper())
        
        # Filter to only items in planned
        stock_df = stock_df[stock_df['ItemKey'].isin(planned_items)]
        
        matched_items = set(stock_df['ItemKey'].unique())
        unmatched = planned_items - matched_items
        
        if stock_df.empty:
            return None, None
        
        # Convert SOH and TOTAL_SOH to numeric, coercing errors to NaN
        stock_df['SOH'] = pd.to_numeric(stock_df['SOH'], errors='coerce')
        stock_df['TOTAL_SOH'] = pd.to_numeric(stock_df['TOTAL_SOH'], errors='coerce')
        
        # Extract size from ITEM_DESC and convert to string for consistent data type
        stock_df['Size'] = stock_df['ITEM_DESC'].apply(lambda x: x.split(':')[-1] if isinstance(x, str) and ':' in x else '').astype(str).str.replace('.0', '').str.strip()
        
        # Get total unique sizes per ItemKey (union across all stores)
        total_sizes = stock_df.groupby('ItemKey')['Size'].apply(lambda x: len(set(x))).to_dict()
        
        # Filter to available stock (SOH > 0)
        avail_df = stock_df[stock_df['SOH'] > 0]
        
        # Count unique available sizes per ItemKey and store
        avail_counts = avail_df.groupby(['ItemKey', 'LOCATION_NAME'])['Size'].apply(lambda x: len(set(x))).reset_index(name='AvailSizes')
        
        # Map total sizes
        avail_counts['TotalSizes'] = avail_counts['ItemKey'].map(total_sizes)
        
        # Calculate fill rate as percentage
        avail_counts['FillRate'] = (avail_counts['AvailSizes'] / avail_counts['TotalSizes']) * 100
        
        # Add category
        avail_counts['Category'] = category.capitalize()
        
        # Create inventory summary (ItemKey, Location, Size, INV)
        inventory_summary = stock_df.groupby(['ItemKey', 'LOCATION_NAME', 'Size'])['TOTAL_SOH'].sum().reset_index()
        inventory_summary.columns = ['ItemKey', 'LOCATION_NAME', 'Size', 'INV']
        inventory_summary['Category'] = category.capitalize()
        
        return avail_counts, inventory_summary
    
    # Process all uploaded stock files and sales files
    all_results = []
    all_sales_data = []
    all_inventory_data = []
    
    file_pairs = [
        (women_stock_file, women_sales_file, 'women'),
        (men_stock_file, men_sales_file, 'men'),
        (boys_stock_file, boys_sales_file, 'boys'),
        (girls_stock_file, girls_sales_file, 'girls')
    ]
    
    for stock_file, sales_file, cat in file_pairs:
        # Process sales data
        sales_summary = process_sales(read_file(sales_file), cat)
        if sales_summary is not None:
            all_sales_data.append(sales_summary)
        
        # Process stock data
        fill_result, inventory_summary = process_stock(read_file(stock_file), cat, sales_summary)
        if fill_result is not None:
            all_results.append(fill_result)
        if inventory_summary is not None:
            all_inventory_data.append(inventory_summary)
    
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        
        # Combine sales and inventory data if available
        combined_data = None
        if all_sales_data and all_inventory_data:
            all_sales = pd.concat(all_sales_data, ignore_index=True)
            all_inventory = pd.concat(all_inventory_data, ignore_index=True)
            
            # Merge sales and inventory data
            combined_data = pd.merge(
                all_sales, 
                all_inventory, 
                on=['ItemKey', 'LOCATION_NAME', 'Size', 'Category'], 
                how='outer'
            ).fillna(0)
        
        # Add a filter for ItemKey
        item_filter = st.text_input("Search ItemKey", "")
        filtered_df = final_df[final_df['ItemKey'].str.contains(item_filter, case=False, na=False)] if item_filter else final_df
        
        # Add view mode selection
        view_mode = st.radio("View Mode", ["All Locations", "Top 50", "Remaining Stores"])
        
        # Display the results with expandable sections by ItemKey
        st.subheader("Item-Wise Fill Rates Across Locations")
        for item in sorted(filtered_df['ItemKey'].unique()):
            with st.expander(f"Item: {item}"):
                item_data = filtered_df[filtered_df['ItemKey'] == item].copy()
                
                # Apply location filter
                if view_mode == "Top 50":
                    item_data = item_data[item_data['LOCATION_NAME'].isin(top_50_stores)]
                elif view_mode == "Remaining Stores":
                    item_data = item_data[~item_data['LOCATION_NAME'].isin(top_50_stores)]
                
                if not item_data.empty:
                    # Prepare data for single table display
                    display_data = item_data[['Category', 'LOCATION_NAME', 'AvailSizes', 'TotalSizes', 'FillRate']].copy()
                    
                    # Add size-wise data if available
                    if combined_data is not None:
                        item_combined = combined_data[combined_data['ItemKey'] == item].copy()
                        
                        # Apply same location filter
                        if view_mode == "Top 50":
                            item_combined = item_combined[item_combined['LOCATION_NAME'].isin(top_50_stores)]
                        elif view_mode == "Remaining Stores":
                            item_combined = item_combined[~item_combined['LOCATION_NAME'].isin(top_50_stores)]
                        
                        if not item_combined.empty:
                            # Get all unique sizes for this item and sort them
                            sizes = sorted(item_combined['Size'].unique(), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else float('inf'), x))
                            
                            # Create pivot tables for PRS and INV
                            prs_pivot = item_combined.pivot_table(
                                values='PRS', 
                                index=['LOCATION_NAME'], 
                                columns='Size', 
                                fill_value=0,
                                aggfunc='sum'
                            )
                            
                            inv_pivot = item_combined.pivot_table(
                                values='INV', 
                                index=['LOCATION_NAME'], 
                                columns='Size', 
                                fill_value=0,
                                aggfunc='sum'
                            )
                            
                            # Merge the size data with display_data
                            for size in sizes:
                                # Add PRS column
                                prs_col = f"{size}_PRS"
                                display_data[prs_col] = display_data['LOCATION_NAME'].map(
                                    prs_pivot[size] if size in prs_pivot.columns else {}
                                ).fillna(0).astype(int)
                                
                                # Add INV column
                                inv_col = f"{size}_INV"
                                display_data[inv_col] = display_data['LOCATION_NAME'].map(
                                    inv_pivot[size] if size in inv_pivot.columns else {}
                                ).fillna(0).astype(int)
                            
                            # Create MultiIndex columns
                            base_columns = [('Basic Info', 'Category'), ('Basic Info', 'Store'), 
                                          ('Basic Info', 'Available Sizes'), ('Basic Info', 'Total Sizes'), 
                                          ('Basic Info', 'Fill Rate %')]
                            
                            size_columns = []
                            for size in sizes:
                                size_columns.extend([
                                    (f'Size {size}', 'PRS'),
                                    (f'Size {size}', 'INV')
                                ])
                            
                            all_columns = base_columns + size_columns
                            
                            # Prepare data with proper column order
                            base_data = display_data[['Category', 'LOCATION_NAME', 'AvailSizes', 'TotalSizes', 'FillRate']].copy()
                            base_data['FillRate'] = base_data['FillRate'].round(1).astype(str) + '%'
                            
                            size_data = display_data[[f"{size}_{metric}" for size in sizes for metric in ['PRS', 'INV']]].copy()
                            
                            final_data = pd.concat([base_data, size_data], axis=1)
                            final_data.columns = pd.MultiIndex.from_tuples(all_columns)
                            
                            st.dataframe(final_data, use_container_width=True)
                        else:
                            # Show only basic fill rate data if no combined data for this item
                            display_data['Fill Rate %'] = display_data['FillRate'].round(1).astype(str) + '%'
                            st.dataframe(display_data[['Category', 'LOCATION_NAME', 'AvailSizes', 'TotalSizes', 'Fill Rate %']].rename(columns={'LOCATION_NAME': 'Store', 'AvailSizes': 'Available Sizes', 'TotalSizes': 'Total Sizes'}))
                    else:
                        # Show only basic fill rate data if no sales/inventory data
                        display_data['Fill Rate %'] = display_data['FillRate'].round(1).astype(str) + '%'
                        st.dataframe(display_data[['Category', 'LOCATION_NAME', 'AvailSizes', 'TotalSizes', 'Fill Rate %']].rename(columns={'LOCATION_NAME': 'Store', 'AvailSizes': 'Available Sizes', 'TotalSizes': 'Total Sizes'}))
        
        # Optional: Download button
        csv = final_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results as CSV", data=csv, file_name="fill_rates.csv", mime="text/csv")
        
        # Download combined data if available
        if combined_data is not None:
            combined_csv = combined_data.to_csv(index=False).encode('utf-8')
            st.download_button("Download Sales & Inventory Data as CSV", data=combined_csv, file_name="sales_inventory_data.csv", mime="text/csv")
    else:
        st.info("No stock reports uploaded or no matching items found.")