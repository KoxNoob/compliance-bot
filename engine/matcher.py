from rapidfuzz import process, fuzz
import itertools
import pandas as pd


def get_language(text: str) -> str:
    return "en"


CONCEPT_GROUPS = {
    "cup": ["cup", "coupe", "coppa", "copa", "taça", "taca"],
    "spain": ["spain", "spanish", "espagne", "espagnol", "españa", "rey", "roi"],
    "italy": ["italy", "italian", "italie", "italien", "italia"],
    "portugal": ["portugal", "portuguese", "portugais", "portugaise"],
    "france": ["france", "french", "français", "française"],
    "germany": ["germany", "german", "allemagne", "allemand", "deutschland"],
    "scotland": ["scotland", "scottish", "ecosse"],
    "switzerland": ["swiss", "suisse", "switzerland"]
}


def normalize(text: str) -> str:
    if not isinstance(text, str): return ""
    t = text.lower().strip()
    words_to_remove = ['?', '!', '.', ',', '-', '_', ' da ', ' de ', ' la ', ' le ', ' the ', ' du ', ' gas ']
    for word in words_to_remove:
        t = t.replace(word, ' ')
    return " ".join(t.split())


def generate_variations(query: str) -> list:
    query_words = normalize(query).split()
    words_possibilities = []
    for word in query_words:
        found_group = False
        for key, variants in CONCEPT_GROUPS.items():
            if word == key or word in variants:
                words_possibilities.append(list(set([word] + variants)))
                found_group = True
                break
        if not found_group:
            words_possibilities.append([word])
    combos = list(itertools.product(*words_possibilities))
    return [" ".join(c) for c in combos][:15]


def get_matches_multiples(query, df_anj, threshold=60):
    if df_anj.empty: return []

    # --- INITIALISATION DES VARIABLES MANQUANTES ---
    user_query = query
    user_norm = normalize(query)

    # --- SÉCURISATION DES COLONNES ---
    # On identifie les index dynamiquement pour ne pas planter si Genre ou Pays manque
    cols_in_df = df_anj.columns.tolist()

    # On prépare un dictionnaire pour savoir où est quoi dans 'opt'
    idx_map = {col: i for i, col in enumerate(["Nom commun", "Genre", "Pays"]) if col in cols_in_df}
    available_cols = [col for col in ["Nom commun", "Genre", "Pays"] if col in cols_in_df]

    # On ne prend que les colonnes existantes
    competition_options = df_anj[available_cols].drop_duplicates().values.tolist()

    # 1. DÉTECTION DU PAYS
    target_country_key = None
    for key, variants in CONCEPT_GROUPS.items():
        if key == "cup": continue
        if any(v in user_norm for v in variants):
            target_country_key = key
            break

    # 2. GÉNÉRATION DES VARIANTES
    user_variations = generate_variations(user_query)

    scored_results = []
    for opt in competition_options:
        # Récupération sécurisée des valeurs
        db_name = normalize(opt[idx_map["Nom commun"]])
        db_genre = opt[idx_map["Genre"]] if "Genre" in idx_map else "N/A"
        db_country = str(opt[idx_map["Pays"]]).lower() if "Pays" in idx_map else "international"

        combined_target = f"{db_name} {db_country}"

        best_var_score = 0
        for var in user_variations:
            var_score = fuzz.token_set_ratio(var, combined_target)
            if var_score > best_var_score:
                best_var_score = var_score

        score = best_var_score

        # --- AJUSTEMENTS ---
        if target_country_key:
            country_variants = CONCEPT_GROUPS[target_country_key]
            if any(v in db_country for v in country_variants):
                score += 10
            elif db_country != "international":
                score -= 30

        if "super" in db_name and "super" not in user_norm:
            score -= 15

        if score >= threshold:
            # On stocke (Nom, Score, Genre)
            scored_results.append((opt[idx_map["Nom commun"]], score, db_genre))

    scored_results.sort(key=lambda x: x[1], reverse=True)
    if not scored_results: return []

    best_score = scored_results[0][1]
    valid_matches = []
    seen = set()

    for res in scored_results:
        if res[1] >= (best_score - 10):
            key = f"{res[0]}_{res[2]}"
            if key not in seen:
                valid_matches.append(res)
                seen.add(key)

    return valid_matches