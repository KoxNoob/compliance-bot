import pandas as pd
import streamlit as st

ANJ_URL = "https://docs.google.com/spreadsheets/d/1vN4_qEFr7b3XmC1v88j4U6v2-M5hS3p6/edit#gid=0"


def load_anj_data(url, sheet_name):
    try:
        file_id = url.split('/')[-2]
        csv_url = f"https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

        # --- TEST DE LECTURE ---
        # Si c'est Foot ou Bad, on essaie d'abord skip=4 (Ligne 5)
        # Mais si on ne trouve pas "Nom commun", on essaie skip=0

        potential_skips = [4, 3, 0, 1] if sheet_name in ["Football", "Badminton"] else [3, 4, 0]
        if sheet_name == "Billard": potential_skips = [3, 0]

        df = pd.DataFrame()
        for s in potential_skips:
            temp_df = pd.read_csv(csv_url, skiprows=s)
            # Nettoyage rapide des colonnes pour le test
            temp_df.columns = [str(c).split('$')[0].strip() for c in temp_df.columns]
            if "Nom commun" in temp_df.columns:
                df = temp_df
                break

        if df.empty:
            return pd.DataFrame()

        # --- NETTOYAGE FINAL ---
        df.columns = [str(c).split('$')[0].strip().replace('\n', ' ') for c in df.columns]

        if "Nom commun" in df.columns:
            df = df.dropna(subset=["Nom commun"])
            df["Nom commun"] = df["Nom commun"].astype(str).str.strip()

        df.attrs['source_ref'] = f"ANJ Regulatory List"
        return df
    except Exception:
        return pd.DataFrame()


def decide_for_sport(comp_name: str, df: pd.DataFrame, sport_name: str):
    """Logique stable : Pas de genre pour Golf/Snooker, genre pour le reste."""
    try:
        comp_name_clean = comp_name.strip()
        # On cherche dans la colonne 'Nom commun' sans se soucier des espaces
        mask = df['Nom commun'].astype(str).str.strip().str.lower() == comp_name_clean.lower()

        if not mask.any():
            return {"allowed": False, "competition": comp_name}

        row = df[mask].iloc[0]

        # On définit les sports sans genre
        if sport_name.lower() in ["snooker", "golf", "billard"]:
            gen = "N/A"
        else:
            gen = str(row.get('Genre', 'Tous'))

        return {
            "allowed": "q-school" not in comp_name.lower(),
            "competition": comp_name,
            "restrictions": str(row.get('Restrictions', 'Aucune')),
            "phases": str(row.get('Phases', 'Toutes')),
            "country": str(row.get('Pays', 'N/A')),
            "genre": gen,
            "sport": sport_name,
            "source": df.attrs.get('source_ref', "ANJ List")
        }
    except:
        return {"allowed": False, "competition": comp_name}


# Constantes de compatibilité
COMPETITION_COL = "Nom commun"
GENRE_COL = "Genre"
RESTRICTION_COL = "Restrictions"
PHASES_COL = "Phases"
COUNTRY_COL = "Pays"
DISCIPLINE_COL = "Discipline"