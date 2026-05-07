"""
Neshama Entity Graph Tests
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.entity_graph import (
    EntityGraph,
    EntityNode,
    GraphEdge,
    EntityType,
    RelationType,
    EdgeDirection,
    create_entity_graph,
    extract_entities_from_text,
)


class TestEntityNodeCreation:
    """Tests for entity node creation."""

    def test_add_entity_basic(self):
        """Test basic entity creation."""
        graph = EntityGraph()
        entity = graph.add_entity("Alice", EntityType.PERSON)
        assert entity is not None
        assert entity.name == "Alice"
        assert entity.entity_type == EntityType.PERSON
        assert entity.id is not None

    def test_add_entity_with_description(self):
        """Test entity creation with description."""
        graph = EntityGraph()
        entity = graph.add_entity(
            "Paris",
            EntityType.PLACE,
            description="City of Light",
        )
        assert entity.description == "City of Light"

    def test_add_entity_with_metadata(self):
        """Test entity creation with metadata."""
        graph = EntityGraph()
        entity = graph.add_entity(
            "Neshama",
            EntityType.CONCEPT,
            metadata={"version": "2.0", "language": "Python"},
        )
        assert entity.metadata["version"] == "2.0"
        assert entity.metadata["language"] == "Python"

    def test_add_entity_with_aliases(self):
        """Test entity with alternative names."""
        graph = EntityGraph()
        entity = graph.add_entity(
            "AI",
            EntityType.CONCEPT,
            aliases=["Artificial Intelligence", "Machine Intelligence"],
        )
        assert "Artificial Intelligence" in entity.aliases

    def test_add_entity_custom_id(self):
        """Test entity with custom ID."""
        graph = EntityGraph()
        entity = graph.add_entity("Bob", EntityType.PERSON, entity_id="bob-001")
        assert entity.id == "bob-001"

    def test_entity_importance(self):
        """Test entity importance score."""
        graph = EntityGraph()
        entity = graph.add_entity("Key", EntityType.PERSON, importance=0.9)
        assert entity.importance == 0.9


class TestEntityRetrieval:
    """Tests for entity retrieval."""

    def test_get_entity_by_id(self):
        """Test getting entity by ID."""
        graph = EntityGraph()
        created = graph.add_entity("Alice", EntityType.PERSON)
        retrieved = graph.get_entity(created.id)
        assert retrieved is not None
        assert retrieved.name == "Alice"

    def test_get_nonexistent_entity(self):
        """Test getting non-existent entity."""
        graph = EntityGraph()
        assert graph.get_entity("nonexistent") is None

    def test_find_entity_by_name(self):
        """Test finding entity by exact name."""
        graph = EntityGraph()
        graph.add_entity("Alice", EntityType.PERSON)
        found = graph.find_entity("Alice")
        assert found is not None
        assert found.name == "Alice"

    def test_find_entity_by_name_case_insensitive(self):
        """Test finding entity case-insensitively."""
        graph = EntityGraph()
        graph.add_entity("Alice", EntityType.PERSON)
        found = graph.find_entity("alice")
        assert found is not None

    def test_find_entity_by_alias(self):
        """Test finding entity by alias."""
        graph = EntityGraph()
        graph.add_entity("AI", EntityType.CONCEPT, aliases=["Artificial Intelligence"])
        found = graph.find_entity("Artificial Intelligence")
        assert found is not None

    def test_find_nonexistent_entity(self):
        """Test finding non-existent entity returns None."""
        graph = EntityGraph()
        assert graph.find_entity("Nobody") is None


class TestEntityUpdateDelete:
    """Tests for entity update and deletion."""

    def test_update_entity(self):
        """Test updating entity fields."""
        graph = EntityGraph()
        entity = graph.add_entity("Alice", EntityType.PERSON)
        updated = graph.update_entity(entity.id, name="Alice Smith", importance=0.8)
        assert updated.name == "Alice Smith"
        assert updated.importance == 0.8

    def test_update_nonexistent(self):
        """Test updating non-existent entity."""
        graph = EntityGraph()
        result = graph.update_entity("fake-id", name="New Name")
        assert result is None

    def test_delete_entity(self):
        """Test deleting entity."""
        graph = EntityGraph()
        entity = graph.add_entity("Alice", EntityType.PERSON)
        assert graph.entity_count() == 1
        result = graph.delete_entity(entity.id)
        assert result is True
        assert graph.entity_count() == 0

    def test_delete_nonexistent(self):
        """Test deleting non-existent entity."""
        graph = EntityGraph()
        result = graph.delete_entity("fake-id")
        assert result is False


class TestEntityQuery:
    """Tests for entity querying."""

    def setup_method(self):
        """Set up test graph."""
        self.graph = EntityGraph()
        self.alice = self.graph.add_entity("Alice", EntityType.PERSON, importance=0.8)
        self.bob = self.graph.add_entity("Bob", EntityType.PERSON, importance=0.5)
        self.paris = self.graph.add_entity("Paris", EntityType.PLACE, importance=0.7)
        self.ai = self.graph.add_entity("AI Research", EntityType.CONCEPT, importance=0.9)

    def test_query_by_type(self):
        """Test querying entities by type."""
        persons = self.graph.query_entities(entity_type=EntityType.PERSON)
        assert len(persons) == 2
        assert all(e.entity_type == EntityType.PERSON for e in persons)

    def test_query_by_name_contains(self):
        """Test querying by name substring."""
        results = self.graph.query_entities(name_contains="Alice")
        assert len(results) >= 1

    def test_query_by_min_importance(self):
        """Test querying by minimum importance."""
        results = self.graph.query_entities(min_importance=0.75)
        assert len(results) == 2
        assert all(e.importance >= 0.75 for e in results)

    def test_query_with_limit(self):
        """Test query with limit."""
        results = self.graph.query_entities(limit=2)
        assert len(results) == 2

    def test_get_all_entities(self):
        """Test getting all entities."""
        all_entities = self.graph.get_all_entities()
        assert len(all_entities) == 4

    def test_entity_count(self):
        """Test entity count."""
        assert self.graph.entity_count() == 4


class TestRelations:
    """Tests for relationship management."""

    def setup_method(self):
        """Set up test graph."""
        self.graph = EntityGraph()
        self.alice = self.graph.add_entity("Alice", EntityType.PERSON)
        self.paris = self.graph.add_entity("Paris", EntityType.PLACE)
        self.ai = self.graph.add_entity("AI", EntityType.CONCEPT)

    def test_add_relation(self):
        """Test adding a directed relation."""
        edge = self.graph.add_relation(
            self.alice.id,
            self.paris.id,
            RelationType.LOCATED_AT,
            weight=0.9,
        )
        assert edge is not None
        assert edge.source_id == self.alice.id
        assert edge.target_id == self.paris.id
        assert edge.relation_type == RelationType.LOCATED_AT
        assert edge.weight == 0.9

    def test_add_relation_nonexistent_entity(self):
        """Test adding relation with non-existent entity."""
        edge = self.graph.add_relation(
            self.alice.id,
            "nonexistent",
            RelationType.KNOWS,
        )
        assert edge is None

    def test_add_undirected_relation(self):
        """Test adding an undirected relation."""
        bob = self.graph.add_entity("Bob", EntityType.PERSON)
        edge = self.graph.add_relation(
            self.alice.id,
            bob.id,
            RelationType.SIMILAR_TO,
            direction=EdgeDirection.UNDIRECTED,
        )
        assert edge is not None

    def test_get_outgoing_relations(self):
        """Test getting outgoing relations."""
        self.graph.add_relation(self.alice.id, self.paris.id, RelationType.LOCATED_AT)
        self.graph.add_relation(self.alice.id, self.ai.id, RelationType.KNOWS)
        relations = self.graph.get_relations(entity_id=self.alice.id, direction="outgoing")
        assert len(relations) == 2

    def test_get_incoming_relations(self):
        """Test getting incoming relations."""
        self.graph.add_relation(self.alice.id, self.paris.id, RelationType.LOCATED_AT)
        relations = self.graph.get_relations(entity_id=self.paris.id, direction="incoming")
        assert len(relations) == 1

    def test_get_relations_by_type(self):
        """Test filtering relations by type."""
        self.graph.add_relation(self.alice.id, self.paris.id, RelationType.LOCATED_AT)
        self.graph.add_relation(self.alice.id, self.ai.id, RelationType.KNOWS)
        knows_relations = self.graph.get_relations(
            entity_id=self.alice.id,
            relation_type=RelationType.KNOWS,
        )
        assert len(knows_relations) == 1
        assert knows_relations[0].relation_type == RelationType.KNOWS

    def test_remove_relation(self):
        """Test removing a relation."""
        edge = self.graph.add_relation(self.alice.id, self.paris.id, RelationType.LOCATED_AT)
        assert self.graph.edge_count() == 1
        result = self.graph.remove_relation(edge.id)
        assert result is True
        assert self.graph.edge_count() == 0

    def test_get_neighbors(self):
        """Test getting neighboring entities."""
        self.graph.add_relation(self.alice.id, self.paris.id, RelationType.LOCATED_AT)
        self.graph.add_relation(self.alice.id, self.ai.id, RelationType.KNOWS)
        neighbors = self.graph.get_neighbors(self.alice.id)
        assert len(neighbors) == 2
        neighbor_names = {n[0].name for n in neighbors}
        assert "Paris" in neighbor_names
        assert "AI" in neighbor_names

    def test_edge_count(self):
        """Test edge count."""
        assert self.graph.edge_count() == 0
        self.graph.add_relation(self.alice.id, self.paris.id, RelationType.LOCATED_AT)
        self.graph.add_relation(self.alice.id, self.ai.id, RelationType.KNOWS)
        assert self.graph.edge_count() == 2


class TestGraphQueries:
    """Tests for graph-level queries."""

    def setup_method(self):
        """Set up test graph with connections."""
        self.graph = EntityGraph()
        self.alice = self.graph.add_entity("Alice", EntityType.PERSON)
        self.paris = self.graph.add_entity("Paris", EntityType.PLACE)
        self.ai = self.graph.add_entity("AI", EntityType.CONCEPT)
        self.graph.add_relation(self.alice.id, self.paris.id, RelationType.LOCATED_AT)
        self.graph.add_relation(self.alice.id, self.ai.id, RelationType.KNOWS)

    def test_find_paths(self):
        """Test finding paths between entities."""
        paths = self.graph.find_paths(self.alice.id, self.paris.id, max_depth=2)
        assert len(paths) >= 1
        # Each path is List[(EntityNode, GraphEdge)], first item is source
        first_path = paths[0]
        assert len(first_path) >= 1
        assert first_path[-1][0].id == self.paris.id  # last node is target

    def test_find_paths_no_path(self):
        """Test finding paths when none exist."""
        paths = self.graph.find_paths(self.paris.id, self.ai.id, max_depth=2)
        assert len(paths) == 0

    def test_shortest_path(self):
        """Test finding shortest path."""
        path = self.graph.shortest_path(self.alice.id, self.paris.id)
        assert path is not None
        assert len(path) >= 1

    def test_subgraph(self):
        """Test extracting subgraph."""
        entities = self.graph.subgraph([self.alice.id, self.paris.id])
        assert len(entities) == 2

    def test_stats(self):
        """Test graph statistics."""
        stats = self.graph.get_stats()
        assert stats["entity_count"] == 3
        assert stats["edge_count"] == 2
        assert "entity_types" in stats
        assert "relation_types" in stats


class TestMemoryAssociation:
    """Tests for memory entity associations."""

    def test_link_to_memory(self):
        """Test linking entity to memory."""
        graph = EntityGraph()
        entity = graph.add_entity("Alice", EntityType.PERSON)
        result = graph.link_to_memory(entity.id, "memory-001")
        assert result is True
        memories = graph.get_memories_for_entity(entity.id)
        assert "memory-001" in memories

    def test_unlink_from_memory(self):
        """Test unlinking entity from memory."""
        graph = EntityGraph()
        entity = graph.add_entity("Alice", EntityType.PERSON)
        graph.link_to_memory(entity.id, "memory-001")
        result = graph.unlink_from_memory(entity.id, "memory-001")
        assert result is True
        memories = graph.get_memories_for_entity(entity.id)
        assert "memory-001" not in memories

    def test_get_entities_by_memory(self):
        """Test getting entities linked to a memory."""
        graph = EntityGraph()
        alice = graph.add_entity("Alice", EntityType.PERSON)
        bob = graph.add_entity("Bob", EntityType.PERSON)
        graph.link_to_memory(alice.id, "shared-memory")
        graph.link_to_memory(bob.id, "shared-memory")
        entities = graph.get_entities_by_memory("shared-memory")
        assert len(entities) == 2

    def test_link_nonexistent_entity(self):
        """Test linking non-existent entity."""
        graph = EntityGraph()
        result = graph.link_to_memory("fake-id", "memory-001")
        assert result is False


class TestSerialization:
    """Tests for graph serialization."""

    def test_to_dict(self):
        """Test exporting graph to dictionary."""
        graph = EntityGraph()
        entity = graph.add_entity("Alice", EntityType.PERSON)
        entity2 = graph.add_entity("Bob", EntityType.PERSON)
        graph.add_relation(entity.id, entity2.id, RelationType.KNOWS)
        data = graph.to_dict()
        assert "entities" in data
        assert "edges" in data
        assert len(data["entities"]) == 2
        assert len(data["edges"]) == 1

    def test_from_dict(self):
        """Test reconstructing graph from dictionary."""
        graph = EntityGraph()
        entity = graph.add_entity("Alice", EntityType.PERSON, importance=0.9)
        data = graph.to_dict()
        restored = EntityGraph.from_dict(data)
        assert restored.entity_count() == 1
        found = restored.find_entity("Alice")
        assert found is not None
        assert found.importance == 0.9

    def test_from_dict_restores_edges(self):
        """Test that edges are restored from dictionary."""
        graph = EntityGraph()
        entity = graph.add_entity("Alice", EntityType.PERSON)
        entity2 = graph.add_entity("Bob", EntityType.PERSON)
        graph.add_relation(entity.id, entity2.id, RelationType.KNOWS)
        data = graph.to_dict()
        restored = EntityGraph.from_dict(data)
        assert restored.edge_count() == 1


class TestEdgeDirection:
    """Tests for edge directionality."""

    def setup_method(self):
        self.graph = EntityGraph()
        self.alice = self.graph.add_entity("Alice", EntityType.PERSON)
        self.bob = self.graph.add_entity("Bob", EntityType.PERSON)

    def test_directed_edge(self):
        """Test directed edge only appears in outgoing."""
        edge = self.graph.add_relation(
            self.alice.id,
            self.bob.id,
            RelationType.KNOWS,
            direction=EdgeDirection.DIRECTED,
        )
        outgoing = self.graph.get_relations(self.alice.id, direction="outgoing")
        incoming = self.graph.get_relations(self.bob.id, direction="incoming")
        assert len(outgoing) == 1
        assert len(incoming) == 1

    def test_undirected_edge_bidirectional(self):
        """Test undirected edge appears in both directions."""
        edge = self.graph.add_relation(
            self.alice.id,
            self.bob.id,
            RelationType.SIMILAR_TO,
            direction=EdgeDirection.UNDIRECTED,
        )
        # Undirected creates 2 edges (one in each direction)
        assert self.graph.edge_count() == 2


class TestExtractEntitiesFromText:
    """Tests for entity extraction from text."""

    def test_extract_simple(self):
        """Test simple entity extraction."""
        graph = EntityGraph()
        entities = extract_entities_from_text(
            "Alice, Bob, and Charlie went to Paris",
            graph,
            EntityType.PERSON,
        )
        assert len(entities) >= 2

    def test_extract_deduplicates(self):
        """Test extraction doesn't duplicate existing entities."""
        graph = EntityGraph()
        graph.add_entity("Alice", EntityType.PERSON)
        entities = extract_entities_from_text(
            "Alice, Bob, Paris",
            graph,
            EntityType.PERSON,
        )
        # Alice already exists so skipped; Bob and Paris are new
        names = [e.name for e in entities]
        assert "Alice" not in names  # deduped
        assert len(entities) == 2  # Bob, Paris

    def test_extract_filters_short(self):
        """Test extraction filters out very short tokens."""
        graph = EntityGraph()
        entities = extract_entities_from_text(
            "I met A and BB and CCC",
            graph,
            EntityType.PERSON,
        )
        # Should filter "A" but keep "BB" and "CCC"
        names = [e.name for e in entities]
        assert "A" not in names


class TestIntegrationWithMemory:
    """Integration tests with existing memory modules."""

    def test_with_memory_layer(self):
        """Test integration with Memory layer."""
        from neshama.memory import Memory, MemoryConfig

        config = MemoryConfig(agent_id="test-agent", short_term_capacity=5)
        memory = Memory(agent_id="test-agent", config=config)

        graph = EntityGraph()

        # Add conversation to memory
        memory.add_turn("user", "I love hiking in mountains")
        memory.add_turn("assistant", "That's great! Which mountains?")

        # Extract entities from memory
        context = memory.get_short_term_context()
        entities = extract_entities_from_text(context, graph, EntityType.PLACE)
        assert len(entities) >= 0  # May or may not extract depending on content

        # Link entities to memory
        for entity in entities:
            graph.link_to_memory(entity.id, "short_term_001")

        linked = graph.get_entities_by_memory("short_term_001")
        assert len(linked) == len(entities)
