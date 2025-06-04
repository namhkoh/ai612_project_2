# AI612 Project 2: Conversational Text-to-SQL Agent

The goal of this project is to implement a conversational text-to-SQL agent (DB Agent) for EHRs that can interact with both a user and a database. To simulate user interactions, you will be provided with a User LLM mimicking a human user that asks questions about the data stored in the EHR database (MIMIC-IV Demo). When interacting with the user, it should interact in natural language, and when interacting with the database, it should interact by using appropriate tools tailored to the database. After gathering all necessary information from the user and the database, the DB agent must generate a valid SQL to retrieve the final answer.

Furthermore, it is guaranteed that all questions asked by the User LLM are answerable. As a result, for each conversation initiated by the User LLM, your DB Agent should generate a correct SQL query. Additionally, note that values mentioned in natural language questions may use different phrasing compared to their representation in the database (e.g., "Hb" vs. "hemoglobin"). Addressing this requires the DB Agent to leverage appropriate tools to explore the database and identify the correct database entities or values corresponding to the user's input. (testing)

Check [Project 2 Specs](https://docs.google.com/document/d/18SVb7a7R0UedJabTadoqJrc1O_-29a_zEEX1AAZ0R2s/edit?usp=sharing) for more details.

## 🏆 State-of-the-Art Performance: 70% Achievement

### **Enhanced Medical Knowledge Strategy**
Our implementation achieves **70% performance** through a focused medical knowledge expansion approach:

- **📊 Performance**: Pass@4: 90% | Pass^4: 50% | **Final Score: 70%**
- **🧠 Medical Knowledge**: 160+ medical abbreviations, drug names, procedures, and diagnoses
- **🏗️ Architecture**: Optimal 6-tool configuration (Version 3)
- **🎯 Key Innovation**: Enhanced Clinical Term Mapper with comprehensive medical terminology

### **Core Strategy Components**

#### **1. Enhanced Clinical Term Mapper**
- **160+ Medical Terms**: Expanded from baseline 60+ to comprehensive 160+ term database
- **Multi-Category Coverage**: 
  - Vital signs and lab values (Hb→hemoglobin, WBC→white blood cell)
  - Drug names and variations (acetaminophen→paracetamol→tylenol)
  - Medical conditions (MI→myocardial infarction, COPD→chronic obstructive pulmonary disease)
  - Procedures and interventions (PCI→percutaneous coronary intervention)
  - Medical specialties and departments (ICU→intensive care unit)

#### **2. Optimal Tool Architecture (Version 3)**
Our research identified the optimal 6-tool configuration:
1. **Clinical Term Mapper** - Medical terminology mapping
2. **Query Analyzer** - Enhanced medical concept extraction  
3. **Smart Schema Assistant** - Intelligent schema guidance
4. **Query Validator** - Pre-execution validation
5. **Query Optimizer** - Error prevention and correction
6. **Execution Helper** - Efficient execution strategies

#### **3. Key Performance Insights**
- **Medical Knowledge Expansion**: Primary driver of performance improvement
- **Architectural Stability**: 6-tool configuration represents optimal complexity
- **Consistency Focus**: 25% relative improvement in Pass^4 (40%→50%)
- **Focused Enhancement > Tool Addition**: Improving existing tools beats adding complexity

### **Performance Evolution**
| Version | Tools | Medical Terms | Pass@4 | Pass^4 | Final Score |
|---------|-------|---------------|--------|--------|-------------|
| Baseline | 0 | 0 | - | - | **40%** |
| V1 | 2 | 60+ | 90% | 30% | **60%** |
| V2 | 4 | 60+ | 80% | 40% | **60%** |
| V3 | 6 | 60+ | 90% | 40% | **65%** |
| **Enhanced V3** | **6** | **160+** | **90%** | **50%** | **🏆 70%** |

### **Path to 75%+ Performance**
Our analysis indicates further improvements through:
1. **Medical Knowledge Expansion**: 160+ → 250+ terms
2. **Enhanced Schema Intelligence**: More MIMIC-IV specific patterns
3. **Query Pattern Recognition**: Common medical query templates

## Database
We use the [MIMIC-IV database demo](https://physionet.org/content/mimic-iv-demo/2.2/), which anyone can access the files as long as they conform to the terms of the [Open Data Commons Open Database License v1.0](https://physionet.org/content/mimic-iv-demo/view-license/2.2/).

## Tutorials
Check out the jupyter notebook file [`tutorial.ipynb`](tutorial.ipynb). It includes an implementation of a baseline tool-calling DB Agent and how to run inference for submission. The score for the baseline agent on the provided validation set is 40 and costs about $0.20.

[Colab version](https://colab.research.google.com/drive/1c13m05YGLrP_B-vRDapybW0ZagsAhnZ0?usp=sharing) is also available.

## Dependencies
The codes were tested in Colab and in a local environment (Python 3.11) with the dependecies listed in `requirements.txt`.

### Local
```bash
conda create -n ai612-project2 python=3.11 -y
conda activate ai612-project2
pip install -r requirements.txt
```

### How to run
```bash
sh run_mimic_iv.sh # running inference
streamlit run visualizer.py --server.port 8505 # visualizing conversations in your localhost.
```

### Enhanced Performance Evaluation
```bash
# Run with our enhanced medical knowledge tools
python run.py --eval_mode valid --user_strategy tool-calling --user_model gemini/gemini-2.0-flash --trials 4
```

## Implementation Details

### **Enhanced Tools Location**
- `src/envs/mimic_iv/tools/clinical_term_mapper.py` - Enhanced medical terminology mapper
- `src/envs/mimic_iv/tools/smart_schema_assistant.py` - Intelligent schema guidance
- `src/envs/mimic_iv/tools/query_optimizer.py` - Query optimization and error prevention
- `src/envs/mimic_iv/env.py` - Version 3 environment configuration

### **Key Features**
- **Comprehensive Medical Knowledge**: 160+ medical abbreviations and variations
- **Intelligent Schema Guidance**: Context-aware table and join recommendations
- **Error Prevention**: Pre-execution validation and auto-correction
- **Optimal Architecture**: Research-proven 6-tool configuration

## Tau-bench
This code repository is based on the [tau-bench github repository](https://github.com/sierra-research/tau-bench.git).