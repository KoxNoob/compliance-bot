import pandas as pd
import re
from engine.anj_loader import COMPETITION_COL, GENRE_COL, DISCIPLINE_COL, RESTRICTION_COL, PHASES_COL, COUNTRY_COL


def clean_string(s):
    if pd.isna(s): return ""
    return re.sub(r'[^a-z0-9]', '', str(s).lower())


def handle_badminton_search(user_prompt, df_anj, selected_discipline):
    # 1. TRADUCTION PRÉVENTIVE
    # On transforme la requête pour qu'elle contienne les mots du fichier Excel FR
    query_raw = user_prompt.lower()
    mapping_keywords = {
        "olympic games": "jeux olympiques",
        "olympic": "olympiques",
        "european games": "jeux europeens",
        "european championship": "championnat d'europe",
        "world championship": "championnat du monde",
        "world championships": "championnat du monde"
    }
    for eng, fr in mapping_keywords.items():
        query_raw = query_raw.replace(eng, fr)

    # 2. NETTOYAGE FINAL
    query_clean = clean_string(query_raw).replace("bwf", "")
    matches = []

    # 3. LOGIQUE DE RECHERCHE
    for idx, row in df_anj.iterrows():
        file_name_orig = str(row[COMPETITION_COL])
        file_name_clean = clean_string(file_name_orig).replace("bwf", "")

        # Test de correspondance
        if query_clean in file_name_clean or file_name_clean in query_clean:

            file_genre = str(row[GENRE_COL]).lower()
            file_discipline = str(row[DISCIPLINE_COL]).lower()

            # --- CAS A : LES "CUPS" (Uber, Thomas, Sudirman) ---
            # On bypass la discipline stricte car ce sont des tournois mixtes/equipes
            is_cup = any(word in file_name_clean for word in ["uber", "thomas", "sudirman"])

            if is_cup:
                if "uber" in query_clean and "uber" in file_name_clean:
                    matches.append((file_name_orig, 100, row[GENRE_COL]))
                elif "thomas" in query_clean and "thomas" in file_name_clean:
                    matches.append((file_name_orig, 100, row[GENRE_COL]))
                elif "sudirman" in query_clean and "sudirman" in file_name_clean:
                    matches.append((file_name_orig, 100, row[GENRE_COL]))

            # --- CAS B : JEUX OLYMPIQUES / EUROPÉENS / CHAMPIONNATS ---
            else:
                # On vérifie si la discipline choisie (Singles/Doubles) est incluse dans la colonne du fichier
                # (Gère "Simple", "Double", ou "Simple et double")
                search_val = "simple" if selected_discipline == "Singles" else "double"
                if search_val in file_discipline:
                    matches.append((file_name_orig, 100, row[GENRE_COL]))

    return list(set(matches))


def decide_badminton(comp_name: str, df: pd.DataFrame, genre: str = None, discipline: str = None):
    # On cherche la ligne
    mask = (df[COMPETITION_COL] == comp_name)
    if genre:
        mask = mask & (df[GENRE_COL] == genre)

    try:
        rows = df[mask]
        if rows.empty:
            # Fallback sans le genre si besoin
            row = df[df[COMPETITION_COL] == comp_name].iloc[0]
        else:
            row = rows.iloc[0]

        return {
            "allowed": True,
            "competition": comp_name,
            "restrictions": str(row[RESTRICTION_COL]) if not pd.isna(row[RESTRICTION_COL]) else "NONE",
            "phases": str(row[PHASES_COL]) if not pd.isna(row[PHASES_COL]) else "ALL",
            "source": df.attrs.get('source_ref', "ANJ Source"),
            "country": str(row[COUNTRY_COL]) if not pd.isna(row[COUNTRY_COL]) else "International",
            "sport": "Badminton",
            "genre": str(row[GENRE_COL])
        }
    except:
        return {"allowed": False, "competition": comp_name}