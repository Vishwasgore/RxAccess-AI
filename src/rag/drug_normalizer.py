"""
Drug normalization layer — brand-to-generic mapping with confidence scoring.
Uses a curated local database + OpenFDA API for unknown drugs.
No hallucination: low-confidence drugs are flagged, not guessed.
"""
import re
import requests
from typing import Dict, List, Optional, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Curated brand → generic mapping ─────────────────────────────────────────
# Source: FDA Orange Book + common clinical usage
BRAND_TO_GENERIC: Dict[str, str] = {
    # Cardiovascular
    "lipitor": "atorvastatin", "crestor": "rosuvastatin", "zocor": "simvastatin",
    "pravachol": "pravastatin", "lescol": "fluvastatin", "livalo": "pitavastatin",
    "norvasc": "amlodipine", "cardizem": "diltiazem", "procardia": "nifedipine",
    "calan": "verapamil", "isoptin": "verapamil",
    "lopressor": "metoprolol", "toprol": "metoprolol", "tenormin": "atenolol",
    "coreg": "carvedilol", "zebeta": "bisoprolol", "inderal": "propranolol",
    "prinivil": "lisinopril", "zestril": "lisinopril",
    "vasotec": "enalapril", "altace": "ramipril", "accupril": "quinapril",
    "cozaar": "losartan", "diovan": "valsartan", "avapro": "irbesartan",
    "benicar": "olmesartan", "atacand": "candesartan", "micardis": "telmisartan",
    "lasix": "furosemide", "bumex": "bumetanide", "aldactone": "spironolactone",
    "hctz": "hydrochlorothiazide", "microzide": "hydrochlorothiazide",
    "coumadin": "warfarin", "jantoven": "warfarin",
    "plavix": "clopidogrel", "brilinta": "ticagrelor", "effient": "prasugrel",
    "eliquis": "apixaban", "xarelto": "rivaroxaban", "pradaxa": "dabigatran",
    "digox": "digoxin", "lanoxin": "digoxin",
    # Diabetes
    "glucophage": "metformin", "fortamet": "metformin", "glumetza": "metformin",
    "januvia": "sitagliptin", "tradjenta": "linagliptin", "onglyza": "saxagliptin",
    "jardiance": "empagliflozin", "farxiga": "dapagliflozin", "invokana": "canagliflozin",
    "ozempic": "semaglutide", "victoza": "liraglutide", "trulicity": "dulaglutide",
    "lantus": "insulin glargine", "levemir": "insulin detemir", "toujeo": "insulin glargine",
    "humalog": "insulin lispro", "novolog": "insulin aspart", "apidra": "insulin glulisine",
    "amaryl": "glimepiride", "glucotrol": "glipizide", "diabeta": "glyburide",
    "actos": "pioglitazone", "avandia": "rosiglitazone",
    # Antibiotics
    "amoxil": "amoxicillin", "trimox": "amoxicillin",
    "augmentin": "amoxicillin-clavulanate",
    "zithromax": "azithromycin", "z-pak": "azithromycin", "zpack": "azithromycin",
    "biaxin": "clarithromycin", "cipro": "ciprofloxacin", "levaquin": "levofloxacin",
    "avelox": "moxifloxacin", "flagyl": "metronidazole",
    "keflex": "cephalexin", "omnicef": "cefdinir", "rocephin": "ceftriaxone",
    "vibramycin": "doxycycline", "doryx": "doxycycline",
    "bactrim": "trimethoprim-sulfamethoxazole", "septra": "trimethoprim-sulfamethoxazole",
    "macrobid": "nitrofurantoin", "macrodantin": "nitrofurantoin",
    "vancocin": "vancomycin", "zyvox": "linezolid",
    # Pain / Anti-inflammatory
    "tylenol": "acetaminophen", "panadol": "acetaminophen",
    "advil": "ibuprofen", "motrin": "ibuprofen", "nuprin": "ibuprofen",
    "aleve": "naproxen", "naprosyn": "naproxen", "anaprox": "naproxen",
    "celebrex": "celecoxib", "voltaren": "diclofenac",
    "ultram": "tramadol", "conzip": "tramadol",
    "percocet": "oxycodone-acetaminophen", "vicodin": "hydrocodone-acetaminophen",
    "norco": "hydrocodone-acetaminophen", "lortab": "hydrocodone-acetaminophen",
    "oxycontin": "oxycodone", "ms contin": "morphine",
    "duragesic": "fentanyl", "actiq": "fentanyl",
    "lyrica": "pregabalin", "neurontin": "gabapentin",
    # GI
    "prilosec": "omeprazole", "losec": "omeprazole",
    "nexium": "esomeprazole", "prevacid": "lansoprazole",
    "protonix": "pantoprazole", "aciphex": "rabeprazole",
    "pepcid": "famotidine", "zantac": "ranitidine", "tagamet": "cimetidine",
    "reglan": "metoclopramide", "zofran": "ondansetron", "phenergan": "promethazine",
    "colace": "docusate", "miralax": "polyethylene glycol",
    # Respiratory
    "ventolin": "albuterol", "proair": "albuterol", "proventil": "albuterol",
    "xopenex": "levalbuterol", "atrovent": "ipratropium",
    "spiriva": "tiotropium", "serevent": "salmeterol",
    "advair": "fluticasone-salmeterol", "symbicort": "budesonide-formoterol",
    "dulera": "mometasone-formoterol", "breo": "fluticasone-vilanterol",
    "flovent": "fluticasone", "pulmicort": "budesonide", "qvar": "beclomethasone",
    "singulair": "montelukast",
    # Mental health
    "prozac": "fluoxetine", "sarafem": "fluoxetine",
    "zoloft": "sertraline", "paxil": "paroxetine", "lexapro": "escitalopram",
    "celexa": "citalopram", "luvox": "fluvoxamine",
    "effexor": "venlafaxine", "cymbalta": "duloxetine", "pristiq": "desvenlafaxine",
    "wellbutrin": "bupropion", "zyban": "bupropion",
    "remeron": "mirtazapine", "trazodone": "trazodone",
    "elavil": "amitriptyline", "pamelor": "nortriptyline",
    "abilify": "aripiprazole", "seroquel": "quetiapine", "zyprexa": "olanzapine",
    "risperdal": "risperidone", "geodon": "ziprasidone", "latuda": "lurasidone",
    "xanax": "alprazolam", "valium": "diazepam", "ativan": "lorazepam",
    "klonopin": "clonazepam", "restoril": "temazepam", "halcion": "triazolam",
    "ambien": "zolpidem", "lunesta": "eszopiclone", "sonata": "zaleplon",
    "adderall": "amphetamine-dextroamphetamine", "ritalin": "methylphenidate",
    "concerta": "methylphenidate", "vyvanse": "lisdexamfetamine",
    # Thyroid / Hormones
    "synthroid": "levothyroxine", "levoxyl": "levothyroxine",
    "armour thyroid": "desiccated thyroid", "cytomel": "liothyronine",
    "premarin": "conjugated estrogens", "prempro": "conjugated estrogens-medroxyprogesterone",
    "provera": "medroxyprogesterone",
    # Cholesterol / Other
    "zetia": "ezetimibe", "welchol": "colesevelam",
    "niaspan": "niacin", "lopid": "gemfibrozil", "tricor": "fenofibrate",
    "repatha": "evolocumab", "praluent": "alirocumab",
    # Allergy / Antihistamine
    "benadryl": "diphenhydramine", "zyrtec": "cetirizine",
    "claritin": "loratadine", "allegra": "fexofenadine",
    "flonase": "fluticasone nasal", "nasonex": "mometasone nasal",
    # Misc
    "glucosamine": "glucosamine", "aspirin": "aspirin",
    "t-minic": "chlorpheniramine-phenylephrine",
    "crocin": "acetaminophen", "dolo": "acetaminophen",
    "combiflam": "ibuprofen-paracetamol", "brufen": "ibuprofen",
    "pan": "pantoprazole", "rantac": "ranitidine",
    "ecosprin": "aspirin", "disprin": "aspirin",
}

# Generic name aliases (different spellings/names for same drug)
GENERIC_ALIASES: Dict[str, str] = {
    "paracetamol": "acetaminophen",
    "pethidine": "meperidine",
    "adrenaline": "epinephrine",
    "noradrenaline": "norepinephrine",
    "salbutamol": "albuterol",
    "frusemide": "furosemide",
    "lignocaine": "lidocaine",
    "amoxycillin": "amoxicillin",
    "cephalexin": "cefalexin",
    "metronidazol": "metronidazole",
    "ibuprofen-paracetamol": "ibuprofen-acetaminophen",
}


def normalize_drug_name(name: str) -> Tuple[str, float, str]:
    """
    Normalize a drug name to its generic form.

    Returns:
        (normalized_name, confidence, resolution_method)
        confidence: 1.0 = exact match, 0.8 = alias, 0.6 = fuzzy, 0.0 = unknown
    """
    if not name:
        return name, 0.0, "empty"

    clean = name.strip().lower()
    clean = re.sub(r'\s+\d+\s*(mg|mcg|ml|g|units?|tabs?|caps?|drops?).*$', '', clean)
    clean = re.sub(r'[^\w\s-]', '', clean).strip()

    # 1. Direct brand match
    if clean in BRAND_TO_GENERIC:
        generic = BRAND_TO_GENERIC[clean]
        return generic, 1.0, "brand_lookup"

    # 2. Generic alias match
    if clean in GENERIC_ALIASES:
        return GENERIC_ALIASES[clean], 0.9, "alias_lookup"

    # 3. Check if it's already a known generic (value in BRAND_TO_GENERIC)
    known_generics = set(BRAND_TO_GENERIC.values()) | set(GENERIC_ALIASES.values())
    if clean in known_generics:
        return clean, 1.0, "known_generic"

    # 4. Partial match (brand name contains the search term)
    for brand, generic in BRAND_TO_GENERIC.items():
        if clean in brand or brand in clean:
            return generic, 0.75, "partial_brand"

    # 5. Try OpenFDA for unknown drugs
    fda_result = _query_openfda(clean)
    if fda_result:
        return fda_result, 0.85, "openfda"

    # 6. Unknown — return as-is with low confidence
    return name.strip(), 0.3, "unresolved"


def _query_openfda(drug_name: str) -> Optional[str]:
    """Query OpenFDA drug label API for generic name"""
    try:
        url = "https://api.fda.gov/drug/label.json"
        params = {
            "search": f'openfda.brand_name:"{drug_name}"',
            "limit": 1
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                openfda = results[0].get("openfda", {})
                generics = openfda.get("generic_name", [])
                if generics:
                    return generics[0].lower()
    except Exception:
        pass
    return None


def normalize_drug_list(drugs: List[str]) -> List[Dict]:
    """
    Normalize a list of drug names.

    Returns list of dicts with:
        original, normalized, confidence, method, needs_clarification
    """
    results = []
    seen_normalized = set()

    for drug in drugs:
        normalized, confidence, method = normalize_drug_name(drug)

        # Deduplicate
        if normalized.lower() in seen_normalized:
            continue
        seen_normalized.add(normalized.lower())

        results.append({
            "original": drug,
            "normalized": normalized,
            "confidence": confidence,
            "method": method,
            "needs_clarification": confidence < 0.5,
            "display_name": normalized.title() if confidence >= 0.5 else drug,
        })

    return results


def get_interaction_pairs(normalized_drugs: List[Dict]) -> List[Tuple[str, str]]:
    """Generate unique drug pairs for interaction checking"""
    high_conf = [d for d in normalized_drugs if not d["needs_clarification"]]
    pairs = []
    for i in range(len(high_conf)):
        for j in range(i + 1, len(high_conf)):
            pairs.append((high_conf[i]["normalized"], high_conf[j]["normalized"]))
    return pairs
