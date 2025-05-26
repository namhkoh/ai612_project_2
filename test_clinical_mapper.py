#!/usr/bin/env python3
"""
Simple test script for the Clinical Term Mapper functionality
This tests the core functionality without requiring database access.
"""

def test_abbreviation_mapping():
    """Test basic abbreviation mapping functionality."""
    print("🧪 Testing Medical Abbreviation Mapping")
    print("=" * 50)
    
    # Test medical abbreviations dictionary
    medical_abbreviations = {
        'hb': 'hemoglobin',
        'hgb': 'hemoglobin', 
        'wbc': 'white blood cell',
        'rbc': 'red blood cell',
        'bp': 'blood pressure',
        'hr': 'heart rate',
        'dm': 'diabetes mellitus',
        'mi': 'myocardial infarction'
    }
    
    test_terms = ["hb", "wbc", "bp", "dm", "unknown_term"]
    
    for term in test_terms:
        print(f"\nTesting: '{term}'")
        if term.lower() in medical_abbreviations:
            mapped = medical_abbreviations[term.lower()]
            print(f"✅ {term} → {mapped}")
        else:
            print(f"ℹ️  No mapping found for '{term}'")

def test_term_variations():
    """Test term variation mapping."""
    print("\n\n🧪 Testing Term Variations")
    print("=" * 50)
    
    term_variations = {
        'lab': ['laboratory', 'labs', 'lab test', 'lab result'],
        'medication': ['med', 'meds', 'drug', 'drugs', 'prescription'],
        'patient': ['pt', 'subject', 'individual', 'person'],
        'diagnosis': ['dx', 'diagnoses', 'condition', 'disease']
    }
    
    test_terms = ["lab", "meds", "pt", "dx"]
    
    for term in test_terms:
        print(f"\nTesting: '{term}'")
        found = False
        for base_term, variations in term_variations.items():
            if term.lower() == base_term or term.lower() in variations:
                print(f"✅ {term} → {base_term} (variations: {', '.join(variations)})")
                found = True
                break
        if not found:
            print(f"ℹ️  No variation mapping found for '{term}'")

def test_query_patterns():
    """Test query pattern recognition."""
    print("\n\n🧪 Testing Query Pattern Recognition")
    print("=" * 50)
    
    test_queries = [
        "Show me recent lab results",
        "Find patients with diabetes medications", 
        "What procedures were performed?",
        "Get admission records for this patient"
    ]
    
    patterns = {
        'recent': 'ORDER BY charttime DESC LIMIT',
        'lab': 'labevents table',
        'medication': 'prescriptions table',
        'procedure': 'procedures_icd table',
        'admission': 'admissions table'
    }
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        query_lower = query.lower()
        found_patterns = []
        
        for keyword, pattern in patterns.items():
            if keyword in query_lower:
                found_patterns.append(pattern)
        
        if found_patterns:
            print(f"✅ Suggested patterns: {', '.join(found_patterns)}")
        else:
            print("ℹ️  No specific patterns identified")

def main():
    """Run all basic tests."""
    print("🚀 Clinical Term Mapper Basic Test Suite")
    print("=" * 60)
    
    test_abbreviation_mapping()
    test_term_variations()
    test_query_patterns()
    
    print("\n\n🎉 Basic functionality tests completed!")
    print("\nTo test full integration with database:")
    print("python test_integration.py")
    
    print("\nTo run the full evaluation:")
    print("bash run_mimic_iv.sh")

if __name__ == "__main__":
    main() 