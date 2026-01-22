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


def get_matches_multiples(user_query: str, df: pd.DataFrame, threshold: int = 65):
    if df.empty: return []

    user_norm = normalize(user_query)
    competition_options = df[["Nom commun", "Genre", "Pays"]].drop_duplicates().values.tolist()

    # 1. DÉTECTION DU PAYS
    target_country_key = None
    for key, variants in CONCEPT_GROUPS.items():
        if key == "cup": continue
        if any(v in user_norm for v in variants):
            target_country_key = key
            break

    # 2. GÉNÉRATION DES VARIANTES (Crucial pour Spanish Cup -> Copa Rey)
    user_variations = generate_variations(user_query)

    scored_results = []
    for opt in competition_options:
        db_name = normalize(opt[0])
        db_country = str(opt[2]).lower()
        combined_target = f"{db_name} {db_country}"

        # On teste chaque variante générée contre le nom en base
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
            scored_results.append((opt[0], score, opt[1]))

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