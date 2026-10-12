
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="UAC Care Load Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 System Capacity & Care Load Analytics")
st.subheader("Unaccompanied Children (UAC) — CBP and HHS")
st.write(
    "Analyze daily child-care loads, intake, transfers, discharges, "
    "and trends using the uploaded dataset."
)


# --------------------------------------------------
# 2. FIND AND LOAD THE DATASET
# --------------------------------------------------

EXPECTED_FILE = "HHS_Unaccompanied_Alien_Children_Program.csv"


def load_csv(uploaded_file=None):
    """Load the uploaded CSV or find it in the project folders."""

    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)

    possible_paths = [
        Path("data") / EXPECTED_FILE,
        Path(EXPECTED_FILE),
    ]

    # Also look for any CSV in the data folder or project root.
    for folder in [Path("data"), Path(".")]:
        if folder.exists():
            possible_paths.extend(
                p for p in folder.glob("*.csv")
                if p not in possible_paths
            )

    for path in possible_paths:
        if path.exists() and path.is_file():
            return pd.read_csv(path)

    return None


uploaded_file = st.sidebar.file_uploader(
    "Upload your UAC CSV dataset",
    type=["csv"]
)

try:
    raw_df = load_csv(uploaded_file)
except Exception as error:
    st.error(f"Could not read the CSV file: {error}")
    st.stop()

if raw_df is None:
    st.warning(
        "Dataset not found. Upload your CSV using the sidebar, "
        "or add it to the repository root or the data/ folder."
    )
    st.info(
        f"Expected filename: {EXPECTED_FILE}"
    )
    st.stop()

if raw_df.empty:
    st.error("The uploaded CSV contains no data.")
    st.stop()


# --------------------------------------------------
# 3. CLEAN COLUMN NAMES
# --------------------------------------------------

def normalize_name(name):
    """Make column names easier to compare."""
    return (
        str(name)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("\n", " ")
    )


df = raw_df.copy()
df.columns = [normalize_name(col) for col in df.columns]


def find_column(possible_names, keywords=()):
    """Find a column by known names or matching keywords."""

    for name in possible_names:
        if name in df.columns:
            return name

    for col in df.columns:
        if all(word in col for word in keywords):
            return col

    return None


column_map = {
    "Date": find_column(
        ["date", "report date", "calendar date"],
        ("date",)
    ),
    "Children apprehended and placed in CBP custody": find_column(
        [
            "children apprehended and placed in cbp custody",
            "children apprehended",
        ],
        ("apprehended",)
    ),
    "Children in CBP custody": find_column(
        ["children in cbp custody", "cbp custody"],
        ("cbp", "custody")
    ),
    "Children transferred out of CBP custody": find_column(
        [
            "children transferred out of cbp custody",
            "transferred out of cbp custody",
        ],
        ("transferred", "cbp")
    ),
    "Children in HHS Care": find_column(
        ["children in hhs care", "hhs care"],
        ("hhs", "care")
    ),
    "Children discharged from HHS Care": find_column(
        [
            "children discharged from hhs care",
            "discharged from hhs care",
        ],
        ("discharged", "hhs")
    ),
}

# Rename recognized columns to standard names.
rename_map = {
    actual: standard
    for standard, actual in column_map.items()
    if actual is not None
}
df = df.rename(columns=rename_map)

required_columns = [
    "Date",
    "Children in CBP custody",
    "Children in HHS Care",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        "Some required columns could not be identified: "
        + ", ".join(missing_columns)
    )
    st.write("**Columns found in your CSV:**")
    st.write(list(raw_df.columns))
    st.info(
        "Check the column names in your CSV. The app needs a date "
        "column, a CBP custody column, and an HHS care column."
    )
    st.stop()


# --------------------------------------------------
# 4. DATA CLEANING
# --------------------------------------------------

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

numeric_columns = [
    "Children apprehended and placed in CBP custody",
    "Children in CBP custody",
    "Children transferred out of CBP custody",
    "Children in HHS Care",
    "Children discharged from HHS Care",
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        )

df = df.dropna(subset=["Date"])
df = df.sort_values("Date").drop_duplicates(
    subset=["Date"], keep="last"
)

if df.empty:
    st.error("No valid dates were found in the dataset.")
    st.stop()

# Fill missing flow fields with zero for calculations.
# Custody snapshots remain missing if the source has no value.
for col in numeric_columns:
    if col in df.columns and col not in [
        "Children in CBP custody",
        "Children in HHS Care",
    ]:
        df[col] = df[col].fillna(0)

df["Total System Load"] = (
    df["Children in CBP custody"].fillna(0)
    + df["Children in HHS Care"].fillna(0)
)

if "Children apprehended and placed in CBP custody" in df.columns:
    df["CBP Net Flow"] = (
        df["Children apprehended and placed in CBP custody"]
        - df.get(
            "Children transferred out of CBP custody",
            pd.Series(0, index=df.index)
        )
    )

if (
    "Children transferred out of CBP custody" in df.columns
    and "Children discharged from HHS Care" in df.columns
):
    df["HHS Net Flow"] = (
        df["Children transferred out of CBP custody"]
        - df["Children discharged from HHS Care"]
    )


# --------------------------------------------------
# 5. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

filtered_df = df[
    (df["Date"].dt.date >= start_date)
    & (df["Date"].dt.date <= end_date)
].copy()

if filtered_df.empty:
    st.warning("No records are available for this date range.")
    st.stop()

st.sidebar.caption(
    f"Records displayed: {len(filtered_df):,}"
)


# --------------------------------------------------
# 6. KEY PERFORMANCE INDICATORS
# --------------------------------------------------

latest = filtered_df.iloc[-1]

cbp_latest = latest["Children in CBP custody"]
hhs_latest = latest["Children in HHS Care"]
total_latest = latest["Total System Load"]

previous = (
    filtered_df.iloc[-2]
    if len(filtered_df) > 1
    else None
)

def format_number(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:,.0f}"


st.header("📌 Key Performance Indicators")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Children in CBP Custody",
    format_number(cbp_latest),
    delta=(
        format_number(cbp_latest - previous["Children in CBP custody"])
        if previous is not None
        else None
    ),
)

c2.metric(
    "Children in HHS Care",
    format_number(hhs_latest),
    delta=(
        format_number(hhs_latest - previous["Children in HHS Care"])
        if previous is not None
        else None
    ),
)

c3.metric(
    "Total System Load",
    format_number(total_latest),
    delta=(
        format_number(
            total_latest - previous["Total System Load"]
        )
        if previous is not None
        else None
    ),
)

c4, c5, c6 = st.columns(3)

if "Children apprehended and placed in CBP custody" in filtered_df:
    c4.metric(
        "Total Apprehensions",
        format_number(
            filtered_df[
                "Children apprehended and placed in CBP custody"
            ].sum()
        ),
    )
else:
    c4.metric("Total Apprehensions", "Not available")

if "Children transferred out of CBP custody" in filtered_df:
    c5.metric(
        "Total CBP Transfers",
        format_number(
            filtered_df[
                "Children transferred out of CBP custody"
            ].sum()
        ),
    )
else:
    c5.metric("Total CBP Transfers", "Not available")

if "Children discharged from HHS Care" in filtered_df:
    c6.metric(
        "Total HHS Discharges",
        format_number(
            filtered_df[
                "Children discharged from HHS Care"
            ].sum()
        ),
    )
else:
    c6.metric("Total HHS Discharges", "Not available")


# --------------------------------------------------
# 7. CUSTODY AND CARE LOAD TRENDS
# --------------------------------------------------

st.header("📈 Care Load Trends")

load_df = filtered_df[
    ["Date", "Children in CBP custody", "Children in HHS Care"]
].melt(
    id_vars="Date",
    var_name="Care System",
    value_name="Number of Children",
)

fig_load = px.line(
    load_df,
    x="Date",
    y="Number of Children",
    color="Care System",
    markers=False,
    title="Daily Children in CBP Custody vs HHS Care",
    labels={
        "Date": "Date",
        "Number of Children": "Number of Children",
        "Care System": "Care System",
    },
)

fig_load.update_layout(legend_title_text="Care System")
st.plotly_chart(fig_load, use_container_width=True)


# --------------------------------------------------
# 8. TOTAL SYSTEM LOAD
# --------------------------------------------------

fig_total = px.area(
    filtered_df,
    x="Date",
    y="Total System Load",
    title="Combined CBP and HHS Care Load",
    labels={
        "Date": "Date",
        "Total System Load": "Total Children",
    },
)

st.plotly_chart(fig_total, use_container_width=True)

st.caption(
    "Total System Load is calculated as children in CBP custody "
    "plus children in HHS care on the same date. It is a combined "
    "caseload indicator, not an official capacity-utilization rate."
)


# --------------------------------------------------
# 9. INTAKE, TRANSFERS AND DISCHARGES
# --------------------------------------------------

st.header("🔄 Intake, Transfers and Discharges")

flow_columns = [
    "Children apprehended and placed in CBP custody",
    "Children transferred out of CBP custody",
    "Children discharged from HHS Care",
]

available_flows = [
    col for col in flow_columns if col in filtered_df.columns
]

if available_flows:
    flow_df = filtered_df[
        ["Date"] + available_flows
    ].melt(
        id_vars="Date",
        var_name="Activity",
        value_name="Number of Children",
    )

    fig_flow = px.line(
        flow_df,
        x="Date",
        y="Number of Children",
        color="Activity",
        title="Daily Intake, Transfers and Discharges",
        labels={
            "Date": "Date",
            "Number of Children": "Number of Children",
            "Activity": "Activity",
        },
    )

    st.plotly_chart(fig_flow, use_container_width=True)
else:
    st.info("No intake, transfer or discharge columns were found.")


# --------------------------------------------------
# 10. WEEKLY SUMMARY
# --------------------------------------------------

st.header("📅 Weekly Summary")

weekly = (
    filtered_df.set_index("Date")
    .resample("W")
    .agg({
        "Children in CBP custody": "mean",
        "Children in HHS Care": "mean",
        "Total System Load": "mean",
    })
    .dropna(how="all")
    .reset_index()
)

weekly = weekly.rename(columns={
    "Date": "Week Ending",
    "Children in CBP custody": "Average CBP Custody",
    "Children in HHS Care": "Average HHS Care",
    "Total System Load": "Average Total System Load",
})

st.dataframe(
    weekly.round(2),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "⬇️ Download Weekly Summary",
    data=weekly.to_csv(index=False).encode("utf-8"),
    file_name="uac_weekly_summary.csv",
    mime="text/csv",
)


# --------------------------------------------------
# 11. SIMPLE TREND-BASED FORECAST
# --------------------------------------------------

st.header("🔮 Simple Trend Forecast")

st.write(
    "This is an exploratory linear-trend forecast based on historical "
    "daily records. It is not an official operational prediction."
)

forecast_days = st.sidebar.slider(
    "Forecast horizon (days)",
    min_value=7,
    max_value=30,
    value=7,
    step=1,
)

forecast_metric = st.selectbox(
    "Choose a metric to forecast",
    [
        "Children in CBP custody",
        "Children in HHS Care",
        "Total System Load",
    ],
)

history = filtered_df[
    ["Date", forecast_metric]
].dropna().sort_values("Date")

if len(history) >= 3:
    # Use elapsed days so dates with gaps are handled sensibly.
    x_values = (
        history["Date"] - history["Date"].min()
    ).dt.days.to_numpy()

    y_values = history[forecast_metric].to_numpy(dtype=float)

    slope, intercept = __import__("numpy").polyfit(
        x_values, y_values, 1
    )

    future_dates = pd.date_range(
        history["Date"].max() + pd.Timedelta(days=1),
        periods=forecast_days,
        freq="D",
    )

    future_x = (
        future_dates - history["Date"].min()
    ).days.to_numpy()

    predictions = intercept + slope * future_x

    forecast_df = pd.DataFrame({
        "Date": future_dates,
        "Forecast": predictions.clip(min=0),
    })

    historical_plot = history.rename(
        columns={forecast_metric: "Historical"}
    )

    fig_forecast = px.line(
        historical_plot,
        x="Date",
        y="Historical",
        title=f"{forecast_metric}: Historical Data and Forecast",
        labels={"Historical": "Number of Children"},
    )

    fig_forecast.add_scatter(
        x=forecast_df["Date"],
        y=forecast_df["Forecast"],
        mode="lines+markers",
        name="Trend Forecast",
    )

    st.plotly_chart(fig_forecast, use_container_width=True)

    st.dataframe(
        forecast_df.round(2),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "⬇️ Download Forecast",
        data=forecast_df.to_csv(index=False).encode("utf-8"),
        file_name="uac_load_forecast.csv",
        mime="text/csv",
    )
else:
    st.info(
        "At least three valid historical observations are required "
        "to calculate this simple trend forecast."
    )


# --------------------------------------------------
# 12. DATA TABLE
# --------------------------------------------------

st.header("📋 Dataset Explorer")

with st.expander("View filtered dataset"):
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
    )

st.download_button(
    "⬇️ Download Filtered Dataset",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="uac_filtered_data.csv",
    mime="text/csv",
)


# --------------------------------------------------
# 13. PROJECT INFORMATION
# --------------------------------------------------

st.divider()

st.subheader("About this Dashboard")

st.write(
    """
    This dashboard supports exploratory analysis of unaccompanied
    children's care-system data.

    **Main features**
    - CBP custody and HHS care monitoring
    - Combined system-load tracking
    - Intake, transfer and discharge trends
    - Weekly summaries
    - Exploratory trend-based forecasting

    **Important:** A true capacity-utilization percentage requires
    verified capacity limits. The combined caseload shown here does
    not by itself establish available beds or operational capacity.
    """
)

st.caption("Built with Python, Streamlit, Pandas and Plotly.")
