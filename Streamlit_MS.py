# Import required libraries
import pandas as pd # For data manipulation and analysis.
import numpy as np # For numerical operations and handling arrays.
import datetime as dt #  For working with dates and times.
import streamlit as st # For creating interactive web applications.
import plotly.express as px # For creating visually appealing, interactive visualizations.
import calendar  # For month names

# Set the page configuration for 
st.set_page_config(
    page_title="Market Sales Dashboard",
    layout="wide"
)

# Define the file path
file_path = r'archive/supermarket_sales new.csv'

# Load the dataset
@st.cache
def load_data():
    data = pd.read_csv(file_path)
    data['Total Amount'] = data['Quantity'] * data['Unit price'] + data['Tax 5%']
    
    # Add a synthetic Date column if it doesn't exist
    if 'Date' not in data.columns:
        start_date = dt.date(2023, 1, 1)
        end_date = dt.date(2023, 12, 31)
        np.random.seed(42)
        date_range = [
            start_date + dt.timedelta(days=np.random.randint(0, (end_date - start_date).days))
            for _ in range(len(data))
        ]
        data['Date'] = date_range

    # Convert the Date column to datetime format
    data['Date'] = pd.to_datetime(data['Date'])

    # Add a synthetic Time column if it doesn't exist
    if 'Time' not in data.columns:
        np.random.seed(42)
        random_times = [
            dt.time(np.random.randint(8, 21), np.random.randint(0, 60)) for _ in range(len(data))
        ]
        data['Time'] = random_times

    # Extract Month and Hour for analysis
    data['Month'] = data['Date'].dt.month
    data['Hour'] = data['Time'].apply(lambda x: x.hour)
    
    # Add a synthetic Payment column if it doesn't exist
    if 'Payment' not in data.columns:
        np.random.seed(42)
        data['Payment'] = np.random.choice(['Cash', 'Credit Card', 'E-Wallet'], size=len(data))

    return data

# Load data
data = load_data()

# Sidebar filters
st.sidebar.header("Filters")
branch_filter = st.sidebar.multiselect("Select Branch", options=data["Branch"].unique(), default=data["Branch"].unique())
gender_filter = st.sidebar.multiselect("Select Gender", options=data["Gender"].unique(), default=data["Gender"].unique())
customer_type_filter = st.sidebar.multiselect("Select Customer Type", options=data["Customer type"].unique(), default=data["Customer type"].unique())

# City Filter
city_filter = st.sidebar.multiselect("Select City", options=data["City"].unique(), default=data["City"].unique())

# Product Line Filter
product_line_filter = st.sidebar.multiselect("Select Product Line", options=data["Product line"].unique(), default=data["Product line"].unique())

# Payment Method Filter
payment_filter = st.sidebar.multiselect("Select Payment Method", options=data["Payment"].unique(), default=data["Payment"].unique())

# Separate Start and End Date Filters
st.sidebar.subheader("Date Range Filters")
start_date = st.sidebar.date_input("Start Date", data['Date'].min())
end_date = st.sidebar.date_input("End Date", data['Date'].max())

# Validate that the start date is not after the end date
if start_date > end_date:
    st.sidebar.error("Error: Start Date must be earlier than End Date")

st.sidebar.subheader("Quantity and Invoice Total Range Filters")
min_quantity, max_quantity = st.sidebar.slider(
    "Select Quantity Range",
    min_value=int(data["Quantity"].min()),
    max_value=int(data["Quantity"].max()),
    value=(int(data["Quantity"].min()), int(data["Quantity"].max()))
)

min_total, max_total = st.sidebar.slider(
    "Select Invoice Total Range",
    min_value=int(data["Total Amount"].min()),
    max_value=int(data["Total Amount"].max()),
    value=(int(data["Total Amount"].min()), int(data["Total Amount"].max()))
)

st.sidebar.subheader("Time Filters")
weekday_filter = st.sidebar.multiselect(
    "Select Day of the Week", 
    options=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], 
    default=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
)
time_of_day_filter = st.sidebar.radio(
    "Select Time of Day",
    options=["All", "Morning", "Afternoon", "Evening"]
)

# Apply the filters
filtered_data = data[
    (data["Branch"].isin(branch_filter)) &
    (data["Gender"].isin(gender_filter)) &
    (data["Customer type"].isin(customer_type_filter)) &
    (data["City"].isin(city_filter)) &
    (data["Product line"].isin(product_line_filter)) &  # Added Product Line filter
    (data["Payment"].isin(payment_filter)) &
    (data["Quantity"].between(min_quantity, max_quantity)) &
    (data["Total Amount"].between(min_total, max_total)) &
    (data["Date"] >= pd.to_datetime(start_date)) &
    (data["Date"] <= pd.to_datetime(end_date)) &
    (data["Date"].dt.day_name().isin(weekday_filter))
]

# Apply time-of-day filter
if time_of_day_filter != "All":
    if time_of_day_filter == "Morning":
        filtered_data = filtered_data[filtered_data["Hour"].between(8, 12)]
    elif time_of_day_filter == "Afternoon":
        filtered_data = filtered_data[filtered_data["Hour"].between(12, 17)]
    elif time_of_day_filter == "Evening":
        filtered_data = filtered_data[filtered_data["Hour"].between(17, 21)]


# Apply time-of-day filter
if time_of_day_filter != "All":
    if time_of_day_filter == "Morning":
        filtered_data = filtered_data[filtered_data["Hour"].between(8, 12)]
    elif time_of_day_filter == "Afternoon":
        filtered_data = filtered_data[filtered_data["Hour"].between(12, 17)]
    elif time_of_day_filter == "Evening":
        filtered_data = filtered_data[filtered_data["Hour"].between(17, 21)]

# Display KPIs
st.title("Market Sales Dashboard")
st.write("A dynamic dashboard for analyzing market sales data.")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Sales", value=int(filtered_data["Quantity"].sum()))
with col2:
    st.metric(label="Total Transactions", value=filtered_data["Invoice ID"].nunique())
with col3:
    avg_sales = filtered_data["Quantity"].sum() / filtered_data["Invoice ID"].nunique()
    st.metric(label="Average Sales per Transaction", value=f"{avg_sales:.2f}")

# Visualizations
st.header("Sales Insights")

# Branch Performance
branch_sales = filtered_data.groupby('Branch')['Quantity'].sum().reset_index()
st.subheader("Total Sales by Branch")
fig_branch = px.bar(
    branch_sales,
    x='Branch',
    y='Quantity',
    title="Total Sales by Branch",
    labels={"Branch": "Branch", "Quantity": "Total Sales"},
    color='Branch',  # Use the 'Branch' column for color mapping
    color_discrete_map={
        "A": "#FF5733",  # Assign a specific color to Branch A
        "B": "#33FF57",  # Assign a specific color to Branch B
        "C": "#3357FF"   # Assign a specific color to Branch C
    }
)
st.plotly_chart(fig_branch)



# Product Line Analysis
product_sales = filtered_data.groupby('Product line')['Quantity'].sum()
st.subheader("Total Sales by Product Line")
fig_product = px.bar(
    product_sales, 
    x=product_sales.index, 
    y=product_sales.values, 
    title="Total Sales by Product Line", 
    labels={"x": "Product Line", "y": "Quantity"}, 
    color=product_sales.values
)
st.plotly_chart(fig_product)

# Time-Based Trends with Month Names
monthly_sales = filtered_data.groupby('Month')['Quantity'].sum()

# Map month numbers to month names
monthly_sales.index = monthly_sales.index.map(lambda x: calendar.month_name[x])

hourly_sales = filtered_data.groupby('Hour')['Quantity'].sum()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Monthly Sales Trend")
    fig_monthly = px.line(
        x=monthly_sales.index, 
        y=monthly_sales.values, 
        title="Monthly Sales Trend", 
        labels={"x": "Month", "y": "Quantity"}
    )
    st.plotly_chart(fig_monthly)

with col2:
    st.subheader("Hourly Sales Trend")
    fig_hourly = px.bar(
        x=hourly_sales.index, 
        y=hourly_sales.values, 
        title="Hourly Sales Trend", 
        labels={"x": "Hour", "y": "Quantity"}
    )
    st.plotly_chart(fig_hourly)

# Customer Demographics
col1, col2 = st.columns(2)
with col1:
    st.subheader("Sales by Gender")
    gender_sales = filtered_data.groupby('Gender')['Quantity'].sum()
    fig_gender = px.pie(
        gender_sales,
        values=gender_sales.values,
        names=gender_sales.index,
        title="Sales by Gender",
        color=gender_sales.index,
        color_discrete_map={"Female": "#FF6692", "Male": "#19D3F3"}  # Map colors explicitly
    )
    st.plotly_chart(fig_gender)

with col2:
    st.subheader("Sales by Customer Type")
    customer_type_sales = filtered_data.groupby('Customer type')['Quantity'].sum()
    fig_customer_type = px.pie(customer_type_sales, values=customer_type_sales.values, names=customer_type_sales.index, title="Sales by Customer Type")
    st.plotly_chart(fig_customer_type)


# Raw Data
st.header("Raw Data")
st.dataframe(filtered_data)
