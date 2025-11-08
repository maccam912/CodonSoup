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
import logging
import random
import sys
import time

import numpy as np
import requests
from organism import Organism, extract_genes
from world import World

# Client identification
CLIENT_ID = f"soup_{int(time.time()) % 100000}"
DEFAULT_SERVER = "https://codonsoup.rackspace.koski.co"


logger = logging.getLogger("codonsoup.client")


def configure_logging(level_name: str, quiet: bool) -> None:
    """Configure root logging for the client."""

    # Quiet mode always forces WARNING regardless of user supplied level
    if quiet:
        level = logging.WARNING
    else:
        level = getattr(logging, level_name.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    logger.debug("Logging configured (requested_level=%s, quiet=%s)", level_name, quiet)


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
    endpoint = f"{server_url.rstrip('/')}/api/genome"
    logger.info("Attempting to fetch immigrant genome", extra={"endpoint": endpoint, "timeout": timeout})

    try:
        response = requests.get(endpoint, timeout=timeout)
        logger.info(
            "Received response from server",
            extra={
                "status_code": response.status_code,
                "elapsed": response.elapsed.total_seconds() if response.elapsed else None,
                "headers": dict(response.headers),
            },
        )
        response.raise_for_status()
        data = response.json()

        genome = data.get("genome")
        if genome is None:
            logger.warning("Server response missing genome payload", extra={"response_body": data})
        else:
            logger.info(
                "Fetched immigrant genome successfully",
                extra={"genome_length": len(genome), "sample_fitness": data.get("fitness")},
            )

        return genome
    except requests.exceptions.Timeout:
        logger.error("Timed out while fetching immigrant genome", exc_info=True)
        return None
    except requests.exceptions.RequestException:
        logger.exception("HTTP error while fetching immigrant genome")
        return None
    except (json.JSONDecodeError, KeyError):
        logger.exception("Invalid genome data returned by server")
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
    payload = {
        "genome": [float(x) for x in genome],
        "fitness": float(fitness),
        "client_id": CLIENT_ID,
    }

    endpoint = f"{server_url.rstrip('/')}/api/genome"
    logger.info(
        "Submitting genome to server",
        extra={
            "endpoint": endpoint,
            "timeout": timeout,
            "payload_fitness": payload["fitness"],
            "payload_length": len(payload["genome"]),
        },
    )

    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)
        logger.info(
            "Received response from genome submission",
            extra={"status_code": response.status_code, "headers": dict(response.headers)},
        )
        response.raise_for_status()
        logger.info("Genome submitted successfully")
        return True
    except requests.exceptions.Timeout:
        logger.error("Timed out while submitting genome", exc_info=True)
        return False
    except requests.exceptions.RequestException:
        logger.exception("HTTP error while submitting genome")
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
        logger.info("🧫 Generation %s", gen_num)
        logger.info("   Starting population: %s", len(world.organisms))

    # Run simulation ticks
    for tick in range(ticks):
        world.update()

        # Progress updates
        if verbose and tick % 100 == 0 and tick > 0:
            stats = world.get_statistics()
            logger.info(
                "   Tick %s: pop=%s, avg_energy=%.2f, avg_fitness=%.2f",
                f"{tick:3d}",
                f"{stats['population']:3d}",
                stats["avg_energy"],
                stats["avg_fitness"],
            )

    # Final statistics
    stats = world.get_statistics()
    if verbose:
        logger.info(
            "   Final: pop=%s, avg_fitness=%.2f",
            stats["population"],
            stats["avg_fitness"],
        )

    # Get fittest organism
    fittest = world.get_fittest()

    if fittest and verbose:
        logger.info(
            "   🏆 Fittest: fitness=%.2f, energy=%.2f, genome_len=%s",
            fittest.fitness,
            fittest.energy,
            len(fittest.genome),
        )
        logger.info(
            "      Phenotype: speed=%.2f, turn=%.2f, photo=%.2f, eff=%.2f",
            fittest.phenotype[0],
            fittest.phenotype[1],
            fittest.phenotype[2],
            fittest.phenotype[3],
        )

        # Show gene expression
        genes = extract_genes(fittest.genome)
        logger.info(
            "      Active genes: %s, lengths: %s",
            len(genes),
            [len(g) for g in genes],
        )
    elif verbose:
        logger.warning("   Population collapsed; no fittest organism available")

    return fittest


def main():
    """Main client loop"""
    parser = argparse.ArgumentParser(description="CodonSoup Client - Distributed Artificial Life Evolution")
    parser.add_argument("--server", default=DEFAULT_SERVER, help=f"Server URL (default: {DEFAULT_SERVER})")
    parser.add_argument("--generations", type=int, default=1000, help="Number of generations to run (default: 1000)")
    parser.add_argument("--ticks", type=int, default=300, help="Simulation ticks per generation (default: 300)")
    parser.add_argument("--population", type=int, default=30, help="Initial population size (default: 30)")
    parser.add_argument("--min-delay", type=int, default=30, help="Minimum delay between generations in seconds (default: 30)")
    parser.add_argument("--max-delay", type=int, default=90, help="Maximum delay between generations in seconds (default: 90)")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    parser.add_argument("--offline", action="store_true", help="Run without server connection (local evolution only)")

    args = parser.parse_args()

    configure_logging(args.log_level, args.quiet)

    logger.info("🧬 CodonSoup Client Starting")
    logger.info("   Client ID: %s", CLIENT_ID)
    logger.info("   Server: %s", args.server)
    logger.info("   Generations: %s", args.generations)
    logger.info("   Ticks/gen: %s", args.ticks)
    logger.info("   Initial pop: %s", args.population)
    logger.info("   Delay between gens: %s-%ss", args.min_delay, args.max_delay)

    if args.offline:
        logger.warning("   Mode: OFFLINE (no server connection)")

    # Add initial random delay to spread out client start times
    if not args.offline:
        initial_delay = random.randint(0, args.max_delay)
        logger.info("⏱️  Initial delay: %ss (spreading client load)", initial_delay)
        time.sleep(initial_delay)

    # Main evolution loop
    for gen in range(args.generations):
        # Create new world
        world = World()

        # Seed population
        seed_genome = None

        if not args.offline:
            # Try to fetch immigrant genome from server
            logger.debug("Requesting immigrant genome before generation %s", gen)
            seed_genome = fetch_immigrant_genome(args.server)
            if seed_genome:
                logger.info("📥 Fetched immigrant genome (length: %s)", len(seed_genome))

        # Fallback to starter genome
        if seed_genome is None:
            seed_genome = create_starter_genome()
            logger.info("🌱 Using starter genome (no immigrants available)")

        # Create initial population
        for _ in range(args.population):
            # Random positions
            pos = np.random.rand(2) * 120
            logger.debug("Seeding organism at position %s", pos)
            world.add_organism(Organism(seed_genome, pos))

        # Run generation
        fittest = run_generation(world, gen, ticks=args.ticks, verbose=not args.quiet)

        # Submit fittest genome back to pool
        if fittest and not args.offline:
            logger.debug(
                "Preparing to submit fittest genome",
                extra={
                    "fitness": fittest.fitness,
                    "genome_length": len(fittest.genome),
                },
            )
            success = submit_genome(args.server, fittest.genome, fittest.fitness)
            if success:
                logger.info("📤 Submitted genome to pool")
            else:
                logger.warning("Submission of fittest genome failed")

        # Randomized delay between generations to spread server load
        delay = random.randint(args.min_delay, args.max_delay)
        if not args.quiet:
            logger.info("⏱️  Waiting %ss until next generation...", delay)
        time.sleep(delay)

    logger.info("✅ Evolution complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("❌ Unhandled error occurred: %s", e)
        sys.exit(1)
