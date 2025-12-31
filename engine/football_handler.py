import pandas as pd
from engine.matcher import get_matches_multiples
from engine.anj_loader import COMPETITION_COL, GENRE_COL, RESTRICTION_COL, PHASES_COL, COUNTRY_COL


def handle_football_search(user_prompt, df_anj):
    """Logique de recherche dédiée au Football (Version Stable)"""
    query = user_prompt.lower()
    # Mapping spécifique au football
    mapping = {
        "olympic games": "jeux olympiques",
        "european championship": "championnat d'europe",
        "world cup": "coupe du monde"
    }
    for eng, fr in mapping.items():
        query = query.replace(eng, fr)

    return get_matches_multiples(query, df_anj, threshold=60)


def decide_football(comp_name: str, df: pd.DataFrame, genre: str = None):
    """Logique de décision FIFA et extraction (Version Stable)"""
    try:
        mask = df[COMPETITION_COL].str.lower() == comp_name.lower()
        if genre:
            mask = mask & (df[GENRE_COL].str.lower() == genre.lower())

        row = df[mask].iloc[0]
        restrictions_value = row[RESTRICTION_COL]
        phases_value = row[PHASES_COL]

        if str(restrictions_value).strip() == "Classement FIFA **":
            restrictions_code = "Classement FIFA **"
            phases_code = "** FIFA category A international friendly matches, between two teams both ranked in the top fifty of the FIFA rankings."
        else:
            is_restrictions_none = pd.isna(restrictions_value) or str(restrictions_value).strip().lower() == 'aucune'
            is_phases_none = pd.isna(phases_value) or str(phases_value).strip().lower() == 'aucune'
            restrictions_code = "NONE" if is_restrictions_none else str(restrictions_value)
            phases_code = "ALL" if is_phases_none else str(phases_value)
            if phases_code != "ALL":
                restrictions_code = "LIMITED_PHASES"

        return {
            "allowed": True,
            "competition": comp_name,
            "restrictions": restrictions_code,
            "phases": phases_code,
            "source": df.attrs.get('source_ref', "ANJ Source"),
            "country": str(row[COUNTRY_COL]) if not pd.isna(row[COUNTRY_COL]) else "International",
            "sport": "Football",
            "genre": str(row[GENRE_COL]) if GENRE_COL in row.index else "N/A"
        }
    except:
        return {"allowed": False, "competition": comp_name, "source": df.attrs.get('source_ref')}