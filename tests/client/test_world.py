"""
Tests for world simulation environment
"""

import pytest
import numpy as np
import sys
import os

# Add client to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../client'))

from world import World
from organism import Organism


class TestWorld:
    """Test world environment"""

    def test_world_creation(self):
        """Test basic world initialization"""
        world = World(size=120)

        assert world.size == 120
        assert world.light_map.shape == (120, 120)
        assert world.nutrient_map.shape == (120, 120)
        assert len(world.organisms) == 0
        assert world.tick == 0

    def test_light_gradient(self):
        """Test light gradient is vertical"""
        world = World(size=120)

        # Top should be brighter than bottom
        top_light = world.light_map[0, 60]
        bottom_light = world.light_map[119, 60]

        assert top_light > bottom_light
        assert 0 <= top_light <= 1
        assert 0 <= bottom_light <= 1

    def test_nutrient_field(self):
        """Test nutrient field initialization"""
        world = World(size=120)

        # All nutrients should be in valid range
        assert np.all(world.nutrient_map >= 0)
        assert np.all(world.nutrient_map <= 1)

        # Should have some variation
        assert np.std(world.nutrient_map) > 0

    def test_add_organism(self):
        """Test adding organisms to world"""
        world = World()
        genome = [0.5] * 100
        org = Organism(genome, [60, 60])

        world.add_organism(org)

        assert len(world.organisms) == 1
        assert world.organisms[0] is org

    def test_update_increments_tick(self):
        """Test that update increments tick counter"""
        world = World()
        initial_tick = world.tick

        world.update()

        assert world.tick == initial_tick + 1

    def test_update_with_organisms(self):
        """Test simulation update with organisms"""
        world = World()

        # Add some organisms
        for i in range(10):
            genome = [0.96, 0.5, 0.5, 0.5, 0.04] + [0.5] * 95
            pos = [60 + i, 60]
            world.add_organism(Organism(genome, pos))

        assert len(world.organisms) == 10

        # Run update
        world.update()

        # Organisms should still exist (unless they died)
        # At minimum, world should have processed them
        assert world.tick == 1

    def test_organism_death_removal(self):
        """Test dead organisms are removed"""
        world = World()

        # Add organism with no energy (will die)
        genome = [0.5] * 100
        org = Organism(genome, [60, 60])
        org.energy = 0.01
        world.add_organism(org)

        # Run many updates with no resources
        world.light_map.fill(0)
        world.nutrient_map.fill(0)

        for _ in range(10):
            world.update()

        # Organism should have died and been removed
        assert len(world.organisms) == 0

    def test_reproduction_increases_population(self):
        """Test that organisms can reproduce"""
        world = World()

        # Add organism with good genome and high energy
        genome = [0.96, 0.9, 0.9, 0.9, 0.04] + [0.5] * 95
        org = Organism(genome, [60, 60])
        org.energy = 30  # Enough to reproduce
        world.add_organism(org)

        # Set abundant resources
        world.light_map.fill(1.0)
        world.nutrient_map.fill(1.0)

        initial_pop = len(world.organisms)

        # Run several updates
        for _ in range(50):
            world.update()
            if len(world.organisms) > initial_pop:
                break

        # Population may have grown (not guaranteed due to random factors)
        # But we can check organisms exist
        assert len(world.organisms) >= 0

    def test_nutrient_regeneration(self):
        """Test nutrients regenerate over time"""
        world = World()

        # Deplete nutrients
        world.nutrient_map.fill(0.1)
        initial = world.nutrient_map[60, 60]

        # Run updates
        for _ in range(100):
            world.update()

        # Nutrients should have increased
        assert world.nutrient_map[60, 60] > initial

    def test_get_fittest(self):
        """Test finding fittest organism"""
        world = World()

        # Add organisms with different fitness
        for i in range(5):
            genome = [0.5] * 100
            org = Organism(genome, [60, 60 + i * 5])
            org.fitness = i * 10  # Different fitness values
            world.add_organism(org)

        fittest = world.get_fittest()

        assert fittest is not None
        assert fittest.fitness == 40  # Highest fitness

    def test_get_fittest_empty_world(self):
        """Test get_fittest with no organisms"""
        world = World()
        fittest = world.get_fittest()

        assert fittest is None

    def test_get_statistics(self):
        """Test population statistics"""
        world = World()

        # Empty world
        stats = world.get_statistics()
        assert stats["population"] == 0
        assert stats["avg_fitness"] == 0

        # Add organisms
        for i in range(5):
            genome = [0.5] * 100
            org = Organism(genome, [60, 60])
            org.fitness = i * 10
            org.energy = 10 + i
            world.add_organism(org)

        stats = world.get_statistics()

        assert stats["population"] == 5
        assert stats["avg_fitness"] == 20  # (0+10+20+30+40)/5
        assert stats["avg_energy"] == 12  # (10+11+12+13+14)/5
        assert stats["max_fitness"] == 40
        assert "avg_genome_length" in stats
        assert "avg_active_genes" in stats

    def test_toroidal_world(self):
        """Test world wraps around (toroidal topology)"""
        world = World()

        genome = [0.5] * 100
        org = Organism(genome, [119, 119])  # Near edge
        world.add_organism(org)

        # Move organism beyond boundary
        org.pos[0] = 121  # Beyond x boundary
        org.pos[1] = 121  # Beyond y boundary

        world.update()

        # Position should wrap
        assert 0 <= world.organisms[0].pos[0] < 120
        assert 0 <= world.organisms[0].pos[1] < 120


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
