import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="CSV Customiser", page_icon="📦")
st.title("📦 CSV Customiser Tool")
st.write("Upload your .csv and I’ll apply your rules automatically!")

# --- Constants & Setup ---
IOSS_NUMBER = "IM5280003071"
GENERIC_US_PHONE = "123-123-1234"

BUNDLE_IDS = {"iljcpq05", "ay5cwt7h", "y23m38jk", "nn5wwlw1", "rfa96qoe", "b4q2b6wi"}
MAGONLY_IDS = {"j6a63izr", "h05r1t4s", "ljae93q8"}
WEIGHT_EXCEPTIONS = {"wl7k4elo": 0.920, "pjzmis04": 0.980}
WEIGHT_BUNDLE = 0.490
WEIGHT_MAGONLY = 0.430

ALLOWED_PRODUCT_NAMES = {
    "12 Month Bundle Subscription",
    "12 Month Mag Only Subscription",
    "Bundle (Print Edition + Vinyl / CD + Web Premium)",
    "Magazine (Print Edition + Web Premium)",
    "Magazine Only monthly subscription",
}

EU_COUNTRIES = {
    "austria","belgium","bulgaria","croatia","cyprus","czechia","czech republic",
    "denmark","estonia","finland","france","germany","greece","hungary","ireland",
    "italy","latvia","lithuania","luxembourg","malta","netherlands","poland",
    "portugal","romania","slovakia","slovenia","spain","sweden"
}
USA_NAMES = {"united states","united states of america","usa","us"}
UK_NAMES = {"united kingdom","uk","great britain","britain","england","scotland","wales","northern ireland"}

def normalize_country(v):
    if pd.isna(v): return ""
    return str(v).strip().lower()

def has_phone(text):
    if pd.isna(text): return False
    return bool(re.search(r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\+\d{1,3}\s?\d{4,}", str(text)))

def process_csv(df):
    def find_col(df, guesses):
        cols_lower = {c.lower(): c for c in df.columns}
        for g in guesses:
            if g.lower() in cols_lower:
                return cols_lower[g.lower()]
        for c_l, c_orig in cols_lower.items():
            for g in guesses:
                if g.lower() in c_l:
                    return c_orig
        return None

    product_id_col = find_col(df, ["Product ID","ProductID"])
    product_name_col = find_col(df, ["Product name"])
    product_length_col = find_col(df, ["Product length"])
    notes_col = find_col(df, ["Notes"])
    country_col = find_col(df, ["Country"])
    product_price_col = find_col(df, ["Product price"])
    order_total_col = find_col(df, ["Order total"])
    order_postage_col = find_col(df, ["Order postage"])

    for c in [product_id_col, product_name_col, notes_col, country_col,
              product_price_col, order_total_col, order_postage_col]:
        if c not in df.columns:
            df[c] = ""

    insert_at = list(df.columns).index(product_length_col)+1 if product_length_col in df.columns else len(df.columns)
    for i,colname in enumerate(["Product weight","Package Size","Service Code"]):
        if colname not in df.columns:
            df.insert(insert_at+i, colname, "")
    if "IOSS" not in df.columns:
        df["IOSS"] = ""

    def process_row(row):
        pid = str(row[product_id_col]).strip().lower() if pd.notna(row[product_id_col]) else ""
        country = normalize_country(row[country_col])
        pname = str(row[product_name_col]).strip()

        if pid in WEIGHT_EXCEPTIONS:
            weight = WEIGHT_EXCEPTIONS[pid]
        elif pid in BUNDLE_IDS:
            weight = WEIGHT_BUNDLE
        elif pid in MAGONLY_IDS:
            weight = WEIGHT_MAGONLY
        else:
            weight = ""
        row["Product weight"] = weight

        row["IOSS"] = IOSS_NUMBER if country in EU_COUNTRIES else ""

        if country in USA_NAMES:
            row["Package Size"] = "Parcel"
            row["Service Code"] = "MPR"
            if not has_phone(row[notes_col]):
                # clean nan and add phone only
                row[notes_col] = GENERIC_US_PHONE
        else:
            if pid in {"pjzmis04","wl7k4elo"}:
                row["Package Size"] = "Parcel"
            else:
                row["Package Size"] = "Large Letter"

            if country in UK_NAMES:
                row["Service Code"] = "TPS48" if pid=="pjzmis04" else "CRL48"
            else:
                row["Service Code"] = "DE4" if pid=="wl7k4elo" else "DG4"

        if pname not in ALLOWED_PRODUCT_NAMES:
            row[product_name_col] = ""

        try:
            price = float(re.sub(r"[^\d.]", "", str(row[product_price_col]))) if row[product_price_col] else 0
        except:
            price = 0
        if price > 19:
            row[product_price_col] = ""
            row[order_total_col] = ""
            row[order_postage_col] = ""
        return row

    return df.apply(process_row, axis=1)

uploaded = st.file_uploader("Upload CSV file", type="csv")
if uploaded:
    df = pd.read_csv(uploaded, dtype=str)
    st.success("✅ File uploaded successfully!")
    if st.button("Process File"):
        processed = process_csv(df)
        st.success("🎉 Done! Click below to download.")
        csv_bytes = processed.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Processed CSV",
            data=csv_bytes,
            file_name=f"AUTO_CONVERTED_WEIGHT+IOSS_ADDED_{uploaded.name}",
            mime="text/csv",
        )

