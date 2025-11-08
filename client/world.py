"""
CodonSoup World - Simulation Environment

Implements:
- 120×120 toroidal petri dish
- Light gradient (bright at top, dark at bottom)
- Nutrient field with local depletion and regeneration
- Population dynamics (birth, death, movement)
"""

import numpy as np


class World:
    """
    The simulation environment where organisms live and evolve.

    Environment features:
    - Size: 120×120 grid (toroidal/wrapped edges)
    - Light: Vertical gradient (bright at y=0, dark at y=119)
    - Nutrients: Spatially distributed, locally depleted, slowly regenerating
    """

    def __init__(self, size=120):
        """
        Initialize the world with environmental gradients.

        Args:
            size: World dimensions (size × size grid)
        """
        self.size = size
        self.tick = 0

        # Create environmental fields
        self.light_map = self._create_light_gradient()
        self.nutrient_map = self._create_nutrient_field()

        # Population
        self.organisms = []

    def _create_light_gradient(self):
        """
        Create a vertical light gradient.

        Light is brightest at the top (y=0) and darkest at bottom (y=size-1).
        This creates selective pressure for phototaxis evolution.

        Returns:
            2D numpy array of light intensities [0, 1]
        """
        light = np.ones((self.size, self.size), dtype=np.float32)

        # Vertical gradient: decreases with depth
        for y in range(self.size):
            light[y, :] *= (1 - y / self.size) * 0.9 + 0.1  # Range: 0.1 to 1.0

        return light

    def _create_nutrient_field(self):
        """
        Create initial nutrient distribution.

        Nutrients are randomly distributed with some spatial structure.

        Returns:
            2D numpy array of nutrient levels [0, 1]
        """
        # Start with random base
        nutrients = np.random.rand(self.size, self.size).astype(np.float32) * 0.5 + 0.5

        # Add some spatial structure (smooth patches)
        # This creates resource heterogeneity
        for _ in range(5):
            # Gaussian blur effect
            nutrients = 0.8 * nutrients + 0.2 * np.roll(nutrients, 1, axis=0)
            nutrients = 0.8 * nutrients + 0.2 * np.roll(nutrients, 1, axis=1)

        return np.clip(nutrients, 0, 1)

    def add_organism(self, org):
        """
        Add an organism to the world.

        Args:
            org: Organism instance
        """
        self.organisms.append(org)

    def update(self):
        """
        Run one simulation tick.

        Update sequence:
        1. Regenerate nutrients (slowly)
        2. Update light field (occasional flicker)
        3. Update each organism (move, metabolize, reproduce)
        4. Remove dead organisms
        5. Handle population dynamics
        """
        self.tick += 1

        # Slowly regenerate nutrients everywhere
        self.nutrient_map = np.clip(self.nutrient_map + 0.002, 0, 1)

        # Occasional light flicker (simulates changing conditions)
        if np.random.rand() < 0.05:
            flicker = np.random.randn(self.size, self.size).astype(np.float32) * 0.02
            self.light_map = np.clip(self.light_map + flicker, 0, 1)

        # Process organisms
        new_organisms = []

        for org in self.organisms:
            if not org.alive:
                continue

            # Get local resources
            x, y = int(org.pos[0]), int(org.pos[1])
            x, y = x % self.size, y % self.size  # Ensure in bounds

            light = self.light_map[y, x]
            nutrient = self.nutrient_map[y, x]

            # Organism actions
            org.move(self.light_map)
            org.metabolize(light, nutrient)

            # Still alive after metabolism?
            if org.alive:
                new_organisms.append(org)

                # Try to reproduce
                child = org.reproduce()
                if child:
                    new_organisms.append(child)

                    # Deplete nutrients locally when reproducing
                    self.nutrient_map[y, x] = max(0, self.nutrient_map[y, x] - 0.15)

        self.organisms = new_organisms

    def get_fittest(self):
        """
        Find the organism with highest fitness.

        Returns:
            Organism with max fitness, or None if population is empty
        """
        if not self.organisms:
            return None
        return max(self.organisms, key=lambda o: o.fitness)

    def get_statistics(self):
        """
        Compute population statistics.

        Returns:
            Dict with population metrics
        """
        if not self.organisms:
            return {
                "population": 0,
                "avg_fitness": 0,
                "avg_energy": 0,
                "avg_genome_length": 0,
                "avg_active_genes": 0,
                "max_fitness": 0,
            }

        fitnesses = [o.fitness for o in self.organisms]
        energies = [o.energy for o in self.organisms]
        genome_lengths = [len(o.genome) for o in self.organisms]
        active_genes = [o.active_gene_count for o in self.organisms]

        return {
            "population": len(self.organisms),
            "avg_fitness": np.mean(fitnesses),
            "avg_energy": np.mean(energies),
            "avg_genome_length": np.mean(genome_lengths),
            "avg_active_genes": np.mean(active_genes),
            "max_fitness": np.max(fitnesses),
            "tick": self.tick,
        }

    def __repr__(self):
        """String representation for debugging"""
        stats = self.get_statistics()
        return f"World(tick={self.tick}, " f"population={stats['population']}, " f"avg_fitness={stats['avg_fitness']:.2f})"
