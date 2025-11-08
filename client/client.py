"""
CodonSoup Client - Distributed Evolution Runner

Connects to the CodonSoup server to participate in distributed evolution:
1. Fetch a high-fitness genome from the global pool
2. Seed local population with immigrants
3. Run simulation for N ticks
4. Submit fittest genome back to the pool
5. Repeat
"""

import argparse
import json
import sys
import time

import numpy as np
import requests
from organism import Organism, extract_genes
from world import World

# Client identification
CLIENT_ID = f"soup_{int(time.time()) % 100000}"
DEFAULT_SERVER = "https://codonsoup.rackspace.koski.co"


def create_starter_genome():
    """
    Create a minimal viable starter genome.

    Structure:
    - Neutral junk DNA (50% values)
    - One functional gene (START + 3 codons + STOP)
    - More neutral DNA

    This gives evolution a foothold without biasing the outcome.
    """
    return (
        [0.5] * 60  # Junk DNA
        + [0.96, 0.4, 0.4, 0.4, 0.04]  # Minimal gene
        + [0.5] * 40  # More junk
    )


def fetch_immigrant_genome(server_url, timeout=5):
    """
    Fetch a genome from the server's gene pool.

    Args:
        server_url: Base URL of CodonSoup server
        timeout: Request timeout in seconds

    Returns:
        List of float values (genome), or None if fetch failed
    """
    try:
        response = requests.get(f"{server_url}/api/genome", timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("genome")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Failed to fetch immigrant genome: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  Invalid genome data from server: {e}")
        return None


def submit_genome(server_url, genome, fitness, timeout=5):
    """
    Submit a genome to the server's gene pool.

    Args:
        server_url: Base URL of CodonSoup server
        genome: List of float values
        fitness: Fitness score
        timeout: Request timeout in seconds

    Returns:
        True if submission succeeded, False otherwise
    """
    try:
        # Convert numpy types to Python native types for JSON serialization
        genome_list = [float(x) for x in genome]
        fitness_float = float(fitness)

        response = requests.post(
            f"{server_url}/api/genome", json={"genome": genome_list, "fitness": fitness_float, "client_id": CLIENT_ID}, timeout=timeout
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Failed to submit genome: {e}")
        return False


def run_generation(world, gen_num, ticks=300, verbose=True):
    """
    Run a single generation (multiple simulation ticks).

    Args:
        world: World instance
        gen_num: Generation number (for logging)
        ticks: Number of simulation ticks to run
        verbose: Whether to print progress

    Returns:
        Organism with highest fitness, or None if population died out
    """
    if verbose:
        print(f"\n🧫 Generation {gen_num}")
        print(f"   Starting population: {len(world.organisms)}")

    # Run simulation ticks
    for tick in range(ticks):
        world.update()

        # Progress updates
        if verbose and tick % 100 == 0 and tick > 0:
            stats = world.get_statistics()
            print(
                f"   Tick {tick:3d}: "
                f"pop={stats['population']:3d}, "
                f"avg_energy={stats['avg_energy']:5.2f}, "
                f"avg_fitness={stats['avg_fitness']:6.2f}"
            )

    # Final statistics
    stats = world.get_statistics()
    if verbose:
        print(f"   Final: pop={stats['population']}, avg_fitness={stats['avg_fitness']:.2f}")

    # Get fittest organism
    fittest = world.get_fittest()

    if fittest and verbose:
        print(f"   🏆 Fittest: fitness={fittest.fitness:.2f}, energy={fittest.energy:.2f}, genome_len={len(fittest.genome)}")
        print(
            f"      Phenotype: speed={fittest.phenotype[0]:.2f}, "
            f"turn={fittest.phenotype[1]:.2f}, "
            f"photo={fittest.phenotype[2]:.2f}, "
            f"eff={fittest.phenotype[3]:.2f}"
        )

        # Show gene expression
        genes = extract_genes(fittest.genome)
        print(f"      Active genes: {len(genes)}, lengths: {[len(g) for g in genes]}")

    return fittest


def main():
    """Main client loop"""
    parser = argparse.ArgumentParser(description="CodonSoup Client - Distributed Artificial Life Evolution")
    parser.add_argument("--server", default=DEFAULT_SERVER, help=f"Server URL (default: {DEFAULT_SERVER})")
    parser.add_argument("--generations", type=int, default=50, help="Number of generations to run (default: 50)")
    parser.add_argument("--ticks", type=int, default=300, help="Simulation ticks per generation (default: 300)")
    parser.add_argument("--population", type=int, default=30, help="Initial population size (default: 30)")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    parser.add_argument("--offline", action="store_true", help="Run without server connection (local evolution only)")

    args = parser.parse_args()

    print("🧬 CodonSoup Client Starting")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Server: {args.server}")
    print(f"   Generations: {args.generations}")
    print(f"   Ticks/gen: {args.ticks}")
    print(f"   Initial pop: {args.population}")

    if args.offline:
        print("   Mode: OFFLINE (no server connection)")
    print()

    # Main evolution loop
    for gen in range(args.generations):
        # Create new world
        world = World()

        # Seed population
        seed_genome = None

        if not args.offline:
            # Try to fetch immigrant genome from server
            seed_genome = fetch_immigrant_genome(args.server)
            if seed_genome:
                print(f"📥 Fetched immigrant genome (length: {len(seed_genome)})")

        # Fallback to starter genome
        if seed_genome is None:
            seed_genome = create_starter_genome()
            print("🌱 Using starter genome (no immigrants available)")

        # Create initial population
        for _ in range(args.population):
            # Random positions
            pos = np.random.rand(2) * 120
            world.add_organism(Organism(seed_genome, pos))

        # Run generation
        fittest = run_generation(world, gen, ticks=args.ticks, verbose=not args.quiet)

        # Submit fittest genome back to pool
        if fittest and not args.offline:
            success = submit_genome(args.server, fittest.genome, fittest.fitness)
            if success:
                print("📤 Submitted genome to pool")

        # Brief pause between generations
        if not args.quiet:
            time.sleep(1)

    print("\n✅ Evolution complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
