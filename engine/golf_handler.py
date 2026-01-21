import pandas as pd
from engine.anj_loader import COMPETITION_COL, GENRE_COL, RESTRICTION_COL, PHASES_COL, COUNTRY_COL


def handle_golf_search(user_prompt, df_anj):
    """Recherche dédiée au Golf avec priorité aux mots-clés"""
    query = user_prompt.lower().strip()

    matches = []
    for idx, row in df_anj.iterrows():
        file_name_orig = str(row[COMPETITION_COL])
        file_name_clean = file_name_orig.lower().strip()

        # Test de correspondance (Exemple: "Ryder" dans "Ryder Cup")
        if query in file_name_clean or file_name_clean in query:
            matches.append((file_name_orig, 100, row[GENRE_COL]))

    return list(set(matches))


def decide_golf(comp_name: str, df: pd.DataFrame, genre: str = None):
    """Logique de décision standard pour le Golf"""
    try:
        mask = (df[COMPETITION_COL] == comp_name)
        if genre:
            mask = mask & (df[GENRE_COL] == genre)

        row = df[mask].iloc[0]

        res_val = row[RESTRICTION_COL]
        pha_val = row[PHASES_COL]

        is_res_none = pd.isna(res_val) or str(res_val).strip().lower() in ['aucune', 'none', 'nan']
        is_pha_none = pd.isna(pha_val) or str(pha_val).strip().lower() in ['aucune', 'none', 'nan']

        return {
            "allowed": True,
            "competition": comp_name,
            "restrictions": "NONE" if is_res_none else str(res_val),
            "phases": "ALL" if is_pha_none else str(pha_val),
            "source": df.attrs.get('source_ref', "ANJ Source"),
            "country": str(row[COUNTRY_COL]) if not pd.isna(row[COUNTRY_COL]) else "International",
            "sport": "Golf",
            "genre": str(row[GENRE_COL])
        }
    except:
        return {"allowed": False, "competition": comp_name}