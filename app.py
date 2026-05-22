import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Propeller Efficiency & Environmental Impact Analyzer")

# --- Propeller Options ---
propellers = [
    "APC_6x3.csv", "APC_7x5.csv", "APC_8x4.csv", "APC_9x6.csv", 
    "APC_10x4.csv", "APC_11x5.csv", "APC_12x6.csv", "APC_13x8.csv", 
    "APC_14x7.csv", "APC_15x10.csv"
]

# --- Propeller Info Dictionary ---
prop_info = {
    "APC_6x3.csv":  {"Diameter": 6,  "Pitch": 3,  "Use": "Micro UAVs, indoor flight"},
    "APC_7x5.csv":  {"Diameter": 7,  "Pitch": 5,  "Use": "Small drones, balance of thrust & speed"},
    "APC_8x4.csv":  {"Diameter": 8,  "Pitch": 4,  "Use": "Small UAVs, endurance"},
    "APC_9x6.csv":  {"Diameter": 9,  "Pitch": 6,  "Use": "Balanced thrust & speed"},
    "APC_10x4.csv": {"Diameter": 10, "Pitch": 4,  "Use": "Training drones, stable lift"},
    "APC_11x5.csv": {"Diameter": 11, "Pitch": 5,  "Use": "Medium UAVs, endurance focus"},
    "APC_12x6.csv": {"Diameter": 12, "Pitch": 6,  "Use": "Larger drones, heavier lift"},
    "APC_13x8.csv": {"Diameter": 13, "Pitch": 8,  "Use": "Larger UAVs, high‑lift missions"},
    "APC_14x7.csv": {"Diameter": 14, "Pitch": 7,  "Use": "High‑power UAVs, speed focus"},
    "APC_15x10.csv":{"Diameter": 15, "Pitch": 10, "Use": "Heavy‑lift UAVs, max thrust"}
}

# --- Always show full propeller table ---
st.markdown("### Propeller Dimensions Overview")
prop_table = pd.DataFrame([
    {"Propeller": k.replace(".csv",""), 
     "Diameter (inches)": v["Diameter"], 
     "Pitch (inches)": v["Pitch"], 
     "Typical Use Case": v["Use"]}
    for k,v in prop_info.items()
])
st.table(prop_table)

# --- Mode Selector ---
mode = st.radio(
    "Choose mode:",
    ["Single Propeller", "Compare Two Propellers"]
)

# --- Single Propeller Mode ---
if mode == "Single Propeller":
    prop = st.selectbox("Choose a propeller", propellers)

    tab1, tab2, tab3 = st.tabs(["Efficiency Analysis", "Fuel & CO₂ Impact", "Suggestions"])

    # --- Efficiency Analysis ---
    with tab1:
        st.markdown("### Efficiency Analysis")

        df = pd.read_csv(f"data/{prop}")
        rpm_min, rpm_max = st.slider(
            "Select RPM range",
            int(df['RPM'].min()), int(df['RPM'].max()),
            (int(df['RPM'].min()), int(df['RPM'].max())),
            key="single_rpm_slider"
        )
        filtered = df[(df['RPM'] >= rpm_min) & (df['RPM'] <= rpm_max)]

        fig, ax = plt.subplots()
        ax.plot(filtered['RPM'], filtered['Efficiency'],
                label=prop.replace(".csv",""), color="blue", linewidth=2.5)

        peak_idx = filtered['Efficiency'].idxmax()
        peak_rpm = filtered.loc[peak_idx, 'RPM']
        peak_eff = filtered.loc[peak_idx, 'Efficiency']
        ax.scatter(peak_rpm, peak_eff, color="red", zorder=5)
        ax.annotate(f"Peak: {peak_eff:.3f} at {peak_rpm} RPM",
                    (peak_rpm, peak_eff),
                    textcoords="offset points", xytext=(10,-10), ha='left',
                    color="red")

        ax.set_xlabel("RPM (revolutions per minute)")
        ax.set_ylabel("Efficiency (dimensionless)")
        ax.set_title("Propeller Efficiency Curve")
        ax.legend()
        st.pyplot(fig)

        st.markdown(f"""
        **Interpretation:**
        - The curve shows how efficiency of the **{prop.replace('.csv','')}** propeller changes with RPM.
        - The red marker highlights the **peak efficiency point**.
        - Operating near this peak RPM maximizes endurance and performance.
        """)

    # --- Fuel & CO₂ Impact ---
    with tab2:
        st.markdown("### Fuel & CO₂ Impact")

        fig, ax = plt.subplots()
        ax.plot(filtered['RPM'], filtered['PWR']*746, label="Power (W)", color="blue", linewidth=2.5)
        ax.set_xlabel("RPM (revolutions per minute)")
        ax.set_ylabel("Power (Watts)")
        ax.set_title("Power Consumption Curve")
        ax.legend()
        st.pyplot(fig)

        fuel_consumption = (filtered['PWR']*746)/3600000
        co2_emissions = fuel_consumption * 0.7
        fig2, ax2 = plt.subplots()
        ax2.plot(filtered['RPM'], co2_emissions, color='green', label="CO₂ Emissions", linewidth=2.5)
        ax2.set_xlabel("RPM (revolutions per minute)")
        ax2.set_ylabel("CO₂ Emissions (kg)")
        ax2.set_title("Estimated CO₂ Emissions Curve")
        ax2.legend()
        st.pyplot(fig2)

        st.markdown("""
        **Interpretation:**
        - Higher RPM increases power demand, which raises fuel/battery consumption.
        - This directly translates into higher CO₂ emissions.
        - Operating closer to the efficiency peak reduces wasted energy and emissions.
        """)

    # --- Suggestions ---
    with tab3:
        st.markdown("### Sustainability Suggestions (Quantitative)")

        avg_rpm = filtered['RPM'].mean()
        avg_power = (filtered['PWR']*746).mean()
        peak_power = filtered.loc[peak_idx, 'PWR']*746
        savings_pct = (avg_power - peak_power)/avg_power * 100
        co2_savings = (avg_power - peak_power)/3600000 * 0.7

        st.markdown(f"""
        - **Lower RPM operation**: Reduce operating RPM from ~{avg_rpm:.0f} to {peak_rpm:.0f}.  
          → Estimated power savings: {savings_pct:.1f}%  
          → CO₂ reduction: {co2_savings*1000:.2f} g/hr
        """)

        st.markdown(f"""
        - **Propeller choice**: The **{prop.replace('.csv','')}**  
          (Diameter {prop_info[prop]['Diameter']} in, Pitch {prop_info[prop]['Pitch']} in)  
          is typically used for *{prop_info[prop]['Use']}*.  
          Choosing a propeller closer to your mission profile improves efficiency and can save ~10–15% fuel use.
        """)

        st.markdown("""
        - **Lightweight UAV design**: Reducing UAV mass by 500 g lowers thrust demand ~0.9 lbf, saving ~6% power and ~0.05 kg CO₂/hr.
        """)

        st.markdown("""
        - **Hybrid assist**: Adding a 50 W solar panel offsets ~0.05 kWh/hr, reducing CO₂ emissions ~0.035 kg/hr.
        """)

# --- Comparison Mode ---
else:
    prop1 = st.selectbox("Choose first propeller", propellers, index=0)
    prop2 = st.selectbox("Choose second propeller", propellers, index=1)

    tab1, tab2, tab3 = st.tabs(["Efficiency Comparison", "Fuel & CO₂ Impact", "Suggestions"])

    df1 = pd.read_csv(f"data/{prop1}")
    df2 = pd.read_csv(f"data/{prop2}")

    rpm_min, rpm_max = st.slider(
        "Select RPM range",
        min(int(df1['RPM'].min()), int(df2['RPM'].min())),
        max(int(df1['RPM'].max()), int(df2['RPM'].max())),
        (min(int(df1['RPM'].min()), int(df2['RPM'].min())),
         max(int(df1['RPM'].max()), int(df2['RPM'].max()))),
        key="compare_rpm_slider"
    )

    df1_filtered = df1[(df1['RPM'] >= rpm_min) & (df1['RPM'] <= rpm_max)]
    df2_filtered = df2[(df2['RPM'] >= rpm_min) & (df2['RPM'] <= rpm_max)]

    # --- Efficiency Comparison ---
    with tab1:
        fig, ax = plt.subplots()
        ax.plot(df1_filtered['RPM'], df1_filtered['Efficiency'], 
                label=prop1.replace(".csv",""), color="blue", linewidth=2.5)
        ax.plot(df2_filtered['RPM'], df2_filtered['Efficiency'], 
                label=prop2.replace(".csv",""), color="orange", linewidth=1.5)

        for df, prop, color in [(df1_filtered, prop1, "blue"), (df2_filtered, prop2, "orange")]:
            peak_idx = df['Efficiency'].idxmax()
            peak_rpm = df.loc[peak_idx, 'RPM']
            peak_eff = df.loc[peak_idx, 'Efficiency']
            ax.scatter(peak_rpm, peak_eff, color=color, edgecolor="black", zorder=5)
            ax.annotate(f"{prop.replace('.csv','')} peak: {peak_eff:.3f} at {peak_rpm} RPM",
                        (peak_rpm, peak_eff),
                        textcoords="offset points", xytext=(10,-10), ha='left',
                        color=color)

        ax.set_xlabel("RPM (revolutions per minute)")
        ax.set_ylabel("Efficiency (dimensionless)")
        ax.set_title("Propeller Efficiency Comparison")

        # Legend moved below the plot
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2)

        st.pyplot(fig)

        st.markdown("""
        **Interpretation:**
        - The blue and orange curves show how efficiency varies with RPM for the two selected propellers.
        - The peak efficiency points are marked, showing the RPM at which each propeller performs best.
        - This comparison highlights which propeller is more efficient in the operating range you care about.
        """)


    # --- Fuel & CO₂ Impact ---
    with tab2:
        fig, ax = plt.subplots()
        ax.plot(df1_filtered['RPM'], df1_filtered['PWR']*746, 
                label=prop1.replace(".csv"," Power"), color="blue", linewidth=2.5)
        ax.plot(df2_filtered['RPM'], df2_filtered['PWR']*746, 
                label=prop2.replace(".csv"," Power"), color="orange", linewidth=1.5)
        ax.set_xlabel("RPM (revolutions per minute)")
        ax.set_ylabel("Power (Watts)")
        ax.set_title("Power Consumption Comparison")
        ax.legend()
        st.pyplot(fig)

        co2_1 = (df1_filtered['PWR']*746)/3600000 * 0.7
        co2_2 = (df2_filtered['PWR']*746)/3600000 * 0.7
        fig2, ax2 = plt.subplots()
        ax2.plot(df1_filtered['RPM'], co2_1, 
                 label=prop1.replace(".csv"," CO₂"), color="green", linewidth=2.5)
        ax2.plot(df2_filtered['RPM'], co2_2, 
                 label=prop2.replace(".csv"," CO₂"), color="red", linewidth=1.5)
        ax2.set_xlabel("RPM (revolutions per minute)")
        ax2.set_ylabel("CO₂ Emissions (kg)")
        ax2.set_title("CO₂ Emissions Comparison")
        ax2.legend()
        st.pyplot(fig2)

        st.markdown("""
        **Interpretation:**
        - The blue/orange curves show how much power each propeller requires across RPM.
        - The green/red curves show the corresponding CO₂ emissions.
        - Using different line widths and colors makes overlapping values easier to distinguish.
        - Comparing these curves helps you see which propeller consumes less energy and produces fewer emissions in the same RPM range.
        """)

    # --- Suggestions ---
    with tab3:
        st.markdown("### Sustainability Suggestions (Quantitative)")

        avg_power1 = (df1_filtered['PWR']*746).mean()
        avg_power2 = (df2_filtered['PWR']*746).mean()
        peak_idx1 = df1_filtered['Efficiency'].idxmax()
        peak_idx2 = df2_filtered['Efficiency'].idxmax()
        peak_power1 = df1_filtered.loc[peak_idx1, 'PWR']*746
        peak_power2 = df2_filtered.loc[peak_idx2, 'PWR']*746

        savings_pct1 = (avg_power1 - peak_power1)/avg_power1 * 100
        savings_pct2 = (avg_power2 - peak_power2)/avg_power2 * 100
        co2_savings1 = (avg_power1 - peak_power1)/3600000 * 0.7
        co2_savings2 = (avg_power2 - peak_power2)/3600000 * 0.7

        st.markdown(f"""
        - **{prop1.replace('.csv','')}** (Diameter {prop_info[prop1]['Diameter']} in, Pitch {prop_info[prop1]['Pitch']} in):  
          → Lower RPM saves ~{savings_pct1:.1f}% power  
          → CO₂ reduction: {co2_savings1*1000:.2f} g/hr  
          → Typical use: *{prop_info[prop1]['Use']}*
        """)

        st.markdown(f"""
        - **{prop2.replace('.csv','')}** (Diameter {prop_info[prop2]['Diameter']} in, Pitch {prop_info[prop2]['Pitch']} in):  
          → Lower RPM saves ~{savings_pct2:.1f}% power  
          → CO₂ reduction: {co2_savings2*1000:.2f} g/hr  
          → Typical use: *{prop_info[prop2]['Use']}*
        """)

        if avg_power1 < avg_power2:
            better_prop = prop1.replace(".csv","")
            diff_power = avg_power2 - avg_power1
            diff_co2 = (avg_power2 - avg_power1)/3600000 * 0.7
        else:
            better_prop = prop2.replace(".csv","")
            diff_power = avg_power1 - avg_power2
            diff_co2 = (avg_power1 - avg_power2)/3600000 * 0.7

        st.markdown(f"""
        - **Direct Comparison**:  
          {better_prop} is more efficient overall, saving ~{diff_power:.1f} W average power  
          and reducing emissions by ~{diff_co2*1000:.2f} g/hr compared to the other propeller.
        """)

        st.markdown("""
        **Interpretation:**
        - Each propeller’s savings are calculated relative to its average vs peak efficiency operation.
        - The direct comparison shows which propeller is more sustainable in terms of energy use and CO₂ emissions.
        - The advice is contextual: larger diameter props (like APC_15x10) are better for heavy lift, while smaller ones (like APC_6x3) suit micro UAVs.
        """)
