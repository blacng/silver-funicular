# Interactive Knowledge Graph Generator - Complete Application Flow Diagram

## Overview Architecture Diagram

```
┌─────────────────┐
│ User Starts App │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ Configuration   │
├─────────────────┤
│ • Neo4j Setup   │
│ • Claude AI Key │
│ • Sample Data   │
└─────────┬───────┘
          │
          ▼
    ┌─────────┐    YES   ┌─────────────┐
    │Neo4j    │─────────▶│ Connected   │
    │Connect? │          │ Success     │
    └─────────┘          └──────┬──────┘
          │ NO                  │
          ▼                     │
    ┌─────────────┐             │
    │ Show Error  │             │
    └─────────────┘             │
                                ▼
          ┌─────────────────────────────────────────┐
          │          Main Interface                 │
          │  ┌─────────────┐  ┌─────────────────┐   │
          │  │    Tabs     │  │  Visualization  │   │
          │  │             │  │     Panel       │   │
          │  └─────────────┘  └─────────────────┘   │
          └─────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ GENERATE    │       │    LOAD     │       │    EDIT     │
│             │       │             │       │             │
│ User Input  │       │ Get Saved   │       │ Add Nodes   │
│     │       │       │ Graphs      │       │ Add Edges   │
│     ▼       │       │     │       │       │ Edit Items  │
│ Claude AI   │       │     ▼       │       │ Delete      │
│ Processing  │       │ Select &    │       │             │
│     │       │       │ Load Graph  │       │             │
│     ▼       │       │             │       │             │
│ Update      │       │             │       │             │
│ Session     │       │             │       │             │
└─────────────┘       └─────────────┘       └─────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ ANALYTICS   │       │   EXPORT    │       │ SESSION     │
│             │       │             │       │ STATE       │
│ Centrality  │       │ Save to DB  │       │             │
│ Community   │       │ JSON Export │       │ • nodes     │
│ Path        │       │ CSV Export  │       │ • edges     │
│ Analysis    │       │ GraphML     │       │ • neo4j_    │
│     │       │       │ Export      │       │   connected │
│     ▼       │       │     │       │       │             │
│ Display     │       │     ▼       │       │             │
│ Charts      │       │ Download    │       │             │
└─────────────┘       └─────────────┘       └─────────────┘
```

## Detailed Component Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ User Input  │  │ Generate    │  │ Graph       │  │ Tabbed  │ │
│  │ Text Area   │  │ Button      │  │ Visual-     │  │ Inter-  │ │
│  │ (666-672)   │  │ (673-692)   │  │ ization     │  │ face    │ │
│  │             │  │             │  │ (1154-1194) │  │         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │                  │                  ▲                   
          ▼                  ▼                  │                   
┌─────────────────────────────────────────────────────────────────┐
│                 SESSION STATE MANAGEMENT                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │
│  │ nodes       │  │ edges       │  │ UI State & Neo4j        │   │
│  │ (Node list) │  │ (Edge list) │  │ Connection Status       │   │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                  │                                      
          ▼                  ▼                                      
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE AI PROCESSING                         │
├─────────────────────────────────────────────────────────────────┤
│  Text Input                                                     │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐     │
│  │ Prompt      │───▶│ API Call    │───▶│ JSON Response   │     │
│  │ Construction│    │ to Claude   │    │ Parsing         │     │
│  │ (302-326)   │    │ (328-332)   │    │ (334-343)       │     │
│  └─────────────┘    └─────────────┘    └─────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                                                    │                
                                                    ▼                
┌─────────────────────────────────────────────────────────────────┐
│                      NEO4J DATABASE                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │
│  │ GraphMeta   │  │ KGNode      │  │ RELATED                 │   │
│  │ Metadata    │  │ Graph       │  │ Relationships           │   │
│  │ Storage     │  │ Vertices    │  │ Graph Edges             │   │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ▲                  ▲                  
                              │                  │                  
                    ┌─────────┴────────┬─────────┴────────┐         
                    │                  │                  │         
                    ▼                  ▼                  ▼         
          ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     
          │ ANALYTICS   │    │   EXPORT    │    │ SAVE/LOAD   │     
          │ ENGINE      │    │   SYSTEM    │    │ OPERATIONS  │     
          ├─────────────┤    ├─────────────┤    ├─────────────┤     
          │ Centrality  │    │ JSON Export │    │ Save Graph  │     
          │ Community   │    │ CSV Export  │    │ Load Graph  │     
          │ Path Anal.  │    │ GraphML     │    │ List Graphs │     
          │ Plotly      │    │ Download    │    │             │     
          │ Charts      │    │ Files       │    │             │     
          └─────────────┘    └─────────────┘    └─────────────┘     

ERROR HANDLING:
├─ API Errors (348-349) ────────────▶ Error Display
├─ JSON Parse Errors (346-347) ─────▶ Error Display  
├─ Database Connection Errors ──────▶ Error Display
└─ Visualization Errors (1190-1192) ▶ Error Display
```

## Key Components & Data Flow

### 1. **User Input Processing**
```
Text Input → Button Click → API Validation → Claude Processing
```

### 2. **AI Pipeline**
```
Natural Language → Structured Prompt → Claude API → JSON Response → Python Objects
```

### 3. **State Management**
```
Python Objects → Session State → UI Persistence → Graph Visualization
```

### 4. **Database Integration**
```
Session State ↔ Neo4j (Save/Load) ↔ Cypher Queries ↔ Graph Storage
```

### 5. **Analytics Pipeline**
```
Neo4j Data → Cypher Algorithms → Statistical Analysis → Plotly Charts
```

### 6. **Export Workflow**
```
Session State → Format Conversion → File Generation → Download
```

## Critical Integration Points

- **Lines 297-349**: Core AI processing function
- **Lines 49-95**: Neo4j save operations
- **Lines 112-140**: Neo4j load operations
- **Lines 1154-1194**: Graph visualization rendering
- **Lines 142-289**: Analytics computation engine

## Error Handling Strategy

- **API Errors**: Graceful Claude API failure handling
- **Parse Errors**: JSON validation and error display
- **DB Errors**: Neo4j connection and query error management
- **UI Errors**: Visualization component error recovery