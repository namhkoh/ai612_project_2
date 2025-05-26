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
        
        print("\n🎉 Clinical Term Mapper tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Clinical Term Mapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_smart_schema_assistant():
    """Test the smart schema assistant tools."""
    print("\n\n🧪 Testing Smart Schema Assistant")
    print("=" * 50)
    
    # Check if database exists
    db_path = "src/envs/mimic_iv/mimic_iv.sqlite"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        # Import the tools
        from src.envs.mimic_iv.tools.smart_schema_assistant import SmartSchemaAssistant, QueryValidator
        
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")
        
        # Test SmartSchemaAssistant
        print("\n1. Testing SmartSchemaAssistant:")
        print("-" * 30)
        
        assistant = SmartSchemaAssistant(engine=engine)
        
        test_intents = [
            "find lab results for patients",
            "get medication history",
            "analyze procedures"
        ]
        
        for intent in test_intents:
            print(f"\nTesting intent: '{intent}'")
            try:
                result = assistant.invoke(intent)
                print(f"✅ Successfully provided guidance")
                # Parse the JSON to verify it's valid
                import json
                parsed = json.loads(result)
                print(f"   Recommended tables: {len(parsed['recommended_tables'])}")
                print(f"   Required joins: {len(parsed['required_joins'])}")
            except Exception as e:
                print(f"❌ Error providing guidance: {e}")
                return False
        
        # Test QueryValidator
        print("\n\n2. Testing QueryValidator:")
        print("-" * 30)
        
        validator = QueryValidator(engine=engine)
        
        test_queries = [
            "SELECT labevents.label FROM labevents",  # Should catch wrong column
            "SELECT admittime FROM admissions"        # Should be valid
        ]
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            try:
                result = validator.invoke(query)
                print(f"✅ Successfully validated query")
                # Parse the JSON to verify it's valid
                parsed = json.loads(result)
                print(f"   Valid: {parsed['is_valid']}")
                print(f"   Issues found: {len(parsed['issues'])}")
            except Exception as e:
                print(f"❌ Error validating query: {e}")
                return False
        
        print("\n🎉 Smart Schema Assistant tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Smart Schema Assistant test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_query_optimizer():
    """Test the query optimizer tools."""
    print("\n\n🧪 Testing Query Optimizer")
    print("=" * 50)
    
    # Check if database exists
    db_path = "src/envs/mimic_iv/mimic_iv.sqlite"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        # Import the tools
        from src.envs.mimic_iv.tools.query_optimizer import QueryOptimizer, ExecutionHelper
        
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")
        
        # Test QueryOptimizer
        print("\n1. Testing QueryOptimizer:")
        print("-" * 30)
        
        optimizer = QueryOptimizer(engine=engine)
        
        test_cases = [
            {
                "query": "SELECT MAX(inputevents.starttime) FROM inputevents JOIN prescriptions ON inputevents.hadm_id = prescriptions.hadm_id WHERE prescriptions.starttime IN (SELECT MAX(starttime) FROM admissions)",
                "error": "Error: (sqlite3.OperationalError) ambiguous column name: starttime"
            },
            {
                "query": "SELECT labevents.label FROM labevents",
                "error": "Error: (sqlite3.OperationalError) no such column: labevents.label"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest case {i}:")
            print(f"Query: {test_case['query'][:50]}...")
            print(f"Error: {test_case['error'][:50]}...")
            try:
                result = optimizer.invoke(test_case['query'], test_case['error'])
                print(f"✅ Successfully provided fix suggestions")
                # Parse the JSON to verify it's valid
                import json
                parsed = json.loads(result)
                print(f"   Error type: {parsed['error_type']}")
                print(f"   Quick fixes: {len(parsed['quick_fixes'])}")
                if parsed['corrected_query']:
                    print(f"   ✅ Auto-corrected query provided")
            except Exception as e:
                print(f"❌ Error optimizing query: {e}")
                return False
        
        # Test ExecutionHelper
        print("\n\n2. Testing ExecutionHelper:")
        print("-" * 30)
        
        helper = ExecutionHelper(engine=engine)
        
        test_goals = [
            "find recent lab results",
            "count patients by diagnosis",
            "join multiple tables"
        ]
        
        for goal in test_goals:
            print(f"\nTesting goal: '{goal}'")
            try:
                result = helper.invoke(goal)
                print(f"✅ Successfully provided execution strategy")
                # Parse the JSON to verify it's valid
                parsed = json.loads(result)
                print(f"   Approach: {parsed['recommended_approach'][:50]}...")
                print(f"   Tips: {len(parsed['efficiency_tips'])}")
            except Exception as e:
                print(f"❌ Error providing strategy: {e}")
                return False
        
        print("\n🎉 Query Optimizer tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Query Optimizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_loading():
    """Test that the environment loads correctly with all new tools."""
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
        
        expected_tools = [
            'clinical_term_mapper',
            'analyze_user_query', 
            'smart_schema_assistant',
            'query_validator',
            'query_optimizer',
            'execution_helper'
        ]
        
        for tool_name in expected_tools:
            if tool_name in tool_names:
                print(f"✅ {tool_name} tool found")
            else:
                print(f"❌ {tool_name} tool not found")
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
    print("🚀 Complete Integration Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test the clinical term mapper tools
    success &= test_clinical_term_mapper()
    
    # Test the smart schema assistant tools
    success &= test_smart_schema_assistant()
    
    # Test the query optimizer tools
    success &= test_query_optimizer()
    
    # Test environment loading
    success &= test_environment_loading()
    
    if success:
        print("\n\n🎉 All tests passed! The complete integration is working correctly.")
        print("\nFinal tool set (6 tools):")
        print("1. Clinical Term Mapper - Maps medical terms and abbreviations")
        print("2. Query Analyzer - Analyzes user queries for medical concepts")
        print("3. Smart Schema Assistant - Provides intelligent schema guidance")
        print("4. Query Validator - Validates queries and suggests corrections")
        print("5. Query Optimizer - Fixes failed queries and prevents retry loops")
        print("6. Execution Helper - Suggests efficient execution strategies")
        print("\nThis should significantly improve both Pass@4 and Pass^4!")
        print("\nYou can now run the evaluation with:")
        print("bash run_mimic_iv.sh")
    else:
        print("\n\n❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 