import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="CSV Customiser", page_icon="📦", layout="wide")

st.title("📦 CSV Customiser App")
st.write("Upload your subscription .csv file, and I’ll automatically customise it for Click & Drop export.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # --- Normalise and clean column names ---
    df.columns = df.columns.map(lambda x: str(x).strip())
    df.columns = df.columns.map(lambda x: x.replace("\n", " ").strip())

    # Lowercase copy for easier matching
    lower_cols = [c.lower() for c in df.columns]

    # --- Helper to find columns by name (case-insensitive, partial match) ---
    def find_col(possible_names):
        for name in possible_names:
            for col in df.columns:
                if name.lower() in str(col).lower():
                    return col
        return None

    # --- Identify important columns ---
    shipping_col = find_col(["shipping country", "ship country", "country"])
    product_len_col = find_col(["product length", "length"])
    product_id_col = find_col(["product id", "sku", "id"])
    product_name_col = find_col(["product name", "name"])
    notes_col = find_col(["notes", "comment", "phone"])
    price_col = find_col(["product price", "price"])
    order_total_col = find_col(["order total", "total"])
    order_postage_col = find_col(["order postage", "postage", "shipping cost"])

    # --- Insert new columns after product length if found ---
    if product_len_col:
        idx = df.columns.get_loc(product_len_col)
        df.insert(idx + 1, "Product weight", "")
        df.insert(idx + 2, "Package Size", "")
        df.insert(idx + 3, "Service Code", "")
    else:
        st.warning("⚠️ 'Product length' column not found — adding new columns at end.")
        for col in ["Product weight", "Package Size", "Service Code"]:
            if col not in df.columns:
                df[col] = ""

    # Always add IOSS at the end
    if "IOSS" not in df.columns:
        df["IOSS"] = ""

    # --- Define product rules ---
    bundles = ["iljcpq05", "ay5cwt7h", "y23m38jk", "nn5wwlw1", "rfa96qoe", "b4q2b6wi"]
    mag_only = ["j6a63izr", "h05r1t4s", "Ljae93q8"]

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

    if product_id_col:
        df["Product weight"] = df[product_id_col].astype(str).apply(assign_weight)

    # --- EU countries for IOSS ---
    eu_countries = [
        "Austria","Belgium","Bulgaria","Croatia","Cyprus","Czech Republic","Denmark",
        "Estonia","Finland","France","Germany","Greece","Hungary","Ireland","Italy",
        "Latvia","Lithuania","Luxembourg","Malta","Netherlands","Poland","Portugal",
        "Romania","Slovakia","Slovenia","Spain","Sweden"
    ]

    if shipping_col:
        df["IOSS"] = df[shipping_col].apply(
            lambda c: "IM5280003071" if any(eu in str(c) for eu in eu_countries) else ""
        )

    # --- USA orders ---
    if shipping_col:
        usa_mask = df[shipping_col].str.contains("United States", case=False, na=False)

        if notes_col:
            df[notes_col] = df[notes_col].fillna("").astype(str)
            df.loc[usa_mask & (df[notes_col].str.strip() == ""), notes_col] = "123-123-1234"

        df.loc[usa_mask, "Service Code"] = "MPR"
        df.loc[usa_mask, "Package Size"] = "Parcel"

    # --- UK and others ---
    if shipping_col:
        uk_mask = df[shipping_col].str.contains("United Kingdom", case=False, na=False)
        df.loc[uk_mask, "Service Code"] = "CRL48"
        df.loc[df.get(product_id_col, "") == "pjzmis04", "Service Code"] = "TPS48"
        df.loc[~uk_mask, "Service Code"] = "DG4"
        df.loc[df.get(product_id_col, "") == "wl7k4elo", "Service Code"] = "DE4"

    # --- Package size defaults ---
    df.loc[df["Package Size"] == "", "Package Size"] = "Large Letter"
    df.loc[df.get(product_id_col, "").isin(["pjzmis04", "wl7k4elo"]), "Package Size"] = "Parcel"

    # --- Clean product names ---
    valid_names = [
        "12 Month Bundle Subscription",
        "12 Month Mag Only Subscription",
        "Bundle (Print Edition + Vinyl / CD + Web Premium)",
        "Magazine (Print Edition + Web Premium)",
        "Magazine Only monthly subscription",
    ]
    if product_name_col:
        df.loc[~df[product_name_col].isin(valid_names), product_name_col] = ""

    # --- Delete high prices ---
    if price_col:
        mask = pd.to_numeric(df[price_col], errors="coerce") > 19
        for col in [price_col, order_total_col, order_postage_col]:
            if col and col in df.columns:
                df.loc[mask, col] = ""

    # --- Prepare file for download ---
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

else:
    st.info("⬆️ Upload a .csv file to begin.")
