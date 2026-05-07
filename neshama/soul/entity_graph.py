# Soul Layer - Entity Graph Module
"""
Entity Knowledge Graph

Features:
- Entity nodes: person, place, concept, event, object, etc.
- Relationship edges: directed/undirected with weight and type
- Graph queries: by entity, relation type, path depth
- Memory associations: bidirectional link between entities and memory entries

Design:
The graph is a simple in-memory adjacency-list implementation.
Entities are stored in a dict keyed by entity_id.
Edges are stored per entity with references to target entity IDs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from enum import Enum
import threading
import uuid


class EntityType(Enum):
    """Types of entity nodes."""
    PERSON = "person"
    PLACE = "place"
    CONCEPT = "concept"
    EVENT = "event"
    OBJECT = "object"
    ORGANIZATION = "organization"
    ABSTRACT = "abstract"  # emotions, beliefs, etc.
    CUSTOM = "custom"


class RelationType(Enum):
    """Types of relationship edges."""
    KNOWS = "knows"
    LOCATED_AT = "located_at"
    PART_OF = "part_of"
    CAUSED = "caused"
    RELATED_TO = "related_to"
    LIKES = "likes"
    DISLIKES = "dislikes"
    CAUSE_OF = "cause_of"
    BEFORE = "before"
    AFTER = "after"
    SIMILAR_TO = "similar_to"
    OWNED_BY = "owned_by"
    CREATED_BY = "created_by"
    MEMBER_OF = "member_of"
    CUSTOM = "custom"


class EdgeDirection(Enum):
    """Edge directionality."""
    DIRECTED = "directed"    # A -> B
    UNDIRECTED = "undirected"  # A <-> B


@dataclass
class EntityNode:
    """A node in the entity graph."""
    id: str
    name: str
    entity_type: EntityType
    description: str = ""
    aliases: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5  # 0-1, affects memory retention
    memory_ids: List[str] = field(default_factory=list)  # linked memory entry IDs
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "description": self.description,
            "aliases": self.aliases,
            "metadata": self.metadata,
            "importance": self.importance,
            "memory_ids": self.memory_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "EntityNode":
        et = data.get("entity_type", "custom")
        if isinstance(et, str):
            try:
                et = EntityType(et)
            except ValueError:
                et = EntityType.CUSTOM
        return cls(
            id=data["id"],
            name=data["name"],
            entity_type=et,
            description=data.get("description", ""),
            aliases=data.get("aliases", []),
            metadata=data.get("metadata", {}),
            importance=data.get("importance", 0.5),
            memory_ids=data.get("memory_ids", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            access_count=data.get("access_count", 0),
        )


@dataclass
class GraphEdge:
    """An edge (relationship) in the entity graph."""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    direction: EdgeDirection = EdgeDirection.DIRECTED
    weight: float = 1.0  # 0-1
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # certainty of this relationship
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "direction": self.direction.value,
            "weight": self.weight,
            "description": self.description,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "GraphEdge":
        rt = data.get("relation_type", "related_to")
        if isinstance(rt, str):
            try:
                rt = RelationType(rt)
            except ValueError:
                rt = RelationType.CUSTOM
        d = data.get("direction", "directed")
        try:
            d = EdgeDirection(d)
        except ValueError:
            d = EdgeDirection.DIRECTED
        return cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=rt,
            direction=d,
            weight=data.get("weight", 1.0),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
            confidence=data.get("confidence", 1.0),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


class EntityGraph:
    """
    Entity Knowledge Graph.

    Manages entity nodes and their relationships with weighted edges.

    Example:
        >>> graph = EntityGraph()

        >>> # Add entities
        >>> alice = graph.add_entity("Alice", EntityType.PERSON, description="AI researcher")
        >>> paris = graph.add_entity("Paris", EntityType.PLACE, description="City of light")
        >>> ai = graph.add_entity("Artificial Intelligence", EntityType.CONCEPT)

        >>> # Add relationships
        >>> graph.add_relation(alice.id, paris.id, RelationType.LOCATED_AT, weight=0.9)
        >>> graph.add_relation(alice.id, ai.id, RelationType.KNOWS, weight=0.8)

        >>> # Query
        >>> entities = graph.query_entities(entity_type=EntityType.PERSON)
        >>> alice_relations = graph.get_relations(entity_id=alice.id)
        >>> paths = graph.find_paths(alice.id, ai.id, max_depth=2)
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize EntityGraph.

        Args:
            storage_path: Optional path for JSON persistence.
        """
        self._entities: Dict[str, EntityNode] = {}
        self._edges: Dict[str, GraphEdge] = {}
        self._outgoing: Dict[str, List[str]] = {}  # entity_id -> [edge_ids]
        self._incoming: Dict[str, List[str]] = {}  # entity_id -> [edge_ids]
        self._lock = threading.RLock()
        self._storage_path = storage_path

    # ── Entity Operations ─────────────────────────────────────────────────────

    def add_entity(
        self,
        name: str,
        entity_type: EntityType,
        description: str = "",
        entity_id: Optional[str] = None,
        importance: float = 0.5,
        metadata: Optional[Dict] = None,
        aliases: Optional[List[str]] = None,
    ) -> EntityNode:
        """
        Add an entity to the graph.

        Args:
            name: Entity name/label
            entity_type: Type of entity
            description: Human-readable description
            entity_id: Optional custom ID (auto-generated if None)
            importance: 0-1 importance score
            metadata: Extra key-value metadata
            aliases: Alternative names for lookup

        Returns:
            The created EntityNode
        """
        node = EntityNode(
            id=entity_id or str(uuid.uuid4()),
            name=name,
            entity_type=entity_type,
            description=description,
            importance=importance,
            metadata=metadata or {},
            aliases=aliases or [],
        )
        with self._lock:
            self._entities[node.id] = node
            self._outgoing.setdefault(node.id, [])
            self._incoming.setdefault(node.id, [])
        return node

    def get_entity(self, entity_id: str) -> Optional[EntityNode]:
        """Get an entity by ID."""
        with self._lock:
            return self._entities.get(entity_id)

    def find_entity(self, name: str) -> Optional[EntityNode]:
        """Find an entity by exact name (case-insensitive) or alias."""
        name_lower = name.lower()
        with self._lock:
            for entity in self._entities.values():
                if entity.name.lower() == name_lower:
                    return entity
                if name_lower in [a.lower() for a in entity.aliases]:
                    return entity
        return None

    def update_entity(self, entity_id: str, **kwargs) -> Optional[EntityNode]:
        """Update entity fields. Returns None if not found."""
        with self._lock:
            entity = self._entities.get(entity_id)
            if not entity:
                return None
            for key, value in kwargs.items():
                if hasattr(entity, key) and key not in ("id", "created_at"):
                    setattr(entity, key, value)
            entity.updated_at = datetime.now().isoformat()
            return entity

    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and all its edges."""
        with self._lock:
            if entity_id not in self._entities:
                return False
            # Remove all connected edges
            for edge_id in list(self._outgoing.get(entity_id, [])):
                self._remove_edge_unsafe(edge_id)
            for edge_id in list(self._incoming.get(entity_id, [])):
                self._remove_edge_unsafe(edge_id)
            del self._entities[entity_id]
            return True

    def query_entities(
        self,
        entity_type: Optional[EntityType] = None,
        name_contains: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 100,
    ) -> List[EntityNode]:
        """Query entities by type, name, and importance."""
        results = []
        with self._lock:
            for entity in self._entities.values():
                if entity_type and entity.entity_type != entity_type:
                    continue
                if min_importance and entity.importance < min_importance:
                    continue
                if name_contains:
                    lc = name_contains.lower()
                    if lc not in entity.name.lower() and \
                       lc not in [a.lower() for a in entity.aliases]:
                        continue
                results.append(entity)
                if len(results) >= limit:
                    break
        return results

    def get_all_entities(self) -> List[EntityNode]:
        """Get all entities."""
        with self._lock:
            return list(self._entities.values())

    def entity_count(self) -> int:
        """Count total entities."""
        with self._lock:
            return len(self._entities)

    # ── Relation Operations ───────────────────────────────────────────────────

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        edge_id: Optional[str] = None,
        weight: float = 1.0,
        direction: EdgeDirection = EdgeDirection.DIRECTED,
        description: str = "",
        metadata: Optional[Dict] = None,
    ) -> Optional[GraphEdge]:
        """Add a relationship between two entities."""
        with self._lock:
            if source_id not in self._entities or target_id not in self._entities:
                return None

            edge = GraphEdge(
                id=edge_id or str(uuid.uuid4()),
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type,
                direction=direction,
                weight=weight,
                description=description,
                metadata=metadata or {},
            )

            self._edges[edge.id] = edge
            self._outgoing.setdefault(source_id, []).append(edge.id)
            self._incoming.setdefault(target_id, []).append(edge.id)

            # For undirected, also add reverse
            if direction == EdgeDirection.UNDIRECTED:
                rev_edge = GraphEdge(
                    id=str(uuid.uuid4()),
                    source_id=target_id,
                    target_id=source_id,
                    relation_type=relation_type,
                    direction=EdgeDirection.UNDIRECTED,
                    weight=weight,
                    description=description,
                    metadata=metadata or {},
                )
                self._edges[rev_edge.id] = rev_edge
                self._outgoing.setdefault(target_id, []).append(rev_edge.id)
                self._incoming.setdefault(source_id, []).append(rev_edge.id)

            return edge

    def _remove_edge_unsafe(self, edge_id: str) -> None:
        """Remove an edge. Must be called while holding _lock."""
        edge = self._edges.pop(edge_id, None)
        if edge:
            self._outgoing.get(edge.source_id, []).remove(edge.id)
            self._incoming.get(edge.target_id, []).remove(edge.id)

    def remove_relation(self, edge_id: str) -> bool:
        """Remove a relationship by edge ID."""
        with self._lock:
            if edge_id not in self._edges:
                return False
            self._remove_edge_unsafe(edge_id)
            return True

    def get_relations(
        self,
        entity_id: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
        direction: str = "outgoing",  # "outgoing" | "incoming" | "both"
    ) -> List[GraphEdge]:
        """Get relations for an entity or by type."""
        with self._lock:
            results = []

            if entity_id:
                outgoing_ids = set(self._outgoing.get(entity_id, []))
                incoming_ids = set(self._incoming.get(entity_id, []))

                if direction == "outgoing":
                    candidates = outgoing_ids
                elif direction == "incoming":
                    candidates = incoming_ids
                else:
                    candidates = outgoing_ids | incoming_ids

                for eid in candidates:
                    edge = self._edges.get(eid)
                    if edge:
                        if relation_type is None or edge.relation_type == relation_type:
                            results.append(edge)
            else:
                for edge in self._edges.values():
                    if relation_type is None or edge.relation_type == relation_type:
                        results.append(edge)

            return results

    def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None,
        max_weight: Optional[float] = None,
        direction: str = "outgoing",
    ) -> List[Tuple[EntityNode, GraphEdge]]:
        """Get neighboring entities with their connecting edges."""
        edges = self.get_relations(
            entity_id=entity_id,
            relation_type=relation_type,
            direction=direction,
        )
        results = []
        with self._lock:
            for edge in edges:
                if direction == "outgoing":
                    neighbor_id = edge.target_id
                else:
                    neighbor_id = edge.source_id
                neighbor = self._entities.get(neighbor_id)
                if neighbor:
                    if max_weight is None or edge.weight >= max_weight:
                        results.append((neighbor, edge))
        return results

    def edge_count(self) -> int:
        """Count total edges."""
        with self._lock:
            return len(self._edges)

    def get_edges_from(self, source_id: str) -> List[GraphEdge]:
        """Get all edges originating from the specified entity.
        
        Args:
            source_id: The source entity ID
            
        Returns:
            List of GraphEdge objects with source_id matching the given ID
        """
        with self._lock:
            results = []
            for edge_id in self._outgoing.get(source_id, []):
                edge = self._edges.get(edge_id)
                if edge:
                    results.append(edge)
            return results

    def add_edge(self, source_id: str, target_id: str,
                 relation_type: RelationType = RelationType.CUSTOM,
                 weight: float = 1.0,
                 description: str = "",
                 metadata: Optional[Dict] = None) -> Optional[GraphEdge]:
        """Add an edge (alias for add_relation with simplified signature).
        
        This method provides a simpler interface for adding edges,
        compatible with callers that use keyword arguments.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relation_type: Type of relationship (defaults to CUSTOM)
            weight: Edge weight (0-1)
            description: Human-readable description
            metadata: Extra key-value metadata
            
        Returns:
            The created GraphEdge, or None if source/target not found
        """
        return self.add_relation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            description=description,
            metadata=metadata,
        )

    # ── Graph Queries ─────────────────────────────────────────────────────────

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 3,
        relation_types: Optional[List[RelationType]] = None,
    ) -> List[List[Tuple[EntityNode, GraphEdge]]]:
        """
        Find all paths between two entities up to max_depth.

        Returns:
            List of paths, each path is [(EntityNode, Edge), ...]
        """
        with self._lock:
            if source_id not in self._entities or target_id not in self._entities:
                return []

            all_paths: List[List] = []
            visited: Set[str] = set()

            def dfs(current_id: str, path: List[Tuple[str, str]]):
                if current_id == target_id:
                    # Reconstruct full path with objects
                    full_path = []
                    for nid, eid in path:
                        node = self._entities.get(nid)
                        edge = self._edges.get(eid)
                        if node and edge:
                            full_path.append((node, edge))
                    all_paths.append(full_path)
                    return

                if len(path) >= max_depth:
                    return

                for edge_id in self._outgoing.get(current_id, []):
                    edge = self._edges.get(edge_id)
                    if not edge:
                        continue
                    if relation_types and edge.relation_type not in relation_types:
                        continue
                    next_id = edge.target_id
                    if next_id in visited:
                        continue
                    visited.add(next_id)
                    path.append((next_id, edge_id))
                    dfs(next_id, path)
                    path.pop()
                    visited.remove(next_id)

            visited.add(source_id)
            dfs(source_id, [])
            return all_paths

    def shortest_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> Optional[List[Tuple[EntityNode, GraphEdge]]]:
        """Find the shortest path between two entities (BFS)."""
        paths = self.find_paths(source_id, target_id, max_depth=max_depth)
        if not paths:
            return None
        return min(paths, key=len)

    def subgraph(
        self,
        entity_ids: List[str],
        include_edges: bool = True,
    ) -> List[EntityNode]:
        """Get a subgraph containing the given entities and their connections."""
        with self._lock:
            result_entities = []
            for eid in entity_ids:
                if eid in self._entities:
                    result_entities.append(self._entities[eid])
            return result_entities

    # ── Memory Association ────────────────────────────────────────────────────

    def link_to_memory(self, entity_id: str, memory_id: str) -> bool:
        """Associate an entity with a memory entry (bidirectional)."""
        with self._lock:
            entity = self._entities.get(entity_id)
            if not entity:
                return False
            if memory_id not in entity.memory_ids:
                entity.memory_ids.append(memory_id)
            return True

    def unlink_from_memory(self, entity_id: str, memory_id: str) -> bool:
        """Remove association between an entity and a memory entry."""
        with self._lock:
            entity = self._entities.get(entity_id)
            if not entity:
                return False
            if memory_id in entity.memory_ids:
                entity.memory_ids.remove(memory_id)
            return True

    def get_entities_by_memory(self, memory_id: str) -> List[EntityNode]:
        """Get all entities linked to a specific memory entry."""
        with self._lock:
            return [
                e for e in self._entities.values()
                if memory_id in e.memory_ids
            ]

    def get_memories_for_entity(self, entity_id: str) -> List[str]:
        """Get all memory IDs linked to an entity."""
        entity = self.get_entity(entity_id)
        if not entity:
            return []
        return list(entity.memory_ids)

    # ── Stats & Export ───────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        with self._lock:
            type_counts: Dict[str, int] = {}
            for entity in self._entities.values():
                t = entity.entity_type.value
                type_counts[t] = type_counts.get(t, 0) + 1

            rel_counts: Dict[str, int] = {}
            for edge in self._edges.values():
                t = edge.relation_type.value
                rel_counts[t] = rel_counts.get(t, 0) + 1

            return {
                "entity_count": len(self._entities),
                "edge_count": len(self._edges),
                "entity_types": type_counts,
                "relation_types": rel_counts,
            }

    def to_dict(self) -> Dict[str, Any]:
        """Export entire graph as dictionary."""
        with self._lock:
            return {
                "entities": [e.to_dict() for e in self._entities.values()],
                "edges": [e.to_dict() for e in self._edges.values()],
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityGraph":
        """Reconstruct graph from dictionary."""
        graph = cls()
        for entity_data in data.get("entities", []):
            node = EntityNode.from_dict(entity_data)
            graph._entities[node.id] = node
            graph._outgoing.setdefault(node.id, [])
            graph._incoming.setdefault(node.id, [])
        for edge_data in data.get("edges", []):
            edge = GraphEdge.from_dict(edge_data)
            graph._edges[edge.id] = edge
            graph._outgoing.setdefault(edge.source_id, []).append(edge.id)
            graph._incoming.setdefault(edge.target_id, []).append(edge.id)
        return graph


# ── Convenience functions ─────────────────────────────────────────────────────

def create_entity_graph() -> EntityGraph:
    """Create a new EntityGraph instance."""
    return EntityGraph()


def extract_entities_from_text(
    text: str,
    graph: EntityGraph,
    entity_type: EntityType = EntityType.CONCEPT,
) -> List[EntityNode]:
    """
    Simple entity extraction from text.

    Extracts comma/pipe-separated names from text as entities.
    In production this would use NER/LLM.

    Args:
        text: Input text containing entity names
        graph: Target EntityGraph to add entities to
        entity_type: Default entity type for extracted entities

    Returns:
        List of created EntityNode objects
    """
    import re
    # Split on common separators and filter short tokens
    raw_names = re.split(r"[,，|｜\n]+", text)
    created = []
    for name in raw_names:
        name = name.strip()
        if len(name) >= 2 and not graph.find_entity(name):
            node = graph.add_entity(
                name=name,
                entity_type=entity_type,
                description=f"Extracted from text: {name[:50]}",
            )
            created.append(node)
    return created
