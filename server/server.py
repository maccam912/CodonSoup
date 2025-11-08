"""
CodonSoup Server - Genome Pool & Statistics Dashboard

This server manages a shared gene pool where clients can:
- Fetch high-fitness genomes to seed their populations
- Submit their best genomes back to the pool
- View real-time statistics on gene expression patterns
"""

import json
import os
import sqlite3
from collections import defaultdict

import numpy as np
from flask import Flask, jsonify, render_template, request

DB_PATH = "data/soup.db"
MAX_POOL_SIZE = int(os.getenv("MAX_POOL_SIZE", "10000"))  # Maximum genomes to keep in pool
app = Flask(__name__)


def init_db():
    """Initialize the SQLite database with genome storage table"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS genomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        genome TEXT,
        fitness REAL,
        length INTEGER,
        client_id TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )"""
    )
    conn.commit()
    conn.close()


def extract_genes(genome, threshold=0.95):
    """
    Extract all genes from a genome using START/STOP codon rules.

    START codon: value > threshold (default 0.95)
    STOP codon: value < 0.05
    Valid gene: length between 3 and 20 codons

    Args:
        genome: List of float values [0, 1]
        threshold: START codon activation threshold

    Returns:
        List of gene sequences (each gene is a list of floats)
    """
    if not genome or len(genome) < 5:
        return []

    genes = []
    gene_positions = set()  # Track gene positions to avoid duplicates
    in_gene = False
    start_pos = 0

    # Circular genome: wrap around to catch genes spanning the origin
    extended = genome + genome[:25]

    for i, val in enumerate(extended):
        if i >= len(genome) + 20:  # Don't go too far past the end
            break

        if not in_gene and val > threshold:
            in_gene = True
            start_pos = i
        elif in_gene and val < 0.05:
            gene_len = i - start_pos - 1  # Exclude START and STOP
            if 3 <= gene_len <= 20:
                # Normalize start position to genome coordinates
                normalized_start = start_pos % len(genome)

                # Only add if we haven't seen this gene position before
                if normalized_start not in gene_positions:
                    gene_positions.add(normalized_start)

                    # Extract gene (wrap-aware)
                    gene_seq = []
                    for j in range(start_pos + 1, i):
                        gene_seq.append(extended[j % len(genome)])
                    genes.append(gene_seq)
            in_gene = False

    return genes


@app.route("/")
def dashboard():
    """Serve the web dashboard"""
    return render_template("dashboard.html")


@app.route("/api/genome", methods=["GET"])
def get_genome():
    """
    Fetch a high-fitness genome from the pool.

    Selection: Weighted toward high fitness with some randomness
    Fallback: Returns a minimal starter genome if pool is empty

    Returns:
        JSON: {"genome": [list of float values]}
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get top performers with some randomness
    c.execute("SELECT genome FROM genomes ORDER BY fitness DESC, RANDOM() LIMIT 1")
    row = c.fetchone()
    conn.close()

    if row:
        return jsonify({"genome": json.loads(row[0])})

    # Default starter genome: mostly neutral with one functional gene
    # Structure: [neutral junk] + [START, functional codons, STOP] + [more junk]
    starter = [0.5] * 60 + [0.96, 0.4, 0.4, 0.4, 0.04] + [0.5] * 40
    return jsonify({"genome": starter})


@app.route("/api/genome", methods=["POST"])
def post_genome():
    """
    Submit a genome to the pool.

    Expects JSON:
        {
            "genome": [float values],
            "fitness": float,
            "client_id": string
        }

    Pool management: Keeps top genomes by fitness (configurable via MAX_POOL_SIZE)

    Returns:
        JSON: {"status": "ok"}
    """
    data = request.json

    if not data or "genome" not in data or "fitness" not in data:
        return jsonify({"status": "error", "message": "Missing genome or fitness"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Insert new genome
    c.execute(
        "INSERT INTO genomes (genome, fitness, length, client_id) VALUES (?, ?, ?, ?)",
        (json.dumps(data["genome"]), data["fitness"], len(data["genome"]), data.get("client_id", "anonymous")),
    )

    # Prune pool to top N genomes
    c.execute(
        """
        DELETE FROM genomes
        WHERE id NOT IN (
            SELECT id FROM genomes
            ORDER BY fitness DESC
            LIMIT ?
        )
    """,
        (MAX_POOL_SIZE,),
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


@app.route("/api/gene_stats")
def gene_stats():
    """
    Analyze active genes in recent high-fitness genomes.

    Returns statistics on:
    - Gene length distribution
    - Average fitness per gene length
    - Gene count by length

    Only analyzes genomes from the last 6 hours to show current trends.

    Returns:
        JSON: {
            gene_length: {
                "count": int,
                "avg_fitness": float
            },
            ...
        }
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get recent genomes
    c.execute(
        """
        SELECT genome, fitness
        FROM genomes
        WHERE timestamp > datetime('now', '-6 hours')
        ORDER BY fitness DESC
        LIMIT 500
    """
    )
    rows = c.fetchall()
    conn.close()

    # Analyze gene expression
    active_genes = defaultdict(list)

    for genome_str, fitness in rows:
        try:
            genome = json.loads(genome_str)
            genes = extract_genes(genome)

            for gene in genes:
                gene_length = len(gene)
                active_genes[gene_length].append(fitness)
        except (json.JSONDecodeError, Exception):
            continue

    # Compute statistics
    stats = {
        str(length): {"count": len(fitness_vals), "avg_fitness": float(np.mean(fitness_vals))}
        for length, fitness_vals in active_genes.items()
    }

    return jsonify(stats)


@app.route("/api/pool_status")
def pool_status():
    """
    Get overall pool statistics.

    Returns:
        JSON: {
            "total_genomes": int,
            "avg_fitness": float,
            "avg_length": float,
            "top_fitness": float
        }
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        SELECT
            COUNT(*) as total,
            AVG(fitness) as avg_fitness,
            AVG(length) as avg_length,
            MAX(fitness) as top_fitness
        FROM genomes
    """
    )
    row = c.fetchone()
    conn.close()

    if row and row[0] > 0:
        return jsonify(
            {
                "total_genomes": row[0],
                "avg_fitness": float(row[1] or 0),
                "avg_length": float(row[2] or 0),
                "top_fitness": float(row[3] or 0),
            }
        )

    return jsonify({"total_genomes": 0, "avg_fitness": 0, "avg_length": 0, "top_fitness": 0})


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    init_db()
    print("🧬 CodonSoup Server starting...")
    print("📊 Dashboard: http://localhost:8080")
    print("🔬 API: http://localhost:8080/api/*")
    app.run(host="0.0.0.0", port=8080, debug=False)
