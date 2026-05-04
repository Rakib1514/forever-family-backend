import re
from thefuzz import fuzz

PREFIXES = [
    'md.', 'md', 'mst.', 'mst', 'mr.', 'mr', 'mrs.', 'mrs', 
    'dr.', 'dr', 'eng.', 'eng', 'doc.', 'doc'
]
# Regex to match prefixes as whole words, ignoring case
PREFIX_PATTERN = r'\b(?:' + '|'.join(map(re.escape, PREFIXES)) + r')\b'

def normalize_name(name):
    if not name:
        return ""
    name = name.lower()
    # Remove prefixes
    name = re.sub(PREFIX_PATTERN, '', name)
    # Remove special characters
    name = re.sub(r'[^a-z0-9\s]', '', name)
    # Remove extra spaces
    name = ' '.join(name.split())
    return name

def calculate_similarity(name1, name2):
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    if not n1 or not n2:
        return 0
    # token_set_ratio ignores word order and duplicates (e.g., "John Doe" vs "Doe John")
    return fuzz.token_set_ratio(n1, n2)

def check_duplicate_user(birth_date, first_name, last_name, nick_name, father_name, mother_name):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not birth_date:
        return "ALLOW"
        
    # Step 1: Filter by exact birth_date
    candidates = User.objects.filter(birth_date=birth_date)
    if not candidates.exists():
        return "ALLOW"
        
    target_name = f"{first_name or ''} {last_name or ''} {nick_name or ''}".strip()
    
    max_score = 0
    for user in candidates:
        user_name = f"{user.first_name or ''} {user.last_name or ''} {user.nick_name or ''}".strip()
        score_self = calculate_similarity(target_name, user_name)
        
        # Father
        user_father_name = ""
        if user.father:
            user_father_name = f"{user.father.first_name or ''} {user.father.last_name or ''}"
        score_father = calculate_similarity(father_name, user_father_name) if father_name and user_father_name else None
        
        # Mother
        user_mother_name = ""
        if user.mother:
            user_mother_name = f"{user.mother.first_name or ''} {user.mother.last_name or ''}"
        score_mother = calculate_similarity(mother_name, user_mother_name) if mother_name and user_mother_name else None
        
        # Calculate combined weighted score
        weights = [1.0] # Weight for self name
        scores = [score_self]
        
        if score_father is not None:
            weights.append(0.5) # Weight for father's name
            scores.append(score_father)
            
        if score_mother is not None:
            weights.append(0.5) # Weight for mother's name
            scores.append(score_mother)
            
        final_score = sum(w * s for w, s in zip(weights, scores)) / sum(weights)
        
        if final_score > max_score:
            max_score = final_score

    # Thresholds
    if max_score > 85:
        return "VERY_LIKELY_DUPLICATE"
    elif max_score > 65:
        return "POSSIBLE_DUPLICATE"
    
    return "ALLOW"
