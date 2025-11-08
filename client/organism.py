"""
CodonSoup Organism - Gene Expression & Evolution

Implements:
- Variable-length circular genomes
- START/STOP codon-based gene extraction
- Overlapping genes and junk DNA
- Regulatory gene networks
- Mutation operators (point, insertion, deletion, duplication)
"""

import uuid

import numpy as np


def extract_genes(genome, threshold=0.95):
    """
    Extract all genes from a circular genome using START/STOP delimiters.

    Gene detection rules:
    - START codon: value > threshold (default 0.95)
    - STOP codon: value < 0.05
    - Valid gene: sequence between START-STOP with length 3-20 codons
    - Genome is circular: wraps around to detect genes spanning origin

    Args:
        genome: List of float values [0, 1] representing codons
        threshold: Activation threshold for START codons

    Returns:
        List of genes, where each gene is a list of codon values
    """
    if not genome or len(genome) < 5:
        return []

    genes = []
    gene_positions = set()  # Track gene positions to avoid duplicates
    in_gene = False
    start_pos = 0

    # Extend genome to handle circular wrap-around
    # Max gene length is 20, so extend by 25 to be safe
    extended = genome + genome[:25]

    for i, val in enumerate(extended):
        if i >= len(genome) + 20:  # Don't go too far past the end
            break

        if not in_gene and val > threshold:
            # Found START codon
            in_gene = True
            start_pos = i

        elif in_gene and val < 0.05:
            # Found STOP codon
            gene_len = i - start_pos - 1  # Exclude START and STOP codons

            if 3 <= gene_len <= 20:
                # Normalize start position to genome coordinates
                normalized_start = start_pos % len(genome)

                # Only add if we haven't seen this gene position before
                if normalized_start not in gene_positions:
                    gene_positions.add(normalized_start)

                    # Extract gene sequence (excluding START and STOP)
                    gene_seq = []
                    for j in range(start_pos + 1, i):
                        idx = j % len(genome)
                        gene_seq.append(genome[idx])
                    genes.append(gene_seq)

            in_gene = False

    return genes


def interpret_gene(gene_seq):
    """
    Convert a gene sequence into a protein effect.

    Protein properties:
    - trait: Which phenotype trait this affects (0-3)
      Determined by content hash (sum of codons mod 4)
    - magnitude: Strength and direction of effect [-1, 1]
      Determined by mean codon value
    - regulatory: Whether this gene modifies expression threshold
      True if gene contains extreme values (< 0.1 or > 0.9)

    Args:
        gene_seq: List of codon values representing a gene

    Returns:
        Dict with keys: trait, magnitude, regulatory, length
        Or None if gene_seq is empty
    """
    if not gene_seq:
        return None

    # Hash the gene content to determine which trait it affects
    # Using sum mod 4 gives reasonable distribution
    content_hash = int(sum(gene_seq) * 1000) % 4  # Traits: 0=speed, 1=turn, 2=phototaxis, 3=efficiency

    # Magnitude: mean of gene values, normalized to [-1, 1]
    magnitude = np.mean(gene_seq) * 2 - 1

    # Regulatory genes contain extreme values
    # They can modify expression thresholds, creating epistatic effects
    is_regulatory = any(val < 0.1 or val > 0.9 for val in gene_seq)

    return {"trait": content_hash, "magnitude": magnitude, "regulatory": is_regulatory, "length": len(gene_seq)}


class Organism:
    """
    A simulated bacterium with an evolvable genome.

    Phenotype traits (0-3):
    - 0: speed - How fast the organism moves
    - 1: turn_rate - How sharply it can turn
    - 2: phototaxis - Attraction (+) or repulsion (-) to light
    - 3: efficiency - How well it converts resources to energy
    """

    def __init__(self, genome, pos):
        """
        Initialize organism with a genome and starting position.

        Args:
            genome: List of float values [0, 1] (variable length)
            pos: [x, y] position in the 120x120 world
        """
        self.id = str(uuid.uuid4())[:8]
        self.genome = list(genome)  # Make a copy, variable length
        self.pos = np.array(pos, dtype=np.float32)
        self.energy = 15.0
        self.age = 0
        self.alive = True
        self.fitness = 0.0

        # Phenotype: [speed, turn_rate, phototaxis, efficiency]
        self.phenotype = np.zeros(4, dtype=np.float32)

        # Express genes to determine phenotype
        self.express_genes()

    def express_genes(self, threshold=0.95):
        """
        Dynamic gene expression: extract genes and build phenotype.

        Two-pass expression:
        1. First pass: identify regulatory genes that modify threshold
        2. Second pass: express all genes with adjusted threshold

        This creates cascading regulatory networks where one gene
        can unlock or suppress multiple other genes.
        """
        # First pass: check for regulatory genes that modify expression
        genes = extract_genes(self.genome, threshold)

        for gene in genes:
            protein = interpret_gene(gene)
            if protein and protein["regulatory"] and protein["trait"] == 3:
                # Regulatory gene affecting trait 3 (efficiency)
                # modifies the expression threshold
                # Negative magnitude lowers threshold (activates more genes)
                # Positive magnitude raises threshold (suppresses genes)
                threshold = max(0.7, min(0.99, threshold - protein["magnitude"] * 0.1))

        # Second pass: express genes with adjusted threshold
        genes = extract_genes(self.genome, threshold)
        self.phenotype.fill(0)

        gene_count = 0
        for gene in genes:
            protein = interpret_gene(gene)
            if protein and not protein["regulatory"]:
                # Non-regulatory genes contribute to phenotype
                idx = protein["trait"]
                self.phenotype[idx] += protein["magnitude"]
                gene_count += 1

        # Store expression threshold for debugging
        self.expression_threshold = threshold
        self.active_gene_count = gene_count

        # Clamp raw phenotype values
        self.phenotype = np.clip(self.phenotype, -2, 2)

        # Scale phenotype values to biologically reasonable ranges
        # Speed: 0 to 3 pixels/tick
        self.phenotype[0] = (self.phenotype[0] + 2) / 4 * 3

        # Turn rate: 0 to 0.5 radians/tick
        self.phenotype[1] = (self.phenotype[1] + 2) / 4 * 0.5

        # Phototaxis: -1 (photophobic) to +1 (photophilic)
        self.phenotype[2] = np.tanh(self.phenotype[2])

        # Efficiency: 0 to 1 (resource conversion rate)
        self.phenotype[3] = (self.phenotype[3] + 2) / 4

    def move(self, light_gradient):
        """
        Move based on phenotype and environmental gradient.

        Movement strategy:
        - Sense light gradient (current vs ahead)
        - If phototaxis positive: move toward brighter areas
        - If phototaxis negative: move toward darker areas
        - Otherwise: random walk with turn rate bias

        Args:
            light_gradient: 2D numpy array of light intensities
        """
        speed, turn_rate, phototaxis, efficiency = self.phenotype

        # Clamp position to world bounds
        self.pos = np.clip(self.pos, 0, 119.9)

        x, y = int(self.pos[0]), int(self.pos[1])
        light_here = light_gradient[y, x]

        # Simple gradient sensing: look ahead in random direction
        angle = np.random.rand() * 2 * np.pi
        ahead_x = (x + int(np.cos(angle) * 3)) % 120
        ahead_y = (y + int(np.sin(angle) * 3)) % 120
        light_ahead = light_gradient[ahead_y, ahead_x]

        # Decide movement direction based on phototaxis
        if phototaxis > 0.2 and light_ahead > light_here:
            # Move toward light
            move_angle = angle
        elif phototaxis < -0.2 and light_ahead < light_here:
            # Move away from light
            move_angle = angle
        else:
            # Random walk
            move_angle = (np.random.rand() - 0.5) * 2 * np.pi * turn_rate

        # Update position
        self.pos[0] += np.cos(move_angle) * speed
        self.pos[1] += np.sin(move_angle) * speed

        # Wrap around (toroidal world)
        self.pos %= 120

    def metabolize(self, light, nutrient):
        """
        Convert environmental resources to energy.

        Energy budget:
        - Cost: Basal metabolism + movement cost (scales with speed)
        - Gain: Light × efficiency × nutrient availability

        Fitness is cumulative energy harvested over lifetime.

        Args:
            light: Light intensity at current position [0, 1]
            nutrient: Nutrient availability at current position [0, 1]
        """
        speed, turn_rate, phototaxis, efficiency = self.phenotype

        # Energy costs
        basal_cost = 0.02  # Just staying alive
        movement_cost = speed * 0.05
        total_cost = basal_cost + movement_cost

        # Energy gain from resources
        # Higher efficiency = better resource conversion
        gain = light * efficiency * nutrient * 0.5

        # Update energy and fitness
        self.energy += gain - total_cost
        self.fitness += gain  # Fitness = total energy harvested

        # Check survival
        if self.energy <= 0:
            self.alive = False

        self.age += 1

    def reproduce(self):
        """
        Asexual reproduction with mutations.

        Reproduction requirements:
        - Energy > 25 (cost of reproduction)
        - Energy is halved upon reproduction

        Mutation operators:
        - Point mutation: 2% per codon (random replacement)
        - Insertion: 0.5% per codon (adds random codon)
        - Deletion: 0.3% per codon (removes codon)
        - Duplication: 1% per reproduction (copies segment)

        Returns:
            Organism instance (child) or None if insufficient energy
        """
        if self.energy < 25:
            return None

        # Pay reproduction cost
        self.energy /= 2

        # Copy genome
        child_genome = self.genome.copy()

        # Apply mutations
        # Point mutations
        i = 0
        while i < len(child_genome):
            if np.random.rand() < 0.02:
                child_genome[i] = np.random.rand()
            i += 1

        # Insertions
        i = 0
        while i < len(child_genome):
            if np.random.rand() < 0.005:
                child_genome.insert(i, np.random.rand())
            i += 1

        # Deletions
        i = 0
        while i < len(child_genome):
            if np.random.rand() < 0.003 and len(child_genome) > 30:
                child_genome.pop(i)
                continue  # Don't increment i since we removed an element
            i += 1

        # Large-scale duplication (rare but powerful)
        if np.random.rand() < 0.01 and len(child_genome) < 300:
            # Duplicate a random segment of length 5-15
            if len(child_genome) >= 10:
                seg_len = np.random.randint(5, min(16, len(child_genome) // 2))
                start = np.random.randint(0, len(child_genome) - seg_len)
                segment = child_genome[start : start + seg_len]
                # Insert at random location
                insert_pos = np.random.randint(0, len(child_genome))
                child_genome[insert_pos:insert_pos] = segment

        # Trim if genome got too large
        if len(child_genome) > 400:
            child_genome = child_genome[:400]

        # Place child nearby
        child_pos = self.pos + np.random.randn(2) * 5
        child_pos = np.clip(child_pos, 0, 119)

        return Organism(child_genome, child_pos)

    def __repr__(self):
        """String representation for debugging"""
        return (
            f"Organism(id={self.id}, "
            f"energy={self.energy:.1f}, "
            f"fitness={self.fitness:.1f}, "
            f"genome_len={len(self.genome)}, "
            f"genes={self.active_gene_count})"
        )
