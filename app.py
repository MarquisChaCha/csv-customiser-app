import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="CSV Customiser", page_icon="📦", layout="wide")

st.title("📦 CSV Customiser App")
st.write("Upload your subscription .csv file, and I’ll automatically customise it for Click & Drop export.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # --- Add new columns ---
    if "Product length" in df.columns:
        idx = df.columns.get_loc("Product length")
        df.insert(idx + 1, "Product weight", "")
        df.insert(idx + 2, "Package Size", "")
        df.insert(idx + 3, "Service Code", "")
    else:
        st.error("Couldn't find 'Product length' column.")
        st.stop()

    df["IOSS"] = ""

    # --- Define Product groups ---
    bundles = ["iljcpq05","ay5cwt7h","y23m38jk","nn5wwlw1","rfa96qoe","b4q2b6wi"]
    mag_only = ["j6a63izr","h05r1t4s","Ljae93q8"]

    # --- Set weights ---
    def assign_weight(pid):
        if pid == "wl7k4elo":
            return 0.920
        elif pid == "pjzmis04":
            return 0.980
        elif pid in bundles:
            return 0.490
        elif pid in mag_only:
            return 0.430
        return ""

    df["Product weight"] = df["Product ID"].apply(assign_weight)

    # --- EU Countries (IOSS applies) ---
    eu_countries = [
        "Austria","Belgium","Bulgaria","Croatia","Cyprus","Czech Republic","Denmark","Estonia","Finland","France",
        "Germany","Greece","Hungary","Ireland","Italy","Latvia","Lithuania","Luxembourg","Malta","Netherlands",
        "Poland","Portugal","Romania","Slovakia","Slovenia","Spain","Sweden"
    ]

    df["IOSS"] = df.apply(
        lambda row: "IM5280003071" if any(c in str(row.get("Shipping country", "")) for c in eu_countries) else "",
        axis=1
    )

    # --- USA phone + service codes ---
    df["Notes"] = df["Notes"].fillna("").astype(str)
    df.loc[df["Shipping country"].str.contains("United States", case=False, na=False) &
           (df["Notes"].str.strip() == ""), "Notes"] = "123-123-1234"

    df.loc[df["Shipping country"].str.contains("United States", case=False, na=False), "Service Code"] = "MPR"
    df.loc[df["Shipping country"].str.contains("United States", case=False, na=False), "Package Size"] = "Parcel"

    # --- UK + rest of world rules ---
    df.loc[df["Shipping country"].str.contains("United Kingdom", case=False, na=False), "Service Code"] = "CRL48"
    df.loc[df["Product ID"] == "pjzmis04", "Service Code"] = "TPS48"
    df.loc[df["Shipping country"].str.contains("United Kingdom", case=False, na=False) == False, "Service Code"] = "DG4"
    df.loc[df["Product ID"] == "wl7k4elo", "Service Code"] = "DE4"

    # --- Package Size adjustments ---
    df.loc[df["Package Size"] == "", "Package Size"] = "Large Letter"
    df.loc[df["Product ID"].isin(["pjzmis04", "wl7k4elo"]), "Package Size"] = "Parcel"

    # --- Product name cleanup ---
    valid_names = [
        "12 Month Bundle Subscription",
        "12 Month Mag Only Subscription",
        "Bundle (Print Edition + Vinyl / CD + Web Premium)",
        "Magazine (Print Edition + Web Premium)",
        "Magazine Only monthly subscription"
    ]
    df.loc[~df["Product name"].isin(valid_names), "Product name"] = ""

    # --- Delete high prices ---
    if "Product price" in df.columns:
        mask = df["Product price"] > 19
        for col in ["Product price", "Order total", "Order postage"]:
            if col in df.columns:
                df.loc[mask, col] = ""

    # --- Export result ---
    output = BytesIO()
    filename = f"AUTO_CONVERTED_WEIGHT+IOSS_ADDED_{uploaded_file.name}"
    df.to_csv(output, index=False)
    output.seek(0)

    st.success("✅ File processed successfully!")
    st.download_button(
        label="📥 Download customised CSV",
        data=output,
        file_name=filename,
        mime="text/csv"
    )
