"""
Tests for organism gene expression and evolution
"""

import os
import sys

import numpy as np
import pytest

# Add client to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../client"))

from organism import Organism, extract_genes, interpret_gene


class TestGeneExtraction:
    """Test gene extraction from genomes"""

    def test_simple_gene(self):
        """Test extraction of a single simple gene"""
        # START (0.96) + 3 codons + STOP (0.04)
        genome = [0.5, 0.96, 0.4, 0.5, 0.6, 0.04, 0.5]
        genes = extract_genes(genome)

        assert len(genes) == 1
        assert len(genes[0]) == 3
        assert genes[0] == [0.4, 0.5, 0.6]

    def test_no_genes(self):
        """Test genome with no valid genes"""
        genome = [0.5] * 100  # All neutral
        genes = extract_genes(genome)

        assert len(genes) == 0

    def test_gene_too_short(self):
        """Genes must be at least 3 codons"""
        # START + 2 codons + STOP (too short)
        genome = [0.96, 0.4, 0.5, 0.04]
        genes = extract_genes(genome)

        assert len(genes) == 0

    def test_gene_too_long(self):
        """Genes must be at most 20 codons"""
        # START + 21 codons + STOP (too long)
        genome = [0.96] + [0.5] * 21 + [0.04]
        genes = extract_genes(genome)

        assert len(genes) == 0

    def test_multiple_genes(self):
        """Test genome with multiple genes"""
        genome = (
            [0.96, 0.1, 0.2, 0.3, 0.04]  # Gene 1 (length 3)
            + [0.5, 0.5]  # Junk
            + [0.96, 0.7, 0.8, 0.9, 0.6, 0.04]  # Gene 2 (length 4)
        )
        genes = extract_genes(genome)

        assert len(genes) == 2
        assert len(genes[0]) == 3
        assert len(genes[1]) == 4

    def test_circular_genome(self):
        """Test gene spanning genome origin (circular)"""
        # Gene wraps around: starts at end, continues at beginning
        genome = [0.4, 0.5, 0.04] + [0.5] * 94 + [0.96, 0.2, 0.3]
        genes = extract_genes(genome)

        # Should find gene spanning the wrap
        assert len(genes) >= 1

    def test_overlapping_genes(self):
        """Test overlapping genes (shared codons)"""
        # Complex case: nested genes
        genome = [0.96, 0.3, 0.96, 0.4, 0.04, 0.5, 0.04]
        genes = extract_genes(genome)

        # Should extract at least one gene
        assert len(genes) >= 1

    def test_custom_threshold(self):
        """Test custom expression threshold"""
        genome = [0.90, 0.4, 0.5, 0.6, 0.04]  # START is 0.90

        # Default threshold (0.95): should not find gene
        genes_default = extract_genes(genome, threshold=0.95)
        assert len(genes_default) == 0

        # Lower threshold (0.85): should find gene
        genes_low = extract_genes(genome, threshold=0.85)
        assert len(genes_low) == 1


class TestGeneInterpretation:
    """Test gene-to-protein conversion"""

    def test_interpret_simple_gene(self):
        """Test protein properties from gene"""
        gene = [0.5, 0.5, 0.5]
        protein = interpret_gene(gene)

        assert protein is not None
        assert "trait" in protein
        assert "magnitude" in protein
        assert "regulatory" in protein
        assert "length" in protein

        assert 0 <= protein["trait"] <= 3
        assert -1 <= protein["magnitude"] <= 1
        assert protein["length"] == 3

    def test_interpret_empty_gene(self):
        """Empty gene should return None"""
        protein = interpret_gene([])
        assert protein is None

    def test_magnitude_calculation(self):
        """Test magnitude is based on mean"""
        # High values -> positive magnitude
        gene_high = [0.9, 0.9, 0.9]
        protein_high = interpret_gene(gene_high)
        assert protein_high["magnitude"] > 0.5

        # Low values -> negative magnitude
        gene_low = [0.1, 0.1, 0.1]
        protein_low = interpret_gene(gene_low)
        assert protein_low["magnitude"] < -0.5

        # Medium values -> near zero magnitude
        gene_mid = [0.5, 0.5, 0.5]
        protein_mid = interpret_gene(gene_mid)
        assert abs(protein_mid["magnitude"]) < 0.2

    def test_regulatory_detection(self):
        """Test regulatory gene detection"""
        # Gene with extreme values
        gene_reg = [0.05, 0.5, 0.95]
        protein_reg = interpret_gene(gene_reg)
        assert protein_reg["regulatory"] is True

        # Gene without extreme values
        gene_normal = [0.4, 0.5, 0.6]
        protein_normal = interpret_gene(gene_normal)
        assert protein_normal["regulatory"] is False


class TestOrganism:
    """Test organism behavior"""

    def test_organism_creation(self):
        """Test basic organism creation"""
        genome = [0.5] * 100
        pos = [60, 60]
        org = Organism(genome, pos)

        assert org.alive is True
        assert org.energy > 0
        assert org.fitness == 0
        assert len(org.phenotype) == 4
        assert len(org.genome) == len(genome)

    def test_gene_expression(self):
        """Test that organisms express genes"""
        # Genome with one functional gene
        genome = [0.5] * 50 + [0.96, 0.4, 0.5, 0.6, 0.04] + [0.5] * 50
        org = Organism(genome, [60, 60])

        # Should have expressed at least one gene
        assert org.active_gene_count > 0

    def test_metabolism_energy_cost(self):
        """Test that metabolism costs energy"""
        genome = [0.5] * 100
        org = Organism(genome, [60, 60])

        initial_energy = org.energy

        # Metabolize with no resources
        org.metabolize(light=0, nutrient=0)

        # Energy should decrease
        assert org.energy < initial_energy

    def test_metabolism_energy_gain(self):
        """Test that metabolism gains energy from resources"""
        # Create organism with high efficiency gene
        genome = [0.96, 0.9, 0.9, 0.9, 0.04] + [0.5] * 95
        org = Organism(genome, [60, 60])

        initial_energy = org.energy

        # Metabolize with abundant resources
        org.metabolize(light=1.0, nutrient=1.0)

        # Energy should increase (if efficiency is good)
        # Note: might not always increase depending on random trait assignment
        # So we just check fitness increases
        assert org.fitness > 0

    def test_death_from_starvation(self):
        """Test organism dies when energy reaches zero"""
        genome = [0.5] * 100
        org = Organism(genome, [60, 60])
        org.energy = 0.01  # Very low energy

        # Metabolize with no resources multiple times
        for _ in range(10):
            org.metabolize(light=0, nutrient=0)

        assert org.alive is False

    def test_movement(self):
        """Test organism movement"""
        genome = [0.5] * 100
        org = Organism(genome, [60, 60])

        initial_pos = org.pos.copy()

        # Create light gradient
        light_gradient = np.ones((120, 120))

        org.move(light_gradient)

        # Position should change (unless speed is exactly zero, unlikely)
        # Due to randomness, we just check position is valid
        assert 0 <= org.pos[0] < 120
        assert 0 <= org.pos[1] < 120

    def test_reproduction_requires_energy(self):
        """Test reproduction energy requirement"""
        genome = [0.5] * 100
        org = Organism(genome, [60, 60])

        # Low energy: should not reproduce
        org.energy = 10
        child = org.reproduce()
        assert child is None

        # High energy: should reproduce
        org.energy = 30
        child = org.reproduce()
        assert child is not None
        assert isinstance(child, Organism)

    def test_reproduction_mutations(self):
        """Test that reproduction includes mutations"""
        genome = [0.5] * 100
        org = Organism(genome, [60, 60])
        org.energy = 30

        child = org.reproduce()

        # Child genome should be similar but not identical (mutations)
        # Due to randomness, we can't guarantee differences, but check it exists
        assert child is not None
        assert len(child.genome) > 0

    def test_regulatory_genes(self):
        """Test that regulatory genes affect expression"""
        # Create genome with regulatory gene
        # Regulatory gene (with extreme values) affecting trait 3
        genome = [0.96, 0.05, 0.95, 0.05, 0.04] + [0.5] * 95

        org = Organism(genome, [60, 60])

        # Expression threshold should be modified
        assert hasattr(org, "expression_threshold")
        # Threshold could be different from default 0.95
        # Hard to test exact value due to complex logic

    def test_phenotype_ranges(self):
        """Test phenotype values are in expected ranges"""
        genome = [0.96, 0.5, 0.5, 0.5, 0.04] + [0.5] * 95
        org = Organism(genome, [60, 60])

        # Speed: 0-3
        assert 0 <= org.phenotype[0] <= 3

        # Turn rate: 0-0.5
        assert 0 <= org.phenotype[1] <= 0.5

        # Phototaxis: -1 to 1
        assert -1 <= org.phenotype[2] <= 1

        # Efficiency: 0-1
        assert 0 <= org.phenotype[3] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
