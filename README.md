# System Capacity & Care Load Analytics for Unaccompanied Children

## Project Overview

The **System Capacity & Care Load Analytics** project is a Python-based data analytics dashboard designed to explore the care loads of Unaccompanied Alien Children (UAC) across U.S. Customs and Border Protection (CBP) custody and the Department of Health and Human Services (HHS) care system.

The dashboard helps users understand changes in daily caseloads, intake, transfers, discharges, and historical trends.

## Objectives

- Analyze daily children in CBP custody and HHS care.
- Monitor combined system caseload trends.
- Examine child intake, transfers, and discharges.
- Display key performance indicators (KPIs).
- Generate weekly summaries.
- Explore simple trend-based forecasts.

## Technologies Used

- Python
- Streamlit
- Pandas
- Plotly
- NumPy

## Dataset

The project uses the following CSV dataset:

`HHS_Unaccompanied_Alien_Children_Program.csv`

The dataset contains daily records relating to children in CBP custody, children in HHS care, intake, transfers, and discharges, depending on the available columns.

## Dashboard Features

1. **KPI Dashboard** – Displays the latest available CBP custody, HHS care, and combined system-load figures.
2. **Care Load Trends** – Visualizes daily CBP and HHS caseloads.
3. **System Load Analysis** – Shows the combined caseload over time.
4. **Intake and Discharge Analysis** – Displays available intake, transfer, and discharge trends.
5. **Weekly Summary** – Calculates weekly average caseloads.
6. **Trend Forecasting** – Provides an exploratory linear-trend forecast.
7. **Data Explorer** – Allows users to view and download filtered records.

## Project Structure

```text
uac-care-load-analytics/
├── app.py
├── requirements.txt
├── README.md
└── HHS_Unaccompanied_Alien_Children_Program.csv
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Jaishini10/uac-care-load-analytics.git
cd uac-care-load-analytics
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
streamlit run app.py
```

The dashboard will open in your browser.

## Deployment

This application can be deployed using Streamlit Community Cloud by connecting the GitHub repository and selecting `app.py` as the main file.

## Expected Outcome

The dashboard provides a clear visual overview of historical care-system caseloads and related activities. It can support exploratory analysis and help users identify trends that may need further investigation.

## Limitations

- Forecasts are simple trend-based estimates, not official predictions.
- Combined caseload is not the same as a verified capacity-utilization percentage.
- Actual capacity limits are needed to calculate capacity utilization.
- Results depend on the completeness and accuracy of the dataset.

## Conclusion

This project demonstrates how Python, data analysis, and interactive visualization can be used to study care-system caseload trends and support data-informed understanding of the UAC care process.

---

**Developed using Python, Streamlit, Pandas, Plotly, and NumPy.**
