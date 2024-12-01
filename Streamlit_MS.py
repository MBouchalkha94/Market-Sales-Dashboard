# Import required libraries
import pandas as pd
import numpy as np
import datetime as dt
import streamlit as st
import plotly.express as px
import calendar  # For month names

# Set the page configuration for Streamlit
st.set_page_config(
    page_title="Market Sales Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject CSS for a scrollable sidebar
st.markdown(
    """
    <style>
    /* Make the entire sidebar scrollable */
    [data-testid="stSidebar"] {
        overflow-y: auto; /* Enable vertical scrolling */
        max-height: 90vh; /* Adjust height to fit the screen */
        padding-right: 10px; /* Add some padding for better appearance */
    }

    /* Optional: Hide the scrollbar for cleaner appearance */
    [data-testid="stSidebar"]::-webkit-scrollbar {
        display: none; /* For Chrome, Safari, and Edge */
    }

    [data-testid="stSidebar"] {
        -ms-overflow-style: none; /* For Internet Explorer and Edge */
        scrollbar-width: none; /* For Firefox */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar: Data Upload
st.sidebar.header("📁 Data Upload")
uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV File",
    type=["csv"],
    key="Upload a CSV file containing sales data with required columns like 'Quantity', 'Unit price', and 'Tax 5%'."
)

# Load the dataset
@st.cache_data
def load_data(uploaded_file=None):
    try:
        if uploaded_file is not None:
            # Read the uploaded file
            data = pd.read_csv(uploaded_file)
        else:
            st.error("No file uploaded. Please upload a CSV file.")
            return None

        # Calculate Total Amount
        data['Total Amount'] = data['Quantity'] * data['Unit price'] + data['Tax 5%']

        # Add synthetic Date if missing
        if 'Date' not in data.columns:
            start_date = dt.date(2023, 1, 1)
            end_date = dt.date(2023, 12, 31)
            np.random.seed(42)
            date_range = [
                start_date + dt.timedelta(days=np.random.randint(0, (end_date - start_date).days))
                for _ in range(len(data))
            ]
            data['Date'] = date_range
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')

        # Ensure Time column is converted to datetime.time
        if 'Time' in data.columns:
            data['Time'] = pd.to_datetime(data['Time'], format='%H:%M:%S', errors='coerce').dt.time
        else:
            np.random.seed(42)
            random_times = [
                dt.time(np.random.randint(8, 21), np.random.randint(0, 60)) for _ in range(len(data))
            ]
            data['Time'] = random_times

        # Extract Month and Hour
        data['Month'] = data['Date'].dt.month
        data['Hour'] = data['Time'].apply(lambda x: x.hour if pd.notnull(x) else None)

        # Add synthetic Payment column if missing
        if 'Payment' not in data.columns:
            np.random.seed(42)
            data['Payment'] = np.random.choice(['Cash', 'Credit Card', 'E-Wallet'], size=len(data))

        return data

    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return None


# Sidebar Filters: Date Range
with st.sidebar.expander("📅 Date Range Filters", expanded=False):
    st.subheader("Date Range")
    start_date = st.date_input(
        "Start Date", 
        data["Date"].min(), 
        key="Filter data starting from this date."
    )
    end_date = st.date_input(
        "End Date", 
        data["Date"].max(), 
        key="Filter data up to this date."
    )
    if start_date > end_date:
        st.error("Start Date cannot be after End Date.")

# Sidebar Filters: Quantity and Invoice Total Range
with st.sidebar.expander("📈 Quantity and Invoice Filters", expanded=False):
    st.subheader("Quantity Range")
    min_quantity, max_quantity = st.slider(
        "Select Quantity Range",
        min_value=int(data["Quantity"].min()),
        max_value=int(data["Quantity"].max()),
        value=(int(data["Quantity"].min()), int(data["Quantity"].max())),
        key="Filter data based on the range of quantities sold."
    )

    st.subheader("Invoice Total Range")
    min_total, max_total = st.slider(
        "Select Invoice Total Range",
        min_value=int(data["Total Amount"].min()),
        max_value=int(data["Total Amount"].max()),
        value=(int(data["Total Amount"].min()), int(data["Total Amount"].max())),
        key="Filter data based on the range of invoice totals."
    )

# Sidebar Filters: Time
with st.sidebar.expander("⏰ Time Filters", expanded=False):
    st.subheader("Day of the Week")
    weekday_filter = st.multiselect(
        "Select Day of the Week",
        options=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        default=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        key="Filter data by the day of the week."
    )

    st.subheader("Time of Day")
    time_of_day_filter = st.radio(
        "Select Time of Day",
        options=["All", "Morning", "Afternoon", "Evening"],
        key="Filter data by time of the day."
    )



# Apply Filters
filtered_data = data[
    (data["City"].isin(city_filter)) &
    (data["Gender"].isin(gender_filter)) &
    (data["Customer type"].isin(customer_type_filter)) &
    (data["Product line"].isin(product_line_filter)) &
    (data["Payment"].isin(payment_filter)) &
    (data["Quantity"].between(min_quantity, max_quantity)) &
    (data["Total Amount"].between(min_total, max_total)) &
    (data["Date"] >= pd.to_datetime(start_date)) &
    (data["Date"] <= pd.to_datetime(end_date)) &
    (data["Date"].dt.day_name().isin(weekday_filter))
]

if time_of_day_filter != "All":
    time_ranges = {"Morning": (8, 12), "Afternoon": (12, 17), "Evening": (17, 21)}
    start_hour, end_hour = time_ranges[time_of_day_filter]
    filtered_data = filtered_data[filtered_data["Hour"].between(start_hour, end_hour)]


# KPIs Section
st.markdown("### Key Performance Indicators")
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

with kpi_col1:
    st.metric("🛒 Total Sales (items)", int(filtered_data["Quantity"].sum()))
with kpi_col2:
    st.metric("📄 Total Transactions", filtered_data["Invoice ID"].nunique())
with kpi_col3:
    avg_sales = filtered_data["Quantity"].sum() / filtered_data["Invoice ID"].nunique()
    st.metric("💳 Avg. Sales per Transaction", f"{avg_sales:.2f}")

# Visualization Section
st.markdown("### Sales Insights")

with st.container():
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        city_sales = filtered_data.groupby('City')['Quantity'].sum().reset_index()
        fig_city = px.bar(
            city_sales,
            x='City', y='Quantity',
            title="Total Sales by City",
            text='Quantity',
            color='City',
            color_discrete_map={"Mandalay": "#1f77b4", "Naypyitaw": "#ff7f0e", "Yangon": "#2ca02c"}
        )
        fig_city.update_layout(title=dict(x=0.5), xaxis_title="City", yaxis_title="Total Sales")
        st.plotly_chart(fig_city)

    with row1_col2:
        product_sales = filtered_data.groupby('Product line')['Quantity'].sum().reset_index()
        fig_product = px.bar(
            product_sales, x='Product line', y='Quantity',
            title="Total Sales by Product Line",
            text='Quantity',
            color='Quantity', color_continuous_scale="Viridis"
        )
        fig_product.update_layout(title=dict(x=0.5), xaxis_title="Product Line", yaxis_title="Total Sales Quantity")
        st.plotly_chart(fig_product)

with st.container():
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        monthly_sales = filtered_data.groupby('Month')['Quantity'].sum().reset_index()
        monthly_sales['Month'] = monthly_sales['Month'].map(lambda x: calendar.month_name[x])
        fig_monthly = px.line(
            monthly_sales, x='Month', y='Quantity',
            title="Monthly Sales Trend",
            markers=True
        )
        st.plotly_chart(fig_monthly)

    with row2_col2:
        hourly_sales = filtered_data.groupby('Hour')['Quantity'].sum().reset_index()
        fig_hourly = px.bar(
            hourly_sales, x='Hour', y='Quantity',
            title="Hourly Sales Trend",
            text='Quantity'
        )
        st.plotly_chart(fig_hourly)

# Demographics
st.markdown("### Customer Demographics")
col1, col2 = st.columns(2)

with col1:
    gender_sales = filtered_data.groupby('Gender')['Quantity'].sum().reset_index()
    fig_gender = px.pie(
        gender_sales, values='Quantity', names='Gender',
        title="Sales by Gender", hole=0.4,
        color='Gender', color_discrete_map={"Male": "#1f77b4", "Female": "#faa2d5"}
    )
    st.plotly_chart(fig_gender)

with col2:
    customer_type_sales = filtered_data.groupby('Customer type')['Quantity'].sum().reset_index()
    fig_customer_type = px.pie(
        customer_type_sales, values='Quantity', names='Customer type',
        title="Sales by Customer Type", hole=0.4,
        color='Customer type', color_discrete_map={"Member": "#69af4b", "Normal": "#ffb84d"}
    )
    st.plotly_chart(fig_customer_type)

# Display Raw Data
st.markdown("### Raw Data")

# Allow column selection
columns_to_display = st.multiselect(
    "Select Columns to Display",
    options=filtered_data.columns,
    default=filtered_data.columns  # Default to displaying all columns
)

# Format numeric columns
formatted_data = filtered_data.copy()
numeric_columns = ['Unit price', 'Total Amount', 'Tax 5%']
for col in numeric_columns:
    if col in formatted_data.columns:
        formatted_data[col] = formatted_data[col].apply(lambda x: f"{x:,.2f}")  # Format numbers to 2 decimal places

# Format Time column to HH:MM format if present
if 'Time' in formatted_data.columns:
    formatted_data['Time'] = formatted_data['Time'].apply(lambda x: x.strftime('%H:%M') if pd.notnull(x) else None)

# Display the formatted dataframe with selectable columns
if len(columns_to_display) > 0:
    st.dataframe(formatted_data[columns_to_display], use_container_width=True)
else:
    st.warning("Please select at least one column to display.")
