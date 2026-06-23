import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

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
    "APC_13x8.csv": {"Diameter": 13, "Pitch": 8,  "Use": "Larger UAVs, high lift missions"},
    "APC_14x7.csv": {"Diameter": 14, "Pitch": 7,  "Use": "High power UAVs, speed focus"},
    "APC_15x10.csv":{"Diameter": 15, "Pitch": 10, "Use": "Heavy lift UAVs, max thrust"}
}

# --- Aliases for flexible column recognition ---
aliases = {
    "RPM": ["RPM", "rpm", "Rev/min", "Revolutions"],
    "Efficiency": ["Efficiency", "Eff", "η", "Efficiency (%)","Pe"],
    "PWR": ["PWR", "Power", "Horsepower", "HP", "Watts"]
}

def normalize_columns(df):
    col_map = {}
    for standard, options in aliases.items():
        for opt in options:
            if opt in df.columns:
                col_map[opt] = standard
    df = df.rename(columns=col_map)
    return df

def clean_uploaded_csv(uploaded_file):
    # Accept either a file-like/path (from uploader) or a pre-read DataFrame
    if isinstance(uploaded_file, pd.DataFrame):
        df = uploaded_file.copy()
    else:
        df = pd.read_csv(uploaded_file)
    df = normalize_columns(df)

    required_cols = {"RPM", "Efficiency", "PWR"}
    if not required_cols.issubset(df.columns):
        st.error("CSV must contain RPM, Efficiency, and PWR columns (aliases accepted).")
        return None

    df = df.dropna()
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Normalize efficiency if given in %
    if df["Efficiency"].max() > 1.5:
        df["Efficiency"] = df["Efficiency"] / 100.0

    # Convert PWR to Watts if values look like HP
    if df["PWR"].mean() < 50:  
        df["PWR"] = df["PWR"] * 746

    return df

# --- Template CSV generator ---
if st.button("Download Template CSV"):
    sample = pd.DataFrame({
        "RPM": [1000, 2000, 3000],
        "Efficiency": [0.65, 0.72, 0.70],
        "PWR": [0.5, 0.8, 1.2]  # in HP
    })
    csv_buffer = io.StringIO()
    sample.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Click to download template",
        data=csv_buffer.getvalue(),
        file_name="propeller_template.csv",
        mime="text/csv"
    )

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
mode = st.radio("Choose mode:", ["Single Propeller", "Compare Two Propellers"])

# --- Single Propeller Mode ---
if mode == "Single Propeller":
    uploaded_file = st.file_uploader("Upload your own propeller CSV", type=["csv"])
    if uploaded_file is not None:
        df = clean_uploaded_csv(uploaded_file)
        prop_label = "Uploaded Propeller"
        prop_info_entry = {"Diameter": "-", "Pitch": "-", "Use": "Custom dataset"}
    else:
        prop = st.selectbox("Choose a propeller", propellers)
        df = pd.read_csv(f"data/{prop}")
        prop_label = prop.replace(".csv","")
        prop_info_entry = prop_info[prop]

    if df is not None:
        tab1, tab2, tab3 = st.tabs(["Efficiency Analysis", "Fuel & CO₂ Impact", "Suggestions"])

        # --- Efficiency Analysis ---
        with tab1:
            rpm_min, rpm_max = st.slider("Select RPM range",
                int(df['RPM'].min()), int(df['RPM'].max()),
                (int(df['RPM'].min()), int(df['RPM'].max())),
                key="single_rpm_slider"
            )
            filtered = df[(df['RPM'] >= rpm_min) & (df['RPM'] <= rpm_max)]
            filtered['Efficiency'] = filtered['Efficiency'].clip(lower=0, upper=1)

            fig, ax = plt.subplots()
            ax.plot(filtered['RPM'], filtered['Efficiency'],
                    label=prop_label, color="#004080", linewidth=2.5)  # Deep Blue

            peak_idx = filtered['Efficiency'].idxmax()
            peak_rpm = filtered.loc[peak_idx, 'RPM']
            peak_eff = filtered.loc[peak_idx, 'Efficiency']
            ax.scatter(peak_rpm, peak_eff, color="black", edgecolor="black", s=80, zorder=5)

            ax.annotate(f"Peak: {peak_eff:.3f} at {peak_rpm} RPM",
                        (peak_rpm, peak_eff),
                        textcoords="offset points", xytext=(10,-10), ha='left',
                        color="#000000")

            ax.set_xlabel("RPM (revolutions per minute)", color="#000000")
            ax.set_ylabel("Efficiency (dimensionless)", color="#000000")
            ax.set_title("Propeller Efficiency Curve")
            ax.tick_params(axis='both', colors="#000000")
            ax.grid(True, color="gray", linestyle="--", linewidth=0.5)
            ax.legend()
            st.pyplot(fig)

            st.markdown(f"""
            **Interpretation:**
            - The curve shows how efficiency of the **{prop_label}** propeller changes with RPM.
            - The black marker highlights the **peak efficiency point**.
            - Operating near this peak RPM maximizes endurance and performance.
            """)

        # --- Fuel & CO₂ Impact ---
        with tab2:
            fig, ax = plt.subplots()
            ax.plot(filtered['RPM'], filtered['PWR']*746, label="Power (W)", color="#4682b4", linewidth=2.5)
            ax.set_xlabel("RPM")
            ax.set_ylabel("Power (Watts)")
            ax.set_title("Power Consumption Curve")
            ax.legend()
            st.pyplot(fig)

            fuel_consumption = (filtered['PWR']*746)/3600000
            co2_emissions = fuel_consumption * 0.7
            fig2, ax2 = plt.subplots()
            ax2.plot(filtered['RPM'], co2_emissions, color="#228b22", label="CO₂ Emissions", linewidth=2.5)
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

            # Only show propeller info if selected from built‑in list
            if uploaded_file is None:
                st.markdown(f"""
                - **Propeller choice**: The **{prop_label}**  
                (Diameter {prop_info_entry['Diameter']} in, Pitch {prop_info_entry['Pitch']} in)  
                is typically used for *{prop_info_entry['Use']}*.
                """)


# --- Comparison Mode ---
else:
    uploaded_file1 = st.file_uploader("Upload first propeller CSV (optional)", type=["csv"], key="upload1")
    uploaded_file2 = st.file_uploader("Upload second propeller CSV (optional)", type=["csv"], key="upload2")

    if uploaded_file1 is not None:
        raw_df1 = pd.read_csv(uploaded_file1)
        df1 = clean_uploaded_csv(raw_df1)
        prop1_label = uploaded_file1.name.replace(".csv","")
        prop1_info = {"Diameter": "-", "Pitch": "-", "Use": "Custom dataset"}
    else:
        prop1 = st.selectbox("Choose first propeller", propellers, index=0)
        raw_df1 = pd.read_csv(f"data/{prop1}")
        df1 = clean_uploaded_csv(raw_df1)
        prop1_label = prop1.replace(".csv","")
        prop1_info = prop_info[prop1]

    if uploaded_file2 is not None:
        raw_df2 = pd.read_csv(uploaded_file2)
        df2 = clean_uploaded_csv(raw_df2)
        prop2_label = uploaded_file2.name.replace(".csv","")
        prop2_info = {"Diameter": "-", "Pitch": "-", "Use": "Custom dataset"}
    else:
        prop2 = st.selectbox("Choose second propeller", propellers, index=1)
        raw_df2 = pd.read_csv(f"data/{prop2}")
        df2 = clean_uploaded_csv(raw_df2)
        prop2_label = prop2.replace(".csv","")
        prop2_info = prop_info[prop2]

    if df1 is not None and df2 is not None:
        tab1, tab2, tab3 = st.tabs(["Efficiency Comparison", "Fuel & CO₂ Impact", "Suggestions"])

        # --- Efficiency Comparison ---
        with tab1:
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
            df1_filtered['Efficiency'] = df1_filtered['Efficiency'].clip(lower=0, upper=1)
            df2_filtered['Efficiency'] = df2_filtered['Efficiency'].clip(lower=0, upper=1)


            fig, ax = plt.subplots()
            ax.plot(df1_filtered['RPM'], df1_filtered['Efficiency'],
                    label=prop1_label, color="#004080", linewidth=2.5)
            ax.plot(df2_filtered['RPM'], df2_filtered['Efficiency'],
                    label=prop2_label, color="#D98C00", linewidth=2.5)

            # Peak markers + staggered annotation boxes
            for i, (df, label) in enumerate([(df1_filtered, prop1_label), (df2_filtered, prop2_label)]):
                peak_idx = df['Efficiency'].idxmax()
                peak_rpm = df.loc[peak_idx, 'RPM']
                peak_eff = df.loc[peak_idx, 'Efficiency']
                ax.scatter(peak_rpm, peak_eff, color="black", edgecolor="black", s=80, zorder=5)

                # Different horizontal + vertical offsets
                offset_x = 10 if i == 0 else -40
                offset_y = -25 if i == 0 else -45

                ax.annotate(f"{label} peak: {peak_eff:.3f} at {peak_rpm} RPM",
                            (peak_rpm, peak_eff),
                            textcoords="offset points", xytext=(offset_x, offset_y),
                            ha='left' if i == 0 else 'right',
                            color="#000000",
                            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.7))

            ax.set_xlabel("RPM (revolutions per minute)", color="#000000")
            ax.set_ylabel("Efficiency (dimensionless)", color="#000000")
            ax.set_title("Propeller Efficiency Comparison")
            ax.tick_params(axis='both', colors="#000000")
            ax.grid(True, color="gray", linestyle="--", linewidth=0.5)
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2)
            st.pyplot(fig)

            st.markdown("""
            **Interpretation:**
            - The blue and orange curves show how efficiency varies with RPM.
            - Black peak markers highlight the maximum efficiency points.
            - This comparison highlights which propeller is more efficient in your chosen range.
            """)

        # --- Fuel & CO₂ Impact ---
        with tab2:
            fig, ax = plt.subplots()
            ax.plot(df1_filtered['RPM'], df1_filtered['PWR']*746, label=f"{prop1_label} Power", color="#4682b4", linewidth=2.5)
            ax.plot(df2_filtered['RPM'], df2_filtered['PWR']*746, label=f"{prop2_label} Power", color="#D98C00", linewidth=1.5)

            ax.set_xlabel("RPM")
            ax.set_ylabel("Power (Watts)")
            ax.set_title("Power Consumption Comparison")
            ax.legend()
            st.pyplot(fig)

            co2_1 = (df1_filtered['PWR']*746)/3600000 * 0.7
            co2_2 = (df2_filtered['PWR']*746)/3600000 * 0.7
            fig2, ax2 = plt.subplots()
            ax2.plot(df1_filtered['RPM'], co2_1, label=f"{prop1_label} CO₂", color="#228b22", linewidth=2.5)
            ax2.plot(df2_filtered['RPM'], co2_2, label=f"{prop2_label} CO₂", color="#b22222", linewidth=1.5)

            ax2.set_ylabel("CO₂ Emissions (kg)")
            ax2.set_title("CO₂ Emissions Comparison")
            ax2.legend()
            st.pyplot(fig2)

            st.markdown("""
            **Interpretation:**
            - The blue/orange curves show how much power each propeller requires across RPM.
            - The green/red curves show the corresponding CO₂ emissions.
            - Comparing these curves helps you see which propeller consumes less energy and produces fewer emissions in the same RPM range.
            """)

        # --- Suggestions ---
        with tab3:
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
            - **{prop1_label}**:  
              → Lower RPM saves ~{savings_pct1:.1f}% power  
              → CO₂ reduction: {co2_savings1*1000:.2f} g/hr  
              → Typical use: *{prop1_info['Use']}*
            """)
            st.markdown(f"""
            - **{prop2_label}**:  
              → Lower RPM saves ~{savings_pct2:.1f}% power  
              → CO₂ reduction: {co2_savings2*1000:.2f} g/hr  
              → Typical use: *{prop2_info['Use']}*
            """)

            if avg_power1 < avg_power2:
                better_prop = prop1_label
                diff_power = avg_power2 - avg_power1
                diff_co2 = (avg_power2 - avg_power1)/3600000 * 0.7
            else:
                better_prop = prop2_label
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
