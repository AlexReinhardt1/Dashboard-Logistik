import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import locale

# Sprache für Monatsnamen auf Deutsch
try:
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'deu')

# 🚚 Ordnerpfade
ordner_cc = r"P:\bellissa\Lagerleitung\KPI\Durchlaufzeiten\2025\C&C\TEST"
ordner_gaz = r"P:\bellissa\Lagerleitung\KPI\Durchlaufzeiten\2025\GAZ\TEST"

# 📊 Daten laden & analysieren
def lade_und_analysiere_daten(pfad):
    dateien = [f for f in os.listdir(pfad) if f.endswith("_fertig.csv")]
    daten = []

    for datei in dateien:
        try:
            datum = datetime.strptime(f"{datei[:5]}.2025", "%d.%m.%Y")
        except:
            continue

        df = pd.read_csv(os.path.join(pfad, datei), sep=";", encoding="utf-8")
        if "Durchlaufzeit" not in df.columns:
            continue

        df = df[df["Durchlaufzeit"].notna()]
        df["Durchlaufzeit"] = pd.to_numeric(df["Durchlaufzeit"], errors="coerce")

        if df.empty:
            continue

        anzahl = len(df)
        unter_24 = (df["Durchlaufzeit"] <= 24).sum()
        quote = round((unter_24 / anzahl) * 100, 1)
        avg = round(df["Durchlaufzeit"].mean(), 1)

        daten.append({
            "Datum": datum.strftime("%d.%m.%Y"),
            "Aufträge Gesamt": anzahl,
            "Aufträge <24h": unter_24,
            "Lieferquote <24h (%)": quote,
            "Ø Tages-Durchlaufzeit (h)": avg,
            "Monat": datum.strftime("%B"),
            "Jahr": datum.year,
            "Monat_Num": datum.month
        })

    df_tag = pd.DataFrame(daten)
    if df_tag.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_tag = df_tag.sort_values("Datum", ascending=False)

    df_monat = df_tag.groupby(["Jahr", "Monat", "Monat_Num"], as_index=False).agg({
        "Aufträge Gesamt": "sum",
        "Aufträge <24h": "sum",
        "Lieferquote <24h (%)": "mean",
        "Ø Tages-Durchlaufzeit (h)": "mean"
    })

    df_monat = df_monat.sort_values(["Jahr", "Monat_Num"], ascending=[False, False])
    df_monat["Lieferquote <24h (%)"] = df_monat["Lieferquote <24h (%)"].round(1)
    df_monat["Ø Tages-Durchlaufzeit (h)"] = df_monat["Ø Tages-Durchlaufzeit (h)"].round(1)
    df_monat = df_monat.drop(columns=["Monat_Num"])

    return df_tag, df_monat

# 🌀 Daten aktualisieren
def aktualisiere_daten():
    os.system(f'start /min cmd /c "cd /d {ordner_cc} && python durchlaufzeit_berechnung.py"')
    os.system(f'start /min cmd /c "cd /d {ordner_gaz} && python durchlaufzeit_berechnung.py"')

# 🧭 Streamlit Layout
st.set_page_config(layout="wide")
st.title("📦 Dashboard – Logistik")

if st.button("🔄 Daten aktualisieren"):
    aktualisiere_daten()

# Funktion zur Anzeige
def zeige_tabellen(name, df_tag, df_monat):
    st.subheader(f"📦 {name} Versandmonitor")
    if not df_tag.empty:
        st.dataframe(df_tag[["Datum", "Aufträge Gesamt", "Aufträge <24h", "Lieferquote <24h (%)", "Ø Tages-Durchlaufzeit (h)"]],
                     use_container_width=True, hide_index=True, height=270)
    else:
        st.info("Keine Tagesdaten verfügbar.")

    st.subheader(f"📊 {name} Monatsauswertung")
    if not df_monat.empty:
        st.dataframe(df_monat[["Monat", "Jahr", "Aufträge Gesamt", "Aufträge <24h", "Lieferquote <24h (%)", "Ø Tages-Durchlaufzeit (h)"]],
                     use_container_width=True, hide_index=True, height=240)
    else:
        st.info("Keine Monatsdaten verfügbar.")

# Daten anzeigen
df_cc_tag, df_cc_monat = lade_und_analysiere_daten(ordner_cc)
zeige_tabellen("C&C", df_cc_tag, df_cc_monat)

df_gaz_tag, df_gaz_monat = lade_und_analysiere_daten(ordner_gaz)
zeige_tabellen("GAZ", df_gaz_tag, df_gaz_monat)
