# Interactive Knowledge Graph Generator

A comprehensive Streamlit application that integrates Claude AI and Neo4j to create, edit, analyze, and visualize knowledge graphs. Transform natural language descriptions into interactive graph visualizations with advanced analytics capabilities.

![Knowledge Graph Generator](https://img.shields.io/badge/Neo4j-5.0+-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![Claude AI](https://img.shields.io/badge/Claude-3.5%20Sonnet-purple)

## Features

### AI-Powered Graph Generation
- **Natural Language Input**: Describe your domain in plain English
- **Intelligent Extraction**: Claude AI automatically identifies entities and relationships
- **Smart Visualization**: Auto-assigns colors and organizes graph layout
- **Multi-Domain Support**: Works across any knowledge domain

### Advanced Analytics
- **Centrality Analysis**: Degree, betweenness, and closeness centrality metrics
- **Community Detection**: Identify clusters and connected components
- **Path Analysis**: Find shortest paths and analyze graph connectivity
- **Visual Insights**: Interactive charts and key metrics dashboard

### Interactive Graph Editing
- **Node Management**: Add, edit, and delete nodes with custom properties
- **Edge Creation**: Create relationships between nodes with labels
- **Real-time Updates**: See changes instantly in the visualization
- **Validation**: Automatic duplicate detection and data validation

### Persistent Storage
- **Neo4j Integration**: Save graphs to production-grade graph database
- **Version Control**: Track multiple graph versions with metadata
- **Quick Loading**: Instant access to previously saved graphs
- **Metadata Tracking**: Store descriptions, timestamps, and statistics

### Multi-Format Export
- **JSON Export**: Complete graph data with metadata
- **CSV Export**: Separate node and edge files for analysis
- **GraphML Export**: Standard format for network analysis tools (Gephi, Cytoscape)
- **One-Click Download**: Export with custom filenames

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Web UI                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Generate │  │   Edit   │  │Analytics │  │  Export  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ▲ │
                              │ │
                    ┌─────────┘ └─────────┐
                    │                     │
         ┌──────────▼──────────┐  ┌──────▼───────────┐
         │    Claude AI API    │  │  Neo4j Database  │
         │  (Graph Generation) │  │ (Storage/Query)  │
         └─────────────────────┘  └──────────────────┘
```

### Technology Stack

- **Frontend**: Streamlit + streamlit-agraph (interactive visualization)
- **AI Engine**: Anthropic Claude 3.5 Sonnet
- **Database**: Neo4j 5.0+ (graph database)
- **Backend**: Python 3.9+ with neo4j-driver
- **Analytics**: Pandas, Plotly for data visualization
- **Infrastructure**: Docker + Docker Compose
- **Package Manager**: UV (fast Python package manager)

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| Main Application | `app.py` | Streamlit UI and all functionality |
| Neo4j Connection | `app.py:33-312` | Database operations and analytics |
| AI Integration | `app.py:314-349` | Claude-powered graph generation |
| Graph Editor | `app.py:945-1066` | Manual node/edge manipulation |
| Analytics Engine | `app.py:143-312` | Centrality, community, path analysis |
| Export System | `app.py:351-442` | JSON, CSV, GraphML export |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development)
- Claude API Key ([get one here](https://console.anthropic.com/))
- UV package manager (optional, recommended)

### 1. Clone Repository

```bash
git clone <repository-url>
cd kgtest
```

### 2. Set Environment Variables

Create a `.env` file:

```bash
ANTHROPIC_API_KEY=your_claude_api_key_here
NEO4J_PASSWORD=your_secure_password
```

### 3. Start Services

```bash
# Start Neo4j and Streamlit
make up

# View logs
make logs

# Open applications
make app     # Opens http://localhost:8501
make neo4j   # Opens http://localhost:7474
```

### 4. Configure Application

1. Open Streamlit app: http://localhost:8501
2. In sidebar, expand "Database Setup"
3. Connect to Neo4j:
   - URI: `bolt://neo4j:7687`
   - Username: `neo4j`
   - Password: (from your `.env` file)
4. In sidebar, expand "AI Configuration"
5. Enter your Claude API key

### 5. Generate Your First Graph

1. Go to **Generate** tab
2. Enter a description:
   ```
   Create a graph showing the solar system with planets,
   their moons, and orbital relationships
   ```
3. Click **Generate Graph**
4. View the interactive visualization
5. Save to Neo4j for analytics

## Usage Guide

### AI Graph Generation

```
Example prompts:
- "Map the characters and relationships in Romeo and Juliet"
- "Create a technology stack graph for a web application"
- "Show the organizational structure of a startup company"
- "Model the water cycle with all processes and states"
```

### Manual Graph Building

1. **Add Nodes**: Define entities with unique IDs, labels, and colors
2. **Create Edges**: Connect nodes with relationship labels
3. **Edit Properties**: Update node labels and colors
4. **Delete Elements**: Remove nodes (cascades to edges) or edges individually

### Running Analytics

Requirements: Graph must be saved to Neo4j first

**Centrality Analysis**:
- Identifies most connected nodes (degree)
- Finds critical bridge nodes (betweenness)
- Measures average distance to others (closeness)

**Community Detection**:
- Groups related nodes into communities
- Visualizes cluster sizes
- Identifies isolated components

**Path Analysis**:
- Find shortest path between specific nodes
- Calculate graph-wide path statistics
- Analyze connectivity metrics

### Exporting Graphs

**JSON Format**: Complete graph with metadata
```json
{
  "metadata": {...},
  "nodes": [{...}],
  "edges": [{...}]
}
```

**CSV Format**: Two files (nodes.csv, edges.csv)
- Import into spreadsheets, databases, or analysis tools

**GraphML Format**: XML-based graph format
- Compatible with Gephi, Cytoscape, NetworkX

## Development

### Local Development Setup

```bash
# Install dependencies
uv sync

# Run Streamlit locally
streamlit run app.py

# Run with UV
uv run streamlit run app.py
```

### Make Commands

```bash
make help      # Show all commands
make up        # Start all services
make down      # Stop all services
make restart   # Restart services
make logs      # View service logs
make clean     # Remove containers and images
make neo4j     # Open Neo4j browser
make app       # Open Streamlit app
```

### Project Structure

```
kgtest/
├── app.py                      # Main Streamlit application
├── main.py                     # Simple entry point
├── Dockerfile                  # Streamlit container
├── docker-compose.yml          # Multi-service orchestration
├── Makefile                    # Development commands
├── pyproject.toml              # Python dependencies (UV)
├── CLAUDE.md                   # Claude Code instructions
├── README.md                   # This file
└── docs/
    ├── SKILL.md                # Neo4j Cypher guide
    └── NEO4J_5_MIGRATION.md    # Migration documentation
```

## Neo4j 5.0+ Compliance

All Cypher queries follow modern Neo4j 5.0+ best practices:

- ✅ Modern `COUNT{}` and `CALL{}` subquery patterns
- ✅ Explicit NULL filtering for all sorting operations
- ✅ No deprecated functions (id(), OPTIONAL MATCH patterns)
- ✅ Explicit WITH clauses for aggregations
- ✅ Optimized query performance

See [NEO4J_5_MIGRATION.md](docs/NEO4J_5_MIGRATION.md) for details.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | Required |
| `NEO4J_PASSWORD` | Neo4j database password | Required |
| `NEO4J_URI` | Neo4j connection URI | `bolt://neo4j:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |

### Neo4j Schema

**Nodes**:
- `:KGNode` - Graph nodes with properties: `{id, label, color, graph_name}`
- `:GraphMeta` - Graph metadata: `{name, description, created_date, node_count, edge_count}`

**Relationships**:
- `:RELATED` - Connections with properties: `{label, graph_name}`

## Sample Graphs

### AI/Technology Domain
- 15 nodes covering AI, ML, NLP, Computer Vision
- Relationships between technologies, frameworks, and applications
- Load via sidebar: "AI/Technology" sample

### Vehicle Lifecycle Management
- 30 nodes covering entire vehicle lifecycle
- Stakeholders, processes, components, documentation
- Load via sidebar: "Vehicle Lifecycle" sample

## Troubleshooting

### Neo4j Connection Issues
```bash
# Check if Neo4j is running
docker ps

# View Neo4j logs
docker logs kgtest-neo4j-1

# Restart services
make restart
```

### Visualization Errors
- Try refreshing the page
- Clear current graph and regenerate
- Check browser console for errors

### API Rate Limits
- Claude API has rate limits
- Wait a moment between generations
- Check your API quota at console.anthropic.com

## Performance Tips

1. **Start Simple**: Generate small graphs first (10-20 nodes)
2. **Save Frequently**: Save to Neo4j before running analytics
3. **Use Filters**: Filter data before visualization for large graphs
4. **Profile Queries**: Use `PROFILE` in Neo4j browser for optimization

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Dependencies

Core dependencies managed via UV:

- `streamlit` - Web application framework
- `neo4j` - Graph database driver
- `streamlit-agraph` - Interactive graph visualization
- `anthropic` - Claude AI API client
- `pandas` - Data manipulation and analysis
- `plotly` - Interactive charts and visualizations
- `python-dotenv` - Environment variable management

## License

[Your License Here]

## Acknowledgments

- **Anthropic Claude AI** for intelligent graph generation
- **Neo4j** for powerful graph database technology
- **Streamlit** for rapid web application development
- **streamlit-agraph** for interactive graph visualization

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review CLAUDE.md for development guidelines

## Roadmap

- [ ] Quantified Path Patterns (QPP) for complex traversals
- [ ] Type predicates for property validation
- [ ] Label expressions for advanced filtering
- [ ] Export to additional formats (DOT, GEXF)
- [ ] Real-time collaborative editing
- [ ] Graph versioning and diff visualization
- [ ] Custom analytics plugins
- [ ] REST API for programmatic access

---

Built with ❤️ using Neo4j, and Streamlit
