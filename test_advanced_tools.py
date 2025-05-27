#!/usr/bin/env python3
"""
Test script for the new Advanced Query Fixer and Query Complexity Analyzer tools.
"""

import os
import sys
from sqlalchemy import create_engine

# Add the src directory to the path so we can import modules
sys.path.append('src')

def test_advanced_query_fixer():
    """Test the advanced query fixer tool."""
    print("🧪 Testing Advanced Query Fixer")
    print("=" * 50)
    
    # Check if database exists
    db_path = "src/envs/mimic_iv/mimic_iv.sqlite"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        # Import the tool
        from src.envs.mimic_iv.tools.advanced_query_fixer import AdvancedQueryFixer
        
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")
        
        # Test AdvancedQueryFixer
        print("\n1. Testing Advanced Query Fixer:")
        print("-" * 30)
        
        fixer = AdvancedQueryFixer(engine=engine)
        
        # Test cases for advanced error patterns
        test_cases = [
            {
                "name": "SQLite EXTRACT Function Issue",
                "query": "SELECT * FROM admissions WHERE EXTRACT(YEAR FROM admittime) = 2100",
                "error": "Error: (sqlite3.OperationalError) near \"FROM\": syntax error",
                "expected": "Convert EXTRACT to STRFTIME"
            },
            {
                "name": "procedures_icd.chartdate Issue",
                "query": "SELECT * FROM procedures_icd WHERE chartdate > '2100-01-01'",
                "error": "Error: (sqlite3.OperationalError) no such column: procedures_icd.chartdate",
                "expected": "Use admissions.admittime instead"
            },
            {
                "name": "icd9_code vs icd_code Issue",
                "query": "SELECT * FROM procedures_icd p JOIN d_icd_procedures d ON p.icd9_code = d.icd9_code",
                "error": "Error: (sqlite3.OperationalError) no such column: p.icd9_code",
                "expected": "Use icd_code instead of icd9_code"
            }
        ]
        
        for test_case in test_cases:
            print(f"\n{test_case['name']}:")
            print(f"  Query: {test_case['query'][:50]}...")
            print(f"  Error: {test_case['error'][:50]}...")
            try:
                result = fixer.invoke(test_case['query'], test_case['error'])
                print(f"✅ Successfully provided advanced fix")
                # Parse the JSON to verify it's valid
                import json
                parsed = json.loads(result)
                print(f"   Error category: {parsed['error_analysis']['error_category']}")
                print(f"   Confidence: {parsed.get('confidence_score', 0):.2f}")
                if parsed.get('auto_corrected_query'):
                    print(f"   ✅ Auto-corrected query provided")
            except Exception as e:
                print(f"❌ Error in advanced fixer: {e}")
                return False
        
        print("\n🎉 Advanced Query Fixer tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Advanced Query Fixer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_query_complexity_analyzer():
    """Test the query complexity analyzer tool."""
    print("\n\n🧪 Testing Query Complexity Analyzer")
    print("=" * 50)
    
    # Check if database exists
    db_path = "src/envs/mimic_iv/mimic_iv.sqlite"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        # Import the tool
        from src.envs.mimic_iv.tools.advanced_query_fixer import QueryComplexityAnalyzer
        
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")
        
        # Test QueryComplexityAnalyzer
        print("\n1. Testing Query Complexity Analyzer:")
        print("-" * 30)
        
        analyzer = QueryComplexityAnalyzer(engine=engine)
        
        test_goals = [
            {
                "goal": "find microbiological tests for patients with drainage procedures",
                "complexity": "high"
            },
            {
                "goal": "get recent lab results for a specific patient",
                "complexity": "medium"
            },
            {
                "goal": "count total number of admissions",
                "complexity": "low"
            }
        ]
        
        for test_goal in test_goals:
            print(f"\nGoal: '{test_goal['goal']}'")
            try:
                result = analyzer.invoke(test_goal['goal'])
                print(f"✅ Successfully analyzed complexity")
                # Parse the JSON to verify it's valid
                import json
                parsed = json.loads(result)
                print(f"   Complexity: {parsed['complexity_assessment']['level']}")
                print(f"   Strategy: {parsed['recommended_strategy'][:50]}...")
                print(f"   Steps: {len(parsed['step_by_step_approach'])}")
            except Exception as e:
                print(f"❌ Error analyzing complexity: {e}")
                return False
        
        print("\n🎉 Query Complexity Analyzer tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Query Complexity Analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_integration():
    """Test that the environment loads correctly with all new tools."""
    print("\n\n🧪 Testing Environment Integration")
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
        
        # Check if our new tools are included
        tool_names = [tool['function']['name'] for tool in env.tools_info]
        print(f"✅ Available tools: {', '.join(tool_names)}")
        
        expected_new_tools = [
            'advanced_query_fixer',
            'query_complexity_analyzer'
        ]
        
        for tool_name in expected_new_tools:
            if tool_name in tool_names:
                print(f"✅ {tool_name} tool found")
            else:
                print(f"❌ {tool_name} tool not found")
                return False
        
        print(f"\n✅ Total tools now: {len(tool_names)} (was 6, now 8)")
        print("\n🎉 Environment integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Environment integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all advanced tool tests."""
    print("🚀 Advanced Tools Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test the advanced query fixer
    success &= test_advanced_query_fixer()
    
    # Test the query complexity analyzer
    success &= test_query_complexity_analyzer()
    
    # Test environment integration
    success &= test_environment_integration()
    
    if success:
        print("\n\n🎉 All advanced tool tests passed!")
        print("\nNew Advanced Tool Set (8 tools total):")
        print("1. Clinical Term Mapper - Maps medical terms and abbreviations")
        print("2. Query Analyzer - Analyzes user queries for medical concepts")
        print("3. Smart Schema Assistant - Provides intelligent schema guidance")
        print("4. Query Validator - Validates queries and suggests corrections")
        print("5. Query Optimizer - Fixes failed queries and prevents retry loops")
        print("6. Execution Helper - Suggests efficient execution strategies")
        print("7. 🆕 Advanced Query Fixer - Handles complex error patterns")
        print("8. 🆕 Query Complexity Analyzer - Breaks down complex queries")
        print("\nExpected improvements:")
        print("• Better handling of SQLite-specific syntax issues")
        print("• Advanced auto-correction for complex errors")
        print("• Query complexity management and simplification")
        print("• Target: 67-68% performance (up from 65%)")
        print("\nYou can now run the evaluation with:")
        print("bash run_mimic_iv.sh")
    else:
        print("\n\n❌ Some advanced tool tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 