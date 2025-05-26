# Clinical Term Mapper Tools for AI612 Project 2

## Overview

This implementation adds **Clinical Term Mapper** tools to boost the baseline accuracy of the conversational text-to-SQL agent for the MIMIC-IV database. The tools address the core challenge mentioned in the project specifications: mapping natural language medical terms to their database representations.

## Problem Addressed

From the project specs:
> "EHRs contain a large amount of differently phrased clinical terms (e.g., 'diabetes' → 'type 2 diabetes mellitus' or 'other specified diabetes mellitus'), requiring the model to accurately map relevant data to the user's request."

## Solution: Two New Tools

### 1. Clinical Term Mapper (`clinical_term_mapper`)
Maps clinical terms, abbreviations, and natural language to their corresponding database representations.

**Features:**
- **Medical Abbreviation Expansion**: Maps common medical abbreviations (e.g., "Hb" → "hemoglobin")
- **Term Standardization**: Normalizes medical terminology variations
- **Database Schema Matching**: Fuzzy matches against actual table/column names
- **Confidence Scoring**: Provides confidence scores for mappings

**Example Usage:**
```json
Input: "hb"
Output: {
  "original_term": "hb",
  "mappings": [
    {
      "original_term": "hb",
      "mapped_term": "hemoglobin",
      "mapping_type": "abbreviation_expansion",
      "confidence": 0.95
    }
  ],
  "related_terms": ["hemoglobin", "hgb"]
}
```

### 2. Query Analyzer (`analyze_user_query`)
Analyzes user queries and suggests better search terms for database exploration.

**Features:**
- **Medical Term Extraction**: Identifies medical terms in natural language queries
- **Search Pattern Suggestions**: Suggests relevant SQL patterns and table names
- **Related Term Discovery**: Finds related medical concepts

**Example Usage:**
```json
Input: "Show me recent lab results for patients"
Output: {
  "mapped_terms": ["laboratory", "labs"],
  "related_terms": ["lab test", "lab result"],
  "search_patterns": ["ORDER BY charttime DESC LIMIT", "labevents table"]
}
```

## Implementation Details

### File Structure
```
src/envs/mimic_iv/tools/
├── clinical_term_mapper.py    # Main implementation
├── sql_db_query.py           # Existing tool
├── sql_db_schema.py          # Existing tool
├── value_substring_search.py # Existing tool
└── sql_db_list_tables.py     # Existing tool

src/envs/mimic_iv/
└── env.py                    # Updated to include new tools

test_clinical_mapper.py       # Basic functionality tests
test_integration.py          # Full integration tests
```

### Medical Knowledge Base
The tools include comprehensive medical abbreviations and term variations:

- **60+ Medical Abbreviations**: Common lab values, vital signs, conditions, medications
- **Term Variations**: Different ways to express medical concepts
- **Database Integration**: Fuzzy matching against actual MIMIC-IV schema

## How to Run

### 1. Basic Functionality Test
```bash
python test_clinical_mapper.py
```
Tests core functionality without requiring database access.

### 2. Full Integration Test
```bash
python test_integration.py
```
Tests integration with the MIMIC-IV database and environment loading.

### 3. Run Full Evaluation
```bash
bash run_mimic_iv.sh
```
Runs the complete evaluation with the enhanced tools.

### 4. Custom Evaluation
```bash
python run.py --env mimic_iv \
    --model gemini/gemini-2.0-flash \
    --agent_strategy tool-calling \
    --temperature 0.0 \
    --seed 42 \
    --num_trials 4 \
    --max_concurrency 5 \
    --eval_mode valid
```

## Expected Performance Improvements

The Clinical Term Mapper tools should improve baseline accuracy by:

1. **Better Term Recognition**: Correctly mapping medical abbreviations and variations
2. **Improved Query Understanding**: Helping the agent understand medical context
3. **Enhanced Database Navigation**: Suggesting relevant tables and search patterns
4. **Reduced Ambiguity**: Providing confidence scores for term mappings

## Integration with Existing Framework

The tools are fully integrated into the existing framework:

- **Follows existing patterns**: Uses the same BaseModel structure as other tools
- **Automatic registration**: Tools are automatically available to the agent
- **No breaking changes**: Existing functionality remains unchanged
- **Extensible**: Easy to add more medical knowledge

## Tool Specifications

### Clinical Term Mapper Tool
- **Name**: `clinical_term_mapper`
- **Input**: `term` (string) - The clinical term to map
- **Output**: JSON with mappings, confidence scores, and related terms

### Query Analyzer Tool
- **Name**: `analyze_user_query`
- **Input**: `user_query` (string) - The natural language query to analyze
- **Output**: JSON with mapped terms, related terms, and search patterns

## Troubleshooting

### Common Issues

1. **Database not found**: Ensure `src/envs/mimic_iv/mimic_iv.sqlite` exists
2. **Import errors**: Make sure you're running from the project root directory
3. **Tool not found**: Verify the tools are properly registered in `env.py`

### Testing Without Database
The basic functionality can be tested without the MIMIC-IV database:
```bash
python test_clinical_mapper.py
```

## Future Enhancements

Potential improvements for even better performance:
- **Expanded medical knowledge base**
- **Context-aware term disambiguation**
- **Learning from successful queries**
- **Integration with medical ontologies (UMLS, SNOMED)**

## Conclusion

The Clinical Term Mapper tools provide a targeted solution to improve the agent's understanding of medical terminology, directly addressing the core challenge of mapping natural language medical terms to database representations in the MIMIC-IV environment. 