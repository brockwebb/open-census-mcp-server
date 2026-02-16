# Expert Review Key

**CONFIDENTIAL — Do not share with reviewers until after data collection**

This key maps the randomized A/B/C labels to actual conditions.

Query        Num   A            B            C           
------------------------------------------------------------
NORM-001     1     rag          control      pragmatics  
NORM-002     2     pragmatics   rag          control     
NORM-005     3     rag          pragmatics   control     
NORM-008     4     rag          pragmatics   control     
NORM-010     5     rag          control      pragmatics  
NORM-012     6     control      rag          pragmatics  
NORM-014     7     rag          pragmatics   control     
NORM-015     8     rag          pragmatics   control     
GEO-002      9     rag          pragmatics   control     
GEO-003      10    rag          control      pragmatics  
GEO-005      11    control      rag          pragmatics  
GEO-006      12    pragmatics   rag          control     
SML-001      13    control      rag          pragmatics  
SML-002      14    rag          pragmatics   control     
SML-004      15    control      rag          pragmatics  
TMP-001      16    control      pragmatics   rag         
TMP-002      17    rag          pragmatics   control     
AMB-001      18    pragmatics   control      rag         
AMB-003      19    pragmatics   rag          control     
PER-001b     20    pragmatics   rag          control     

## Legend
- **control**: Bare LLM (no tools, no retrieval)
- **rag**: Retrieval-augmented generation from source documents
- **pragmatics**: Structured pragmatic context via MCP tools
