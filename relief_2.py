import streamlit as st
import pandas as pd
import requests
import json
from collections import defaultdict

# ✅ API Key
GROQ_API_KEY = st.secrets["API_KEY"]

# ✅ Load JSON data
with open("disaster_data.json") as f:
    disaster_data = json.load(f)

with open("ngo_data.json") as f:
    ngo_data = json.load(f)

# ✅ Convert disaster data to DataFrame
disaster_df = pd.DataFrame(disaster_data)

# ✅ Streamlit UI setup
st.set_page_config(page_title="AI Disaster Resource Estimator", layout="wide")
st.title("🚨 AI-Powered Disaster Resource Estimator")

# ========== Sidebar ==========
st.sidebar.header("📍 Region & Disaster Info")
region = st.sidebar.selectbox("Select Region", disaster_df["Region"].unique())
estimate_btn = st.sidebar.button("Estimate Resources")

# ========== Resource Explanation ==========
with st.expander("📘 Per Person / Per Day Resource Requirement Explanation"):
    st.markdown("""
    The following assumptions are used for estimating required resources:

    - **Food_Packets**: 2 packets per person per day  
    - **Water_Litres**: 5 litres per person per day  
    - **Tents**: 1 tent per 5 people  
    - **Medical_Teams**: 1 team per 500 people  
    - **Hygiene_Kits**: 1 kit per person  
    - **Volunteers_Available**: 1 per 50 people
    """)

# ========== Main Calculation ==========
if region:
    disaster_info = disaster_df[disaster_df["Region"] == region].iloc[0]

    total_resources = defaultdict(int)
    supporting_ngos = []
    total_volunteers = 0

    for ngo in ngo_data:
        if region in ngo["Supported_Regions"]:
            supporting_ngos.append(ngo["NGO_Name"])
            for resource, amount in ngo["Resources"].items():
                total_resources[resource] += amount
            total_volunteers += ngo.get("Volunteers_Available", 0)

    # Sidebar display
    st.sidebar.markdown(f"**📍 Region**: {region}")
    st.sidebar.markdown(f"**⚠️ Disaster**: {disaster_info['Disaster_Type']}")
    st.sidebar.markdown(f"**👥 People Affected**: {disaster_info['People_Affected']}")
    st.sidebar.markdown(f"**📆 Duration**: {disaster_info['Disaster_Duration_Days']} days")
    st.sidebar.markdown("---")

    for ngo in ngo_data:
        if region in ngo["Supported_Regions"]:
            with st.sidebar.expander(ngo["NGO_Name"]):
                st.markdown("**Resources Provided:**")
                for resource, qty in ngo["Resources"].items():
                    st.markdown(f"- {resource.replace('_', ' ')}: {qty}")
                st.markdown(f"- 👥 Volunteers: {ngo.get('Volunteers_Available', 0)}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**📦 Total Available Resources:**")
    for res, qty in total_resources.items():
        st.sidebar.markdown(f"- {res.replace('_', ' ')}: {qty}")
    st.sidebar.markdown(f"- 👥 Volunteers: {total_volunteers}")

# ========== Estimation Logic ==========
st.subheader("📦 Estimated Resources Needed")

if estimate_btn:
    people = disaster_info['People_Affected']
    days = disaster_info['Disaster_Duration_Days']

    # Per person/day logic
    requirement_factors = {
        "Food_Packets": 2 * people * days,
        "Water_Litres": 5 * people * days,
        "Tents": people // 5,
        "Medical_Teams": people // 500,
        "Hygiene_Kits": people,
        "Volunteers_Available": people // 50
    }

    rows = []
    for resource in requirement_factors:
        required = requirement_factors[resource]
        available = total_resources.get(resource, 0)
        if resource == "Volunteers_Available":
            available = total_volunteers  # override from NGO volunteer count
        shortage = max(required - available, 0)
        rows.append([resource.replace("_", " "), required, available, shortage])

    df = pd.DataFrame(rows, columns=["Resource", "Required", "Available", "Shortage"])
    df["Required"] = df["Required"].astype(int)
    df["Available"] = df["Available"].astype(int)
    df["Shortage"] = df["Shortage"].astype(int)

    st.success("Below is the resource estimation based on the current NGO support and disaster impact:")
    st.dataframe(df, use_container_width=True)

    st.markdown("✅ **Calculation is based on standardized need per person per day. You can see the logic in the expander above.**")
