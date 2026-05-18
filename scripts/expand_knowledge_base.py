"""
Expand the medical knowledge base with comprehensive drug data.
Run this once to populate ChromaDB with 30+ drugs, interactions, and conditions.
"""
import sys, json
sys.path.insert(0, '.')

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Comprehensive drug database ──────────────────────────────────────────────
DRUGS = [
    {
        "name": "Lisinopril", "generic_name": "Lisinopril", "class": "ACE Inhibitor",
        "uses": "Hypertension, heart failure, post-MI, diabetic nephropathy",
        "dosage": "5-40mg once daily",
        "side_effects": "Dry cough (10-15%), dizziness, headache, fatigue, hyperkalemia",
        "serious_effects": "Angioedema (rare but life-threatening), severe hypotension, acute kidney injury",
        "precautions": "Avoid in pregnancy (teratogenic). Monitor kidney function and potassium. Avoid NSAIDs.",
        "interactions": "NSAIDs reduce effect; potassium supplements cause hyperkalemia; lithium toxicity risk",
        "management": "Take at same time daily. Rise slowly to avoid dizziness. Report swelling of face/lips immediately."
    },
    {
        "name": "Metformin", "generic_name": "Metformin HCl", "class": "Biguanide",
        "uses": "Type 2 diabetes mellitus, insulin resistance, PCOS",
        "dosage": "500-2000mg daily in divided doses with meals",
        "side_effects": "Nausea, diarrhea, stomach upset, metallic taste (usually improves over time)",
        "serious_effects": "Lactic acidosis (rare, risk with kidney disease), Vitamin B12 deficiency",
        "precautions": "Hold 48h before contrast dye procedures. Avoid with severe kidney disease (eGFR<30). Avoid alcohol.",
        "interactions": "Alcohol increases lactic acidosis risk; contrast dye; cimetidine increases metformin levels",
        "management": "Take with meals to reduce GI side effects. Extended-release form better tolerated."
    },
    {
        "name": "Atorvastatin", "generic_name": "Atorvastatin", "class": "Statin (HMG-CoA reductase inhibitor)",
        "uses": "High cholesterol, cardiovascular disease prevention, familial hypercholesterolemia",
        "dosage": "10-80mg once daily, preferably in the evening",
        "side_effects": "Muscle aches (myalgia), headache, nausea, elevated liver enzymes",
        "serious_effects": "Rhabdomyolysis (rare), severe liver damage, new-onset diabetes",
        "precautions": "Avoid grapefruit juice. Monitor liver function. Report unexplained muscle pain immediately.",
        "interactions": "Grapefruit juice increases levels; clarithromycin, erythromycin, antifungals increase toxicity risk",
        "management": "Take at bedtime for best effect. Avoid grapefruit. Report muscle pain or weakness."
    },
    {
        "name": "Amlodipine", "generic_name": "Amlodipine besylate", "class": "Calcium Channel Blocker",
        "uses": "Hypertension, angina, coronary artery disease",
        "dosage": "2.5-10mg once daily",
        "side_effects": "Peripheral edema (ankle swelling), flushing, headache, dizziness, palpitations",
        "serious_effects": "Severe hypotension, worsening heart failure in some patients",
        "precautions": "Use caution in liver disease. May worsen heart failure. Monitor blood pressure.",
        "interactions": "Simvastatin levels increased (limit simvastatin to 20mg); cyclosporine; CYP3A4 inhibitors",
        "management": "Ankle swelling is common and usually harmless. Take at same time daily."
    },
    {
        "name": "Metoprolol", "generic_name": "Metoprolol succinate/tartrate", "class": "Beta-1 Selective Blocker",
        "uses": "Hypertension, heart failure, angina, post-MI, atrial fibrillation",
        "dosage": "25-200mg daily (succinate once daily; tartrate twice daily)",
        "side_effects": "Fatigue, bradycardia, dizziness, cold extremities, depression",
        "serious_effects": "Severe bradycardia, heart block, bronchospasm in asthmatics",
        "precautions": "Never stop abruptly — taper over 1-2 weeks. Avoid in asthma/COPD. Monitor heart rate.",
        "interactions": "Verapamil/diltiazem cause severe bradycardia; clonidine rebound hypertension on withdrawal",
        "management": "Do not stop suddenly. Take with food. Monitor pulse — contact doctor if below 60 bpm."
    },
    {
        "name": "Omeprazole", "generic_name": "Omeprazole", "class": "Proton Pump Inhibitor (PPI)",
        "uses": "GERD, peptic ulcer disease, H. pylori eradication, Zollinger-Ellison syndrome",
        "dosage": "20-40mg once daily before breakfast",
        "side_effects": "Headache, nausea, diarrhea, abdominal pain",
        "serious_effects": "C. difficile infection, hypomagnesemia with long-term use, bone fractures, B12 deficiency",
        "precautions": "Long-term use (>1 year) increases fracture risk. Monitor magnesium. Reassess need periodically.",
        "interactions": "Reduces clopidogrel effectiveness; increases methotrexate levels; reduces absorption of some drugs",
        "management": "Take 30-60 minutes before first meal. Do not crush delayed-release capsules."
    },
    {
        "name": "Losartan", "generic_name": "Losartan potassium", "class": "ARB (Angiotensin Receptor Blocker)",
        "uses": "Hypertension, diabetic nephropathy, heart failure, stroke prevention",
        "dosage": "25-100mg once or twice daily",
        "side_effects": "Dizziness, hyperkalemia, elevated creatinine, back pain",
        "serious_effects": "Angioedema (less common than ACE inhibitors), acute kidney injury, fetal toxicity",
        "precautions": "Avoid in pregnancy. Monitor kidney function and potassium. Do not combine with ACE inhibitors.",
        "interactions": "NSAIDs reduce effect; potassium supplements; lithium; fluconazole increases levels",
        "management": "Good alternative to ACE inhibitors for patients with cough. Monitor blood pressure regularly."
    },
    {
        "name": "Levothyroxine", "generic_name": "Levothyroxine sodium", "class": "Thyroid Hormone",
        "uses": "Hypothyroidism, thyroid cancer suppression, myxedema coma",
        "dosage": "25-200mcg once daily on empty stomach",
        "side_effects": "At correct dose: none. Overdose: palpitations, weight loss, anxiety, insomnia, sweating",
        "serious_effects": "Cardiac arrhythmias, angina, osteoporosis with long-term overtreatment",
        "precautions": "Take on empty stomach 30-60 min before breakfast. Many drug and food interactions.",
        "interactions": "Calcium, iron, antacids reduce absorption (take 4h apart); warfarin effect increased",
        "management": "Take same time every morning on empty stomach. Do not skip doses. Regular TSH monitoring."
    },
    {
        "name": "Sertraline", "generic_name": "Sertraline HCl", "class": "SSRI Antidepressant",
        "uses": "Depression, anxiety, OCD, PTSD, panic disorder, social anxiety",
        "dosage": "25-200mg once daily",
        "side_effects": "Nausea, insomnia, diarrhea, dry mouth, sexual dysfunction, sweating",
        "serious_effects": "Serotonin syndrome, suicidal ideation (especially in young adults), bleeding risk",
        "precautions": "Do not stop abruptly — taper. Monitor for suicidal thoughts in first weeks. Avoid MAOIs.",
        "interactions": "MAOIs (fatal interaction); NSAIDs/aspirin increase bleeding; tramadol causes serotonin syndrome",
        "management": "Takes 2-4 weeks for full effect. Take with food if nausea occurs. Do not stop suddenly."
    },
    {
        "name": "Albuterol", "generic_name": "Albuterol sulfate", "class": "Short-Acting Beta-2 Agonist (SABA)",
        "uses": "Acute bronchospasm, asthma attacks, COPD exacerbations, exercise-induced bronchospasm",
        "dosage": "1-2 puffs (90mcg each) every 4-6 hours as needed",
        "side_effects": "Tremor, palpitations, tachycardia, headache, nervousness, hypokalemia",
        "serious_effects": "Paradoxical bronchospasm, severe tachycardia, hypokalemia",
        "precautions": "Rescue inhaler only — not for daily maintenance. Overuse indicates poor asthma control.",
        "interactions": "Beta-blockers reduce effect; MAOIs and TCAs increase cardiovascular effects",
        "management": "Shake well before use. Rinse mouth after use. If using >2 days/week, see doctor."
    },
    {
        "name": "Gabapentin", "generic_name": "Gabapentin", "class": "Anticonvulsant / Neuropathic Pain Agent",
        "uses": "Neuropathic pain, epilepsy (partial seizures), restless leg syndrome, fibromyalgia",
        "dosage": "300-3600mg daily in 3 divided doses",
        "side_effects": "Drowsiness, dizziness, ataxia, fatigue, peripheral edema, weight gain",
        "serious_effects": "Respiratory depression (especially with opioids/CNS depressants), suicidal ideation",
        "precautions": "Reduce dose in kidney disease. Do not stop abruptly. Avoid driving until effects known.",
        "interactions": "CNS depressants (alcohol, opioids, benzodiazepines) increase sedation and respiratory depression",
        "management": "Start low, go slow. Take with food. Avoid alcohol. Do not drive until you know how it affects you."
    },
    {
        "name": "Warfarin", "generic_name": "Warfarin sodium", "class": "Anticoagulant (Vitamin K Antagonist)",
        "uses": "Atrial fibrillation, DVT/PE treatment and prevention, mechanical heart valves",
        "dosage": "Individualized based on INR target (usually 2-3)",
        "side_effects": "Bleeding (bruising, nosebleeds, prolonged bleeding from cuts)",
        "serious_effects": "Major bleeding (intracranial, GI), skin necrosis, purple toe syndrome",
        "precautions": "Regular INR monitoring essential. Consistent vitamin K intake. Many drug and food interactions.",
        "interactions": "Hundreds of interactions — antibiotics, NSAIDs, aspirin, many foods with vitamin K",
        "management": "Keep vitamin K intake consistent. Report any unusual bleeding. Regular INR checks."
    },
    {
        "name": "Aspirin", "generic_name": "Acetylsalicylic acid", "class": "Antiplatelet / NSAID",
        "uses": "Cardiovascular event prevention, pain, fever, anti-inflammatory",
        "dosage": "81mg daily (cardioprotective); 325-650mg every 4-6h (pain/fever)",
        "side_effects": "GI upset, heartburn, nausea, increased bleeding time",
        "serious_effects": "GI bleeding, peptic ulcer, Reye syndrome in children, tinnitus at high doses",
        "precautions": "Avoid in children with viral illness. Take with food. Avoid if on anticoagulants without guidance.",
        "interactions": "Warfarin (bleeding risk); NSAIDs (GI bleeding); ACE inhibitors (reduced effect)",
        "management": "Take with food or milk. Use enteric-coated for GI protection. Do not crush enteric-coated."
    },
    {
        "name": "Lisinopril + Metformin combination", "generic_name": "Combination therapy",
        "class": "ACE Inhibitor + Biguanide",
        "uses": "Hypertension with Type 2 Diabetes — very common combination",
        "dosage": "As prescribed for each individual drug",
        "side_effects": "Combined: cough from lisinopril, GI upset from metformin",
        "serious_effects": "Kidney function must be monitored — both drugs affect kidneys",
        "precautions": "Monitor kidney function (eGFR) and potassium regularly. Both drugs are renally cleared.",
        "interactions": "NSAIDs should be avoided with this combination — triple whammy effect on kidneys",
        "management": "Excellent combination for diabetic patients with hypertension. Protects kidneys when used correctly."
    },
]

# ── Drug interactions database ───────────────────────────────────────────────
INTERACTIONS = [
    {
        "drug1": "Lisinopril", "drug2": "Ibuprofen", "severity": "Moderate",
        "description": "NSAIDs reduce the antihypertensive effect of ACE inhibitors and increase risk of acute kidney injury (triple whammy with diuretics).",
        "recommendation": "Use acetaminophen instead. If NSAID needed, monitor blood pressure and kidney function closely."
    },
    {
        "drug1": "Metformin", "drug2": "Alcohol", "severity": "Moderate",
        "description": "Alcohol increases the risk of lactic acidosis with metformin, especially with binge drinking.",
        "recommendation": "Limit alcohol to 1-2 drinks occasionally. Avoid heavy drinking entirely."
    },
    {
        "drug1": "Warfarin", "drug2": "Aspirin", "severity": "High",
        "description": "Combination significantly increases bleeding risk. Both inhibit clotting through different mechanisms.",
        "recommendation": "Only use together under close medical supervision with regular INR monitoring."
    },
    {
        "drug1": "Metoprolol", "drug2": "Verapamil", "severity": "High",
        "description": "Both slow heart rate and conduction. Combination can cause severe bradycardia, heart block, or cardiac arrest.",
        "recommendation": "Avoid combination. If necessary, use with extreme caution and cardiac monitoring."
    },
    {
        "drug1": "Sertraline", "drug2": "Tramadol", "severity": "High",
        "description": "Risk of serotonin syndrome — potentially life-threatening condition with agitation, fever, rapid heart rate.",
        "recommendation": "Avoid combination. Use alternative pain medication."
    },
    {
        "drug1": "Atorvastatin", "drug2": "Clarithromycin", "severity": "Moderate",
        "description": "Clarithromycin inhibits CYP3A4, increasing atorvastatin levels and risk of myopathy/rhabdomyolysis.",
        "recommendation": "Temporarily stop atorvastatin during short antibiotic course, or use azithromycin instead."
    },
    {
        "drug1": "Levothyroxine", "drug2": "Calcium supplements", "severity": "Moderate",
        "description": "Calcium binds levothyroxine in the gut, reducing absorption by up to 40%.",
        "recommendation": "Take levothyroxine at least 4 hours before or after calcium supplements."
    },
    {
        "drug1": "Gabapentin", "drug2": "Opioids", "severity": "High",
        "description": "Combination significantly increases risk of respiratory depression and death.",
        "recommendation": "Avoid combination if possible. If necessary, use lowest effective doses with close monitoring."
    },
    {
        "drug1": "Lisinopril", "drug2": "Potassium supplements", "severity": "Moderate",
        "description": "ACE inhibitors already raise potassium levels. Adding supplements can cause dangerous hyperkalemia.",
        "recommendation": "Monitor potassium levels closely. Avoid potassium supplements unless specifically prescribed."
    },
    {
        "drug1": "Metformin", "drug2": "Contrast dye", "severity": "Moderate",
        "description": "Contrast dye can cause acute kidney injury, which impairs metformin clearance and increases lactic acidosis risk.",
        "recommendation": "Hold metformin 48 hours before and after contrast procedures. Restart only after kidney function confirmed normal."
    },
    {
        "drug1": "Amlodipine", "drug2": "Simvastatin", "severity": "Moderate",
        "description": "Amlodipine inhibits CYP3A4, increasing simvastatin levels and risk of myopathy.",
        "recommendation": "Limit simvastatin dose to 20mg/day when combined with amlodipine. Consider switching to atorvastatin."
    },
    {
        "drug1": "Aspirin", "drug2": "Ibuprofen", "severity": "Moderate",
        "description": "Ibuprofen can block aspirin's antiplatelet effect when taken together, reducing cardiovascular protection.",
        "recommendation": "Take aspirin at least 30 minutes before ibuprofen, or use acetaminophen for pain instead."
    },
]

# ── Side effects database ────────────────────────────────────────────────────
SIDE_EFFECTS = {
    "Lisinopril": {
        "common": ["Dry cough (10-15% of patients)", "Dizziness", "Headache", "Fatigue", "Nausea"],
        "serious": ["Angioedema (face/throat swelling — EMERGENCY)", "Severe hypotension", "Acute kidney injury", "Hyperkalemia"],
        "management": "The dry cough is the most common reason to switch to an ARB (like losartan). Rise slowly from sitting/lying. Report any facial swelling immediately — it is a medical emergency."
    },
    "Metformin": {
        "common": ["Nausea", "Diarrhea", "Stomach upset", "Metallic taste", "Loss of appetite"],
        "serious": ["Lactic acidosis (rare but serious)", "Vitamin B12 deficiency with long-term use"],
        "management": "GI side effects usually improve after 2-4 weeks. Take with food. Extended-release formulation causes fewer GI side effects. Get B12 levels checked annually."
    },
    "Atorvastatin": {
        "common": ["Muscle aches (myalgia)", "Headache", "Nausea", "Joint pain", "Diarrhea"],
        "serious": ["Rhabdomyolysis (severe muscle breakdown — rare)", "Liver damage", "New-onset diabetes"],
        "management": "Report any unexplained muscle pain, weakness, or dark urine immediately. Avoid grapefruit juice. Liver function tests recommended before starting."
    },
    "Amlodipine": {
        "common": ["Ankle/foot swelling (peripheral edema)", "Flushing", "Headache", "Dizziness", "Palpitations"],
        "serious": ["Severe hypotension", "Worsening angina when starting treatment"],
        "management": "Ankle swelling is common and usually harmless — elevating legs helps. Flushing and headache usually improve after a few weeks."
    },
    "Metoprolol": {
        "common": ["Fatigue", "Slow heart rate", "Dizziness", "Cold hands/feet", "Depression"],
        "serious": ["Severe bradycardia", "Heart block", "Bronchospasm in asthmatics", "Masking hypoglycemia symptoms"],
        "management": "Never stop abruptly — can cause rebound hypertension or angina. Monitor pulse. Avoid in asthma."
    },
    "Sertraline": {
        "common": ["Nausea (usually improves)", "Insomnia or drowsiness", "Diarrhea", "Dry mouth", "Sexual dysfunction", "Sweating"],
        "serious": ["Serotonin syndrome", "Increased suicidal thoughts (especially in young adults, first weeks)", "Bleeding risk"],
        "management": "Takes 2-4 weeks for full antidepressant effect. Take with food for nausea. Do not stop abruptly — taper over weeks."
    },
    "Omeprazole": {
        "common": ["Headache", "Nausea", "Diarrhea", "Abdominal pain", "Flatulence"],
        "serious": ["C. difficile infection", "Hypomagnesemia", "Bone fractures (long-term use)", "B12 deficiency"],
        "management": "Take 30-60 minutes before first meal. Reassess need every 3-6 months. Long-term use should be medically justified."
    },
    "Gabapentin": {
        "common": ["Drowsiness", "Dizziness", "Ataxia (unsteady gait)", "Fatigue", "Weight gain", "Peripheral edema"],
        "serious": ["Respiratory depression (with CNS depressants)", "Suicidal ideation", "Withdrawal seizures if stopped abruptly"],
        "management": "Start low and increase slowly. Avoid alcohol and other CNS depressants. Do not drive until you know how it affects you."
    },
    "Albuterol": {
        "common": ["Tremor", "Palpitations", "Tachycardia", "Headache", "Nervousness", "Throat irritation"],
        "serious": ["Paradoxical bronchospasm", "Severe hypokalemia", "Cardiac arrhythmias"],
        "management": "Shake inhaler before use. Rinse mouth after use. If needed more than 2 days/week, asthma is not well-controlled — see doctor."
    },
}

# ── Disease/condition information ────────────────────────────────────────────
CONDITIONS = [
    {
        "name": "Hypertension (High Blood Pressure)",
        "description": "Blood pressure consistently above 130/80 mmHg. Often called the 'silent killer' because it has no symptoms.",
        "lifestyle": "Reduce sodium (<2300mg/day), DASH diet, regular exercise (150 min/week), limit alcohol, quit smoking, manage stress, maintain healthy weight.",
        "monitoring": "Check blood pressure daily at home, same time each day. Keep a log. Target: below 130/80 mmHg.",
        "warning_signs": "Severe headache, vision changes, chest pain, shortness of breath — seek emergency care immediately.",
        "medications": "ACE inhibitors, ARBs, calcium channel blockers, diuretics, beta-blockers"
    },
    {
        "name": "Type 2 Diabetes",
        "description": "Chronic condition where the body doesn't use insulin properly, causing high blood sugar levels.",
        "lifestyle": "Low-carb or Mediterranean diet, regular exercise, weight loss (even 5-10% helps significantly), quit smoking.",
        "monitoring": "Check blood sugar as directed. HbA1c every 3 months. Target HbA1c: below 7% for most patients.",
        "warning_signs": "Very high blood sugar: extreme thirst, frequent urination, blurred vision. Low blood sugar: shakiness, sweating, confusion.",
        "medications": "Metformin (first-line), GLP-1 agonists, SGLT2 inhibitors, sulfonylureas, insulin"
    },
    {
        "name": "High Cholesterol (Hyperlipidemia)",
        "description": "Elevated LDL cholesterol increases risk of heart attack and stroke.",
        "lifestyle": "Heart-healthy diet (reduce saturated fat, trans fat), increase fiber, regular exercise, quit smoking.",
        "monitoring": "Lipid panel every 3-12 months depending on treatment. Target LDL depends on cardiovascular risk.",
        "warning_signs": "High cholesterol itself has no symptoms — regular testing is essential.",
        "medications": "Statins (first-line), ezetimibe, PCSK9 inhibitors, fibrates, niacin"
    },
    {
        "name": "Hypothyroidism",
        "description": "Underactive thyroid gland producing insufficient thyroid hormone, slowing metabolism.",
        "lifestyle": "Consistent medication timing is crucial. Avoid excessive iodine. Regular monitoring.",
        "monitoring": "TSH levels every 6-12 months once stable. Symptoms: fatigue, weight gain, cold intolerance, constipation.",
        "warning_signs": "Myxedema coma (rare): extreme fatigue, low body temperature, confusion — medical emergency.",
        "medications": "Levothyroxine (T4 replacement) — take on empty stomach, same time daily"
    },
    {
        "name": "Asthma",
        "description": "Chronic inflammatory airway disease causing episodes of wheezing, breathlessness, chest tightness, and coughing.",
        "lifestyle": "Identify and avoid triggers (allergens, smoke, exercise, cold air). Use peak flow meter. Have action plan.",
        "monitoring": "Peak flow monitoring. Spirometry annually. Count rescue inhaler use — more than 2x/week = poor control.",
        "warning_signs": "Severe breathlessness, unable to speak in full sentences, blue lips/fingertips — call 911.",
        "medications": "Rescue: albuterol (SABA). Controller: inhaled corticosteroids, LABAs, montelukast, biologics"
    },
]


def expand_knowledge_base():
    """Add all new documents to ChromaDB"""
    from src.rag.vector_store import VectorStore

    vs = VectorStore(collection_name="medical_knowledge")

    # Check existing count
    existing = vs.get_collection_stats()["document_count"]
    print(f"Current documents: {existing}")

    # Reset and rebuild for clean state
    try:
        vs.delete_collection()
        print("Cleared old collection")
    except Exception:
        pass

    # Recreate
    vs = VectorStore(collection_name="medical_knowledge")

    documents, metadatas, ids = [], [], []

    # Add drugs
    for drug in DRUGS:
        doc = f"""Drug Name: {drug['name']}
Generic Name: {drug.get('generic_name', drug['name'])}
Drug Class: {drug['class']}
Uses / Indications: {drug['uses']}
Typical Dosage: {drug['dosage']}
Common Side Effects: {drug['side_effects']}
Serious Side Effects: {drug['serious_effects']}
Precautions & Warnings: {drug['precautions']}
Drug Interactions: {drug['interactions']}
Patient Guidance: {drug['management']}"""

        documents.append(doc)
        metadatas.append({"source": "drug_info", "drug_name": drug['name'], "type": "drug_information"})
        ids.append(f"drug_{drug['name'].lower().replace(' ', '_').replace('+', 'plus')[:50]}")

    # Add interactions
    for i, interaction in enumerate(INTERACTIONS):
        doc = f"""Drug Interaction: {interaction['drug1']} and {interaction['drug2']}
Severity: {interaction['severity']}
Description: {interaction['description']}
Clinical Recommendation: {interaction['recommendation']}"""

        documents.append(doc)
        metadatas.append({
            "source": "interactions", "type": "drug_interaction",
            "severity": interaction['severity'].lower(),
            "drug1": interaction['drug1'], "drug2": interaction['drug2']
        })
        ids.append(f"interaction_{i}_{interaction['drug1'][:10]}_{interaction['drug2'][:10]}".lower().replace(' ', '_'))

    # Add side effects
    for drug_name, effects in SIDE_EFFECTS.items():
        doc = f"""Drug: {drug_name}
Common Side Effects: {', '.join(effects['common'])}
Serious Side Effects: {', '.join(effects['serious'])}
Management & Patient Guidance: {effects['management']}"""

        documents.append(doc)
        metadatas.append({"source": "side_effects", "drug_name": drug_name, "type": "side_effects"})
        ids.append(f"se_{drug_name.lower().replace(' ', '_')}")

    # Add conditions
    for condition in CONDITIONS:
        doc = f"""Medical Condition: {condition['name']}
Description: {condition['description']}
Lifestyle Recommendations: {condition['lifestyle']}
Monitoring: {condition['monitoring']}
Warning Signs: {condition['warning_signs']}
Common Medications: {condition['medications']}"""

        documents.append(doc)
        metadatas.append({"source": "conditions", "condition": condition['name'], "type": "condition_info"})
        ids.append(f"condition_{condition['name'][:30].lower().replace(' ', '_').replace('(', '').replace(')', '')}")

    # Save to JSON files too
    kb_dir = settings.knowledge_base_dir
    with open(kb_dir / "drug_info.json", 'w') as f:
        json.dump(DRUGS, f, indent=2)
    with open(kb_dir / "interactions.json", 'w') as f:
        json.dump(INTERACTIONS, f, indent=2)
    with open(kb_dir / "side_effects.json", 'w') as f:
        json.dump(SIDE_EFFECTS, f, indent=2)
    with open(kb_dir / "conditions.json", 'w') as f:
        json.dump(CONDITIONS, f, indent=2)

    # Add to vector store
    vs.add_documents(documents, metadatas, ids)

    final_count = vs.get_collection_stats()["document_count"]
    print(f"\n✅ Knowledge base expanded: {existing} → {final_count} documents")
    print(f"   Drugs: {len(DRUGS)}")
    print(f"   Interactions: {len(INTERACTIONS)}")
    print(f"   Side effects: {len(SIDE_EFFECTS)}")
    print(f"   Conditions: {len(CONDITIONS)}")

    # Test a retrieval
    print("\n🔍 Test retrieval: 'side effects of metformin'")
    results = vs.query("side effects of metformin", n_results=2)
    for doc, meta in zip(results['documents'], results['metadatas']):
        print(f"  [{meta['type']}] {doc[:120]}...")


if __name__ == "__main__":
    expand_knowledge_base()
