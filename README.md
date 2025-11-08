# 🧬 CodonSoup

**Emergent Gene Regulatory Networks in Distributed Artificial Life**

CodonSoup is a distributed artificial life simulation where genes are not predefined—they **emerge spontaneously** from variable-length genomes through START/STOP delimiters. Genes can overlap arbitrarily, most DNA is junk, and each client evolves light-seeking "bacteria" whose phenotypes arise from on-the-fly gene expression.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/badge/uv-package%20manager-blue)](https://github.com/astral-sh/uv)

## 🎯 Core Concept

Each client simulates a 120×120 petri dish where bacteria swim in a nutrient-light gradient. Genomes are **circular, variable-length sequences** (50–200 codons) where:

- **START codon**: value > 0.95 (activates expression)
- **STOP codon**: value < 0.05 (terminates expression)
- **Gene**: Any sequence between START-STOP (if length 3–20)
- **Protein**: The gene's *content hash* determines which of 4 traits it modifies; the gene's *mean value* determines magnitude
- **Regulation**: Special "operator" genes can modify expression threshold, creating cascading epistatic effects

**Genes can**: overlap (nested or shared regions), be junk (non-coding), duplicate, or encode regulatory proteins that suppress/activate other genes.

## ✨ Key Features

### Biological Realism
- **De Novo Genes**: Mutations create new START codons, activating silent regions
- **Overlapping Genes**: Multiple genes can share the same DNA sequence
- **Junk DNA**: 80-90% of genomes never express; neutral until promoters appear
- **Regulatory Networks**: Genes can modify expression thresholds, unlocking cascades
- **Gene Duplication**: Instant copying of functional units with subsequent divergence

### Emergent Dynamics
- **Gene Birth**: Discovery of first functional genes causes fitness jumps
- **Regulatory Revolutions**: Rare regulatory genes unlock multiple genes at once (punctuated equilibrium)
- **Genome Bloat**: Successful lineages accumulate junk DNA over time
- **Metapopulation Waves**: Breakthrough genes spread globally across clients

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/maccam912/CodonSoup.git
cd CodonSoup

# Start server and 3 clients
docker-compose up

# View dashboard
open http://localhost:8080
```

### Manual Setup with uv

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/maccam912/CodonSoup.git
cd CodonSoup

# Sync dependencies (creates .venv automatically)
uv sync --all-extras

# Set up pre-commit hooks (optional but recommended)
make pre-commit

# Terminal 1: Start server
make server
# or: uv run python server/server.py

# Terminal 2: Run client
make client
# or: uv run python client/client.py --server=http://localhost:8080
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CodonSoup Server                      │
│  ┌────────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │  Gene Pool DB  │  │  REST API   │  │  Dashboard   │ │
│  │   (SQLite)     │  │ /api/genome │  │   (Flask)    │ │
│  └────────────────┘  └─────────────┘  └──────────────┘ │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌─────▼───────┐
    │  Client 1   │ │  Client 2   │ │  Client N   │
    │             │ │             │ │             │
    │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │
    │ │Organism │ │ │ │Organism │ │ │ │Organism │ │
    │ │Organism │ │ │ │Organism │ │ │ │Organism │ │
    │ │Organism │ │ │ │Organism │ │ │ │Organism │ │
    │ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │
    └─────────────┘ └─────────────┘ └─────────────┘
         ▲                 ▲                 ▲
         │                 │                 │
         └─────── Fetch immigrant genomes ───┘
         └─────── Submit fittest genomes ────┘
```

## 🧫 How It Works

### Genome Structure

```
Genome: [0.5, 0.5, 0.96, 0.4, 0.5, 0.6, 0.04, 0.5, ...]
         └──┬──┘ └──┬──┘ └────┬─────┘ └──┬──┘ └─┬─┘
         Junk DNA  START   Gene (3)    STOP  Junk
```

### Gene Expression

1. **Scan genome** for START codons (> 0.95)
2. **Find matching STOP** codons (< 0.05)
3. **Extract sequence** between START and STOP
4. **Validate length** (3-20 codons)
5. **Interpret as protein**:
   - Trait = hash(gene) mod 4
   - Magnitude = mean(gene) * 2 - 1
   - Regulatory = contains extreme values

### Phenotype Traits

Each organism has 4 traits determined by gene expression:

| Trait | Range | Effect |
|-------|-------|--------|
| **Speed** | 0-3 | Movement speed (pixels/tick) |
| **Turn Rate** | 0-0.5 | Turning ability (radians/tick) |
| **Phototaxis** | -1 to +1 | Light attraction (+) or repulsion (-) |
| **Efficiency** | 0-1 | Resource → energy conversion rate |

### Evolution Cycle

```
1. Fetch immigrant genome from server
2. Seed local population (30 organisms)
3. Simulate 300 ticks:
   - Move based on phototaxis
   - Metabolize (light × efficiency × nutrients)
   - Reproduce if energy > 25
   - Apply mutations (point, insertion, deletion, duplication)
4. Submit fittest genome to server
5. Repeat
```

## 🧪 Development & Testing

### Running Tests

```bash
# Run all tests
make test
# or: uv run pytest

# Run with coverage report
make coverage
# This generates an HTML report in htmlcov/index.html

# Run specific test file
uv run pytest tests/client/test_organism.py -v
```

### Code Quality

```bash
# Lint code with ruff
make lint
# or: uv run ruff check .

# Auto-format code with ruff
make format
# or: uv run ruff format . && uv run ruff check --fix .

# Run pre-commit hooks manually
uv run pre-commit run --all-files
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:
- **Ruff**: Linting and formatting
- **Pytest**: Runs tests with coverage before each commit

Install hooks:
```bash
make pre-commit
# or: uv run pre-commit install
```

Once installed, hooks run automatically on `git commit`.

## 🐋 Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up

# Scale clients
docker-compose up --scale client=10

# Run single client
docker run --rm codonsoup-client --server=http://your-server:8080

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f client

# Stop all
docker-compose down
```

## 📈 Dashboard

The web dashboard (`http://localhost:8080`) shows:

- **Pool Status**: Total genomes, top fitness, averages
- **Active Genes**: Gene lengths and counts
- **Performance Chart**: Gene length vs. average fitness (bubble chart)

**Key Insights**:
- Optimal gene lengths emerge (usually 8-12 codons)
- Short genes too weak, long genes waste energy
- Regulatory genes cluster at length ~5
- Fitness spikes indicate breakthrough mutations

## 🔬 Advanced Usage

### Custom Parameters

```bash
# Client with custom settings
python client.py \
  --server=http://localhost:8080 \
  --generations=100 \
  --ticks=500 \
  --population=50 \
  --quiet

# Offline evolution (no server)
python client.py --offline --generations=20
```

### Server Configuration

Edit `server/server.py` or set environment variables:

```python
DB_PATH = "data/soup.db"  # Database location
app.run(host="0.0.0.0", port=8080)  # Server address
```

### API Endpoints

```bash
# Get genome
curl http://localhost:8080/api/genome

# Submit genome
curl -X POST http://localhost:8080/api/genome \
  -H "Content-Type: application/json" \
  -d '{"genome": [...], "fitness": 42.5, "client_id": "test"}'

# Get statistics
curl http://localhost:8080/api/gene_stats
curl http://localhost:8080/api/pool_status

# Health check
curl http://localhost:8080/health
```

## 🎓 Educational Use

CodonSoup demonstrates:

- **Evolutionary algorithms**: Mutation, selection, genetic drift
- **Emergence**: Complex behaviors from simple rules
- **Distributed systems**: Client-server architecture, gene pool dynamics
- **Bioinformatics**: Gene expression, regulatory networks, genomic structure
- **Alife research**: Open-ended evolution, minimal genome complexity

Perfect for:
- Computational biology courses
- Evolutionary computation labs
- Distributed systems projects
- Science communication / visualization

## 🛠️ Development

### Project Structure

```
CodonSoup/
├── server/
│   ├── server.py           # Flask API & gene pool
│   └── templates/
│       └── dashboard.html  # Web dashboard
├── client/
│   ├── organism.py         # Gene expression & evolution
│   ├── world.py            # Simulation environment
│   └── client.py           # Main runner
├── tests/
│   ├── client/             # Client tests
│   └── server/             # Server tests
├── .github/
│   └── workflows/          # CI/CD pipelines
├── Dockerfile.server       # Server container
├── Dockerfile.client       # Client container
├── docker-compose.yml      # Orchestration
└── requirements-*.txt      # Dependencies
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Run tests (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 🔍 Troubleshooting

### Server won't start
```bash
# Check if port 8080 is in use
lsof -i :8080

# Use different port
cd server
python server.py  # Edit port in server.py
```

### Client can't connect
```bash
# Verify server is running
curl http://localhost:8080/health

# Check server URL
python client.py --server=http://localhost:8080
```

### Tests failing
```bash
# Install all dependencies
pip install -r requirements-server.txt
pip install -r requirements-client.txt
pip install -r requirements-test.txt

# Run tests verbosely
pytest -v
```

### Docker issues
```bash
# Rebuild containers
docker-compose build --no-cache

# Check logs
docker-compose logs server
docker-compose logs client

# Clean up
docker-compose down -v
docker system prune -a
```

## 📚 References

- **Gene Overlapping**: [Wikipedia - Overlapping gene](https://en.wikipedia.org/wiki/Overlapping_gene)
- **Regulatory Networks**: [Artificial Gene Regulatory Networks](https://www.mitpressjournals.org/doi/abs/10.1162/106454600568879)
- **Junk DNA**: [Non-coding DNA](https://en.wikipedia.org/wiki/Non-coding_DNA)
- **Artificial Life**: [Open-ended evolution](https://www.mitpressjournals.org/doi/full/10.1162/isal_a_00245)

## 📄 License

This project is open source. Add your preferred license.

## 🙏 Acknowledgments

Inspired by:
- Tierra (Tom Ray, 1991) - First digital evolution system
- Avida (Adami et al., 1993) - Evolution of digital organisms
- PolyWorld (Larry Yaeger) - Artificial life simulation

## 📞 Contact

For questions, issues, or contributions, please open an issue on GitHub.

---

**Made with 🧬 by the artificial life community**
