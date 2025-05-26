#!/usr/bin/env python3
"""
Test script to verify the Clinical Term Mapper integration works correctly.
Run this to test the tools before running the full evaluation.
"""

import os
import sys
from sqlalchemy import create_engine

# Add the src directory to the path so we can import modules
sys.path.append('src')

def test_clinical_term_mapper():
    """Test the clinical term mapper tool integration."""
    print("🧪 Testing Clinical Term Mapper Integration")
    print("=" * 50)
    
    # Check if database exists
    db_path = "src/envs/mimic_iv/mimic_iv.sqlite"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Please ensure the MIMIC-IV database is available.")
        return False
    
    try:
        # Import the tools
        from src.envs.mimic_iv.tools.clinical_term_mapper import ClinicalTermMapper, QueryAnalyzer
        
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")
        
        # Test ClinicalTermMapper
        print("\n1. Testing ClinicalTermMapper:")
        print("-" * 30)
        
        mapper = ClinicalTermMapper(engine=engine)
        
        # Test cases
        test_terms = ["hb", "lab", "patient", "medication"]
        
        for term in test_terms:
            print(f"\nTesting term: '{term}'")
            try:
                result = mapper.invoke(term)
                print(f"✅ Successfully mapped '{term}'")
                # Parse the JSON to verify it's valid
                import json
                parsed = json.loads(result)
                print(f"   Found {len(parsed['mappings'])} mappings")
                if parsed['mappings']:
                    best = parsed['mappings'][0]
                    print(f"   Best: '{best['mapped_term']}' (confidence: {best['confidence']:.2f})")
            except Exception as e:
                print(f"❌ Error mapping '{term}': {e}")
                return False
        
        # Test QueryAnalyzer
        print("\n\n2. Testing QueryAnalyzer:")
        print("-" * 30)
        
        analyzer = QueryAnalyzer(engine=engine)
        
        test_queries = [
            "Show me recent Hb levels for patients",
            "Find patients with diabetes medications"
        ]
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            try:
                result = analyzer.invoke(query)
                print(f"✅ Successfully analyzed query")
                # Parse the JSON to verify it's valid
                parsed = json.loads(result)
                print(f"   Mapped terms: {len(parsed['mapped_terms'])}")
                print(f"   Search patterns: {len(parsed['search_patterns'])}")
            except Exception as e:
                print(f"❌ Error analyzing query: {e}")
                return False
        
        # Test tool info
        print("\n\n3. Testing tool info:")
        print("-" * 30)
        
        mapper_info = ClinicalTermMapper.get_info()
        analyzer_info = QueryAnalyzer.get_info()
        
        print(f"✅ ClinicalTermMapper tool name: {mapper_info['function']['name']}")
        print(f"✅ QueryAnalyzer tool name: {analyzer_info['function']['name']}")
        
        print("\n🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_loading():
    """Test that the environment loads correctly with the new tools."""
    print("\n\n🧪 Testing Environment Loading")
    print("=" * 50)
    
    try:
        from src.envs import get_env
        
        # Try to create the environment
        env = get_env(
            env_name="mimic_iv",
            eval_mode="valid",
            user_strategy="llm",
            user_model="gemini/gemini-2.0-flash",
            task_index=0
        )
        
        print(f"✅ Environment loaded successfully")
        print(f"✅ Number of tools: {len(env.tools_info)}")
        
        # Check if our tools are included
        tool_names = [tool['function']['name'] for tool in env.tools_info]
        print(f"✅ Available tools: {', '.join(tool_names)}")
        
        if 'clinical_term_mapper' in tool_names:
            print("✅ Clinical Term Mapper tool found")
        else:
            print("❌ Clinical Term Mapper tool not found")
            return False
            
        if 'analyze_user_query' in tool_names:
            print("✅ Query Analyzer tool found")
        else:
            print("❌ Query Analyzer tool not found")
            return False
        
        print("\n🎉 Environment loading test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Environment loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Clinical Term Mapper Integration Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test the tools directly
    success &= test_clinical_term_mapper()
    
    # Test environment loading
    success &= test_environment_loading()
    
    if success:
        print("\n\n🎉 All tests passed! The integration is working correctly.")
        print("\nYou can now run the evaluation with:")
        print("bash run_mimic_iv.sh")
    else:
        print("\n\n❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 