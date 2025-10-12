"""
Comprehensive Medical Dictionary for DiagnoAI
Contains detailed definitions for medical terms
"""

MEDICAL_TERMS_DICTIONARY = {
    "hypertension": {
        "definition": "Hypertension, commonly known as high blood pressure, is a chronic medical condition where the force of blood against artery walls is consistently too high. This condition forces the heart to work harder to pump blood throughout the body, which can lead to serious health complications over time including heart disease, stroke, kidney damage, and vision problems.",
        "category": "cardiovascular",
        "aliases": ["high blood pressure", "htn"],
        "severity": "serious"
    },
    
    "tachycardia": {
        "definition": "Tachycardia refers to a heart rate that exceeds the normal resting rate, generally defined as over 100 beats per minute in adults. This condition can occur in either the heart's upper chambers (atria) or lower chambers (ventricles). Tachycardia may be caused by various factors including stress, exercise, fever, anemia, or underlying heart conditions.",
        "category": "cardiovascular",
        "aliases": ["fast heart rate", "rapid heartbeat"],
        "severity": "moderate"
    },
    
    "bradycardia": {
        "definition": "Bradycardia is a slower than normal heart rate, typically defined as fewer than 60 beats per minute in adults. While well-trained athletes often have resting heart rates in this range, bradycardia in others may indicate problems with the heart's electrical conduction system.",
        "category": "cardiovascular",
        "aliases": ["slow heart rate"],
        "severity": "moderate"
    },
    
    "arrhythmia": {
        "definition": "Arrhythmia describes any disorder of the heart's rhythm where the heart beats too fast, too slow, or with an irregular pattern. This occurs when the electrical impulses that coordinate heartbeats don't work properly, causing the heart to beat inefficiently.",
        "category": "cardiovascular",
        "aliases": ["irregular heartbeat", "cardiac dysrhythmia"],
        "severity": "moderate"
    },
    
    "myocardial infarction": {
        "definition": "Myocardial infarction, commonly known as a heart attack, occurs when blood flow to a part of the heart muscle is blocked, usually by a blood clot. This causes damage or death to the heart tissue due to lack of oxygen.",
        "category": "cardiovascular",
        "aliases": ["heart attack", "mi", "cardiac infarction"],
        "severity": "emergency"
    },

    "diabetes": {
        "definition": "Diabetes mellitus is a chronic metabolic disorder characterized by high blood sugar levels over a prolonged period. This occurs either because the pancreas doesn't produce enough insulin (Type 1) or because the body's cells don't respond properly to insulin (Type 2).",
        "category": "endocrine",
        "aliases": ["diabetes mellitus", "high blood sugar"],
        "severity": "serious"
    },
    
    "hyperglycemia": {
        "definition": "Hyperglycemia refers to abnormally high levels of glucose (sugar) in the blood, typically above 125 mg/dL when fasting or above 180 mg/dL after meals. This condition is the hallmark of diabetes and can cause symptoms like increased thirst, frequent urination, fatigue, and blurred vision.",
        "category": "endocrine",
        "aliases": ["high blood sugar"],
        "severity": "moderate"
    },
    
    "hypoglycemia": {
        "definition": "Hypoglycemia, or low blood sugar, occurs when blood glucose levels drop below normal (typically below 70 mg/dL). This condition is common in people with diabetes who use insulin or certain medications.",
        "category": "endocrine",
        "aliases": ["low blood sugar"],
        "severity": "moderate"
    },

    "asthma": {
        "definition": "Asthma is a chronic inflammatory disease of the airways characterized by variable and recurring symptoms, reversible airflow obstruction, and bronchospasm. Common symptoms include wheezing, coughing, chest tightness, and shortness of breath.",
        "category": "respiratory",
        "aliases": ["bronchial asthma", "reactive airway disease"],
        "severity": "moderate"
    },
    
    "pneumonia": {
        "definition": "Pneumonia is an inflammatory condition of the lung primarily affecting the microscopic air sacs (alveoli). It's usually caused by infection with viruses or bacteria and less commonly by other microorganisms.",
        "category": "respiratory",
        "aliases": ["lung infection", "pulmonary infection"],
        "severity": "serious"
    },
    
    "bronchitis": {
        "definition": "Bronchitis is inflammation of the bronchial tubes, the airways that carry air to your lungs. There are two main types: acute bronchitis (usually caused by viruses) and chronic bronchitis (a serious long-term condition often part of COPD).",
        "category": "respiratory",
        "aliases": ["bronchial inflammation"],
        "severity": "moderate"
    },

    "migraine": {
        "definition": "A migraine is not just a bad headache but a complex neurological disorder characterized by recurrent, often debilitating headaches typically accompanied by other symptoms like sensitivity to light and sound, nausea, and visual disturbances.",
        "category": "neurological",
        "aliases": ["migraine headache", "vascular headache"],
        "severity": "moderate"
    },
    
    "epilepsy": {
        "definition": "Epilepsy is a chronic neurological disorder characterized by recurrent, unprovoked seizures. These seizures result from sudden, excessive electrical discharges in brain cells (neurons).",
        "category": "neurological",
        "aliases": ["seizure disorder"],
        "severity": "serious"
    },
    
    "stroke": {
        "definition": "A stroke, or cerebrovascular accident (CVA), occurs when blood supply to part of the brain is interrupted or reduced, preventing brain tissue from getting oxygen and nutrients.",
        "category": "neurological",
        "aliases": ["cerebrovascular accident", "brain attack"],
        "severity": "emergency"
    },

    "arthritis": {
        "definition": "Arthritis is not a single disease but rather a term covering over 100 conditions that affect joints and surrounding tissues. The most common forms are osteoarthritis (degenerative joint disease) and rheumatoid arthritis (autoimmune inflammatory disease).",
        "category": "musculoskeletal",
        "aliases": ["joint inflammation"],
        "severity": "moderate"
    },
    
    "osteoporosis": {
        "definition": "Osteoporosis is a progressive bone disease characterized by decreased bone density and quality, leading to weakened bones that are more susceptible to fractures.",
        "category": "musculoskeletal",
        "aliases": ["brittle bone disease"],
        "severity": "moderate"
    },
    
    "fibromyalgia": {
        "definition": "Fibromyalgia is a chronic disorder characterized by widespread musculoskeletal pain accompanied by fatigue, sleep, memory, and mood issues.",
        "category": "musculoskeletal",
        "aliases": ["fibromyalgia syndrome"],
        "severity": "moderate"
    },

    "gastroenteritis": {
        "definition": "Gastroenteritis is inflammation of the stomach and intestines, typically resulting from bacterial toxins or viral infection and causing vomiting and diarrhea.",
        "category": "gastrointestinal",
        "aliases": ["stomach flu", "gastric flu"],
        "severity": "moderate"
    },
    
    "hepatitis": {
        "definition": "Hepatitis refers to inflammation of the liver, commonly caused by viral infections (hepatitis A, B, C) but also by alcohol, medications, or autoimmune diseases.",
        "category": "gastrointestinal",
        "aliases": ["liver inflammation"],
        "severity": "serious"
    },

    "fever": {
        "definition": "Fever is a temporary increase in body temperature, often due to an illness. It's a common sign that your body is fighting an infection or other diseases.",
        "category": "symptom",
        "aliases": ["pyrexia", "elevated temperature"],
        "severity": "mild"
    },
    
    "fatigue": {
        "definition": "Fatigue is a subjective feeling of tiredness, exhaustion, or lack of energy that isn't relieved by rest. Unlike normal tiredness, fatigue can be overwhelming and interfere with daily activities.",
        "category": "symptom",
        "aliases": ["tiredness", "exhaustion"],
        "severity": "mild"
    },
    
    "nausea": {
        "definition": "Nausea is an unpleasant sensation of unease and discomfort in the upper stomach with an involuntary urge to vomit. It often precedes vomiting but can occur alone.",
        "category": "symptom",
        "aliases": ["sick to stomach", "queasiness"],
        "severity": "mild"
    },
    
    "headache": {
        "definition": "A headache is pain in any region of the head. Headaches can occur on one or both sides of the head, be isolated to a certain location, radiate across the head, or have a vise-like quality.",
        "category": "symptom",
        "aliases": ["cephalgia"],
        "severity": "mild"
    },

    "paracetamol": {
        "definition": "Paracetamol, also known as acetaminophen, is a common over-the-counter medication used to treat pain and fever. It's generally considered safe when used as directed but can cause liver damage in high doses.",
        "category": "medication",
        "aliases": ["acetaminophen", "tylenol", "panadol"],
        "severity": "info"
    },
    
    "ibuprofen": {
        "definition": "Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID) used to treat pain, fever, and inflammation. Common brand names include Advil and Motrin.",
        "category": "medication",
        "aliases": ["advil", "motrin", "nurofen"],
        "severity": "info"
    },
    
    "antibiotic": {
        "definition": "Antibiotics are medications that destroy or slow down the growth of bacteria. They are used to treat bacterial infections and are not effective against viral infections like the common cold or flu.",
        "category": "medication",
        "aliases": ["antimicrobial", "antibacterial"],
        "severity": "info"
    }
}

CATEGORY_COLORS = {
    "cardiovascular": "#ff6b6b",
    "endocrine": "#4ecdc4",
    "respiratory": "#45b7d1",
    "neurological": "#96ceb4",
    "musculoskeletal": "#feca57",
    "gastrointestinal": "#ff9ff3",
    "symptom": "#54a0ff",
    "medication": "#5f27cd",
    "emergency": "#ff0000",
    "serious": "#ff6b6b",
    "moderate": "#feca57",
    "mild": "#54a0ff",
    "info": "#4ecdc4"
}

MEDICAL_TERM_PATTERNS = {
    "suffixes": [
        'itis', 'emia', 'osis', 'algia', 'dynia', 'ectomy', 'stomy', 'otomy',
        'plasty', 'scopy', 'pathy', 'megaly', 'malacia', 'plasia', 'trophy',
        'penia', 'rrhea', 'uria', 'lysis', 'ptosis', 'ptysis', 'rrhage'
    ],
    "prefixes": [
        'cardio', 'neuro', 'hepato', 'nephro', 'pulmo', 'pneumo', 'osteo',
        'arthro', 'dermato', 'gastro', 'entero', 'colo', 'procto', 'uro',
        'hemo', 'lympho', 'myo', 'osteo', 'psycho', 'thyro', 'adreno'
    ]
}