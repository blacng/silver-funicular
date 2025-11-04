# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Streamlit application called "Interactive Knowledge Graph Generator" that integrates Claude AI and Neo4j to create, edit, analyze, and visualize knowledge graphs. The application provides a complete workflow from AI-powered graph generation to advanced network analysis.

## Architecture

- **app.py**: Main Streamlit application with complete UI and all functionality
- **main.py**: Simple entry point script  
- **Dockerfile**: Containerized Streamlit application
- **docker-compose.yml**: Neo4j + Streamlit services with networking
- **Makefile**: Infrastructure management commands
- **UV package manager**: Fast dependency management with `pyproject.toml`

### Key Components

- **Neo4jConnection class** (app.py:28): Database operations, analytics, save/load functionality
- **Claude AI integration** (app.py:291): Intelligent graph generation from natural language
- **Graph editing system** (app.py:423-693): Manual node/edge creation, editing, deletion
- **Analytics engine** (app.py:142-289): Centrality, community detection, path analysis
- **Export system** (app.py:329-420): JSON, CSV, GraphML export functionality
- **Interactive visualization**: Uses streamlit-agraph with error handling
- **Tabbed UI interface**: Organized workflow with Generate/Load/Edit/Analytics/Export tabs

## Development Commands

### Infrastructure Management (Recommended)
```bash
# Show all available commands
make help

# Start all services (Neo4j + Streamlit)
make up

# Stop all services
make down

# Restart all services
make restart

# View service logs
make logs

# Clean up all Docker resources
make clean

# Quick browser shortcuts
make neo4j  # Opens http://localhost:7474
make app    # Opens http://localhost:8501
```

### Direct Commands (Alternative)
```bash
# Install dependencies
uv sync

# Run the Streamlit application locally
streamlit run app.py

# Start Neo4j database
docker-compose up -d

# Stop Neo4j database  
docker-compose down

# Run simple main script
python main.py
```

## Environment Setup

Create a `.env` file with:
```
ANTHROPIC_API_KEY=your_claude_api_key
NEO4J_PASSWORD=your_neo4j_password
```

## Features Implemented

### 🚀 **AI Graph Generation**
- Natural language to knowledge graph conversion using Claude AI
- Intelligent node/edge extraction with automatic color assignment
- Error handling and validation for API interactions

### 📂 **Graph Management**
- Save graphs to Neo4j with metadata (name, description, timestamps)
- Load and display previously saved graphs
- List all saved graphs with statistics
- Clear and manage current graph state

### ✏️ **Manual Graph Editing**
- Add new nodes with custom IDs, labels, and colors
- Create edges between existing nodes with relationship labels
- Edit node properties (label, color) for existing nodes
- Delete nodes and edges with cascade cleanup
- Input validation and duplicate prevention

### 📊 **Advanced Analytics**
- **Centrality Analysis**: Degree, betweenness, and closeness centrality
- **Community Detection**: Connected component analysis with visualization
- **Path Analysis**: Shortest paths between nodes and graph connectivity metrics
- Interactive charts and key insights display
- Works with saved graphs using native Cypher algorithms

### 📤 **Export Functionality**
- **JSON Export**: Complete graph data with metadata
- **CSV Export**: Separate files for nodes and edges
- **GraphML Export**: Standard format for network analysis tools
- Downloadable files with custom naming

### 🎨 **User Interface**
- Clean tabbed interface for organized workflows
- Real-time graph visualization with node interaction
- Comprehensive error handling and user feedback
- Responsive design with consistent styling

## Dependencies

- **streamlit**: Web application framework and UI components
- **neo4j**: Database driver for graph storage and analytics
- **streamlit-agraph**: Interactive graph visualization with click handling
- **anthropic**: Claude AI API integration for graph generation
- **pandas**: Data manipulation and DataFrame operations for analytics
- **plotly**: Chart visualizations for analytics results
- **python-dotenv**: Environment variable management for API keys

## Important Notes

### Edge Object Attributes
```python
# IMPORTANT: Edge objects use 'to' attribute, not 'target'
# Constructor: Edge(source="A", target="B", label="rel") 
# Access: edge.source, edge.to, edge.label (NOT edge.target)
```

### Neo4j Schema
- **Nodes**: `:KGNode` with properties `{id, label, color, graph_name}`
- **Relationships**: `:RELATED` with properties `{label, graph_name}`
- **Metadata**: `:GraphMeta` with properties `{name, description, created_date, node_count, edge_count}`

### Analytics Requirements
- Graph analytics require graphs to be saved to Neo4j first
- Uses native Cypher algorithms for compatibility (no GDS dependency)
- Centrality metrics are calculated using custom Cypher queries

## Recent Updates and Bug Fixes

### UI/UX Improvements
- **Fixed Path Analysis UI Flow**: Path type selection (Graph Summary vs Specific Path) now appears immediately when Path Analysis is selected, rather than after clicking "Run Analysis"
- **Improved Analytics Workflow**: Source/target node selectors appear immediately when "Specific Path" is chosen
- **Enhanced User Experience**: All analysis options are visible upfront for better decision making

### Technical Fixes
- **Resolved pandas Import Error**: Fixed `UnboundLocalError` by removing duplicate pandas import inside analytics function
- **Fixed Cypher Path Analysis**: Corrected syntax error in path summary query by using `path = (a)-[:RELATED*]-(b)` instead of relationship variable
- **Edge Attribute Consistency**: Comprehensive fix for streamlit-agraph Edge object attribute usage (use `edge.to` not `edge.target`)
- **Neo4j GDS Compatibility**: Replaced problematic Graph Data Science projections with reliable native Cypher algorithms
- **JSON Parse Error Resolution**: Added comprehensive error handling for graph visualization component

### Algorithm Implementations
- **Centrality Analysis**: Custom Cypher implementations for degree, betweenness approximation, and closeness centrality
- **Community Detection**: Connected component analysis with alphabetical fallback grouping
- **Path Analysis**: Native Cypher shortest path with proper error handling and type safety

### Development Workflow
- **Make Commands**: Added infrastructure management with `make infrastructure-up/down/restart/logs`
- **Detached Mode**: Docker containers run in background for improved development workflow
- **Containerized Development**: Complete Docker setup for consistent cross-platform development
- **Dependency Management** always use uv for dependency management and virtual environments. do not use pip directly.
- use uv to run python files.
- Make sure the Neo4j syntax conform with Neo4j 5.0. Use the skills.md file in the project directory as a guide.