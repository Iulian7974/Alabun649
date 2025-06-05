
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

import streamlit as st

with st.expander("🔮 Predicție ML (10 numere din ultimele 20 extrageri)"):
    import json
    try:
        with open("predictie_ml_10numere.json", "r") as f:
            data = json.load(f)
            pred_10 = data.get("predictie_10numere", [])
            st.subheader("🎯 Recomandare model ML (10 numere):")
            st.write(sorted(pred_10))
    except Exception as e:
        st.warning("Nu există fișier de predicție sau a apărut o eroare.")


with st.expander("📊 Compară predicția cu ultimele extrageri"):
    try:
        with open("predictie_ml_10numere.json", "r") as f:
            pred_10 = set(json.load(f).get("predictie_10numere", []))

        df_recent = df.sort_values("Data", ascending=False).head(5)
        st.write("📅 Ultimele 5 extrageri:")
        for _, row in df_recent.iterrows():
            extragere = set(row[['Nr.1', 'Nr.2', 'Nr.3', 'Nr.4', 'Nr.5', 'Nr.6']].values)
            intersectie = sorted(pred_10.intersection(extragere))
            st.write(f"🔸 {row['Data'].date()} → {sorted(extragere)}")
            st.write(f"   ✅ Numere prezise corect: {intersectie}")
    except Exception as e:
        st.warning(f"Eroare la comparare: {e}")


    # === Salvare istoric comparații ===
    try:
        istoric_cmp_path = "istoric_comparatii.json"
        if os.path.exists(istoric_cmp_path):
            with open(istoric_cmp_path, "r") as f:
                istoric_cmp = json.load(f)
        else:
            istoric_cmp = []

        for _, row in df_recent.iterrows():
            extragere = sorted(set(row[['Nr.1', 'Nr.2', 'Nr.3', 'Nr.4', 'Nr.5', 'Nr.6']].values))
            intersectie = sorted(pred_10.intersection(extragere))
            istoric_cmp.append({
                "data_extragere": str(row["Data"].date()),
                "numere_extrase": extragere,
                "corecte": intersectie,
                "total_corecte": len(intersectie)
            })

        with open(istoric_cmp_path, "w") as f:
            json.dump(istoric_cmp, f, indent=2)

        st.success("📚 Comparațiile au fost salvate în istoric.")
    except Exception as e:
        st.warning(f"Eroare la salvarea istoric comparații: {e}")


with st.expander("📈 Istoric comparații ML"):
    try:
        with open("istoric_comparatii.json", "r") as f:
            istoric_cmp = json.load(f)
            df_istoric = pd.DataFrame(istoric_cmp)
            df_istoric['data_extragere'] = pd.to_datetime(df_istoric['data_extragere'])
            df_istoric = df_istoric.sort_values("data_extragere", ascending=False)

            st.dataframe(df_istoric[['data_extragere', 'numere_extrase', 'corecte', 'total_corecte']])
            st.line_chart(df_istoric.set_index("data_extragere")["total_corecte"])
    except Exception as e:
        st.warning("📂 Nu există istoric sau a apărut o eroare.")


with st.expander("⬇️ Export istoric comparații în CSV"):
    try:
        if 'df_istoric' in locals():
            csv_export = df_istoric.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descarcă fișier CSV", data=csv_export, file_name="istoric_comparatii.csv", mime="text/csv")
        else:
            st.info("📄 Istoricul nu este încă disponibil.")
    except Exception as e:
        st.warning("Eroare la generarea fișierului CSV.")


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

def trimite_email(data, scor, corecte, extragere):
    if not (EMAIL_USER and EMAIL_PASS and EMAIL_TO):
        st.warning("⚠️ Nu există date de email în .env. Emailul nu a fost trimis.")
        return

    subject = f"Loto ML: {scor} numere prezise corect pe {data}"
    body = f"""🔮 Predicție ML a avut {scor} numere corecte!

Data extragerii: {data}
Numere extrase: {sorted(extragere)}
Corecte prezise: {sorted(corecte)}
"""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
        server.quit()
        st.success(f"📧 Email trimis cu scorul {scor} pentru {data}")
    except Exception as e:
        st.error(f"Eroare la trimiterea emailului: {e}")

# Verificare trimis automat pentru scor >= 4
for cmp in istoric_cmp[-5:]:
    if cmp["total_corecte"] >= 4:
        trimite_email(cmp["data_extragere"], cmp["total_corecte"], cmp["corecte"], cmp["numere_extrase"])


with st.expander("✉️ Trimite email de test"):
    if st.button("📧 Trimite un email de test"):
        try:
            trimite_email("TEST", 6, [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6])
        except Exception as e:
            st.error(f"Eroare la trimiterea emailului de test: {e}")


with st.expander("📊 Evoluția scorului ML"):
    try:
        df_istoric['Scor Corecte'] = df_istoric['total_corecte']
        media = df_istoric['Scor Corecte'].mean()
        st.metric("⚙️ Scor mediu ML", f"{media:.2f} numere prezise corect")

        fig, ax = plt.subplots()
        ax.plot(df_istoric['data_extragere'], df_istoric['Scor Corecte'], marker='o')
        ax.axhline(media, color='gray', linestyle='--', label='Media')
        ax.set_title("📈 Număr de predicții corecte în timp")
        ax.set_xlabel("Data")
        ax.set_ylabel("Numere corecte")
        ax.legend()
        st.pyplot(fig)
    except Exception as e:
        st.warning("⚠️ Nu s-a putut calcula scorul mediu.")


with st.expander("🎯 Compară cu selecții aleatorii"):
    import random

    try:
        rezultate_random = []
        for extragere in istoric_cmp:
            random_predictie = random.sample(range(1, 50), 10)
            corecte = set(extragere["numere_extrase"]).intersection(random_predictie)
            rezultate_random.append(len(corecte))

        scoruri_ml = [e["total_corecte"] for e in istoric_cmp]
        scoruri_random = rezultate_random

        fig, ax = plt.subplots()
        ax.plot(scoruri_ml, label="ML", marker="o")
        ax.plot(scoruri_random, label="Aleatoriu", marker="x", linestyle="--")
        ax.set_title("📊 ML vs. Aleatoriu - Numere corecte")
        ax.set_ylabel("Numere corecte din 10")
        ax.set_xlabel("Extragere #")
        ax.legend()
        st.pyplot(fig)

        media_ml = sum(scoruri_ml) / len(scoruri_ml)
        media_random = sum(scoruri_random) / len(scoruri_random)
        st.write(f"📈 Scor mediu ML: **{media_ml:.2f}**")
        st.write(f"🎲 Scor mediu aleatoriu: **{media_random:.2f}**")
    except Exception as e:
        st.error("Eroare la compararea cu selecții aleatorii.")


with st.expander("💾 Export scoruri în CSV"):
    try:
        df_istoric.to_csv("scoruri_predictie.csv", index=False)
        with open("scoruri_predictie.csv", "rb") as f:
            st.download_button(
                label="📥 Descarcă scoruri ML (CSV)",
                data=f,
                file_name="scoruri_predictie.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error("❌ Eroare la generarea fișierului CSV.")


with st.expander("📤 Încarcă extrageri noi (Excel)"):
    uploaded_new = st.file_uploader("Încarcă un fișier Excel cu extrageri noi (format identic)", type=["xlsx"])

    if uploaded_new:
        try:
            df_new = pd.read_excel(uploaded_new)
            df_new['Data'] = pd.to_datetime(df_new['Data'], errors='coerce')
            df_new[draw_cols] = df_new[draw_cols].applymap(int)
            df_new = df_new.dropna(subset=['Data'])

            # Concatenează și elimină duplicate
            df_combined = pd.concat([df, df_new])
            df_combined = df_combined.drop_duplicates(subset=['Data'] + draw_cols).sort_values("Data")

            # Suprascrie baza de date
            conn = sqlite3.connect(DB_NAME)
            df_combined.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
            conn.commit()
            conn.close()

            st.success(f"✅ {len(df_new)} extrageri noi adăugate. Baza de date actualizată.")

        except Exception as e:
            st.error(f"Eroare la încărcarea fișierului: {e}")
