"""
Entity Graph API - Web endpoints for entity knowledge graph.
"""

from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException

router = APIRouter()

# Module-level graph instance
_graph_instances: Dict[str, Dict[str, Any]] = {}


def get_or_create_graph(graph_id: str) -> Any:
    """Get or create a graph instance."""
    if graph_id not in _graph_instances:
        from neshama.soul.entity_graph import EntityGraph, EntityType, RelationType
        _graph_instances[graph_id] = {
            "graph": EntityGraph(),
            "entity_types": {e.value: e for e in EntityType},
            "relation_types": {e.value: e for e in RelationType},
        }
    return _graph_instances[graph_id]


@router.post("/entity")
async def add_entity(
    graph_id: str = "default",
    name: str = "",
    entity_type: str = "concept",
    description: str = "",
    importance: float = 0.5,
):
    """Add an entity to the graph."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    entity_type_enum = data["entity_types"].get(entity_type)
    if entity_type_enum is None:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")

    entity = graph.add_entity(
        name=name,
        entity_type=entity_type_enum,
        description=description,
        importance=importance,
    )
    return {
        "success": True,
        "data": entity.to_dict(),
    }


@router.get("/entity/{entity_id}")
async def get_entity(graph_id: str = "default", entity_id: str = ""):
    """Get an entity by ID."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    entity = graph.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"success": True, "data": entity.to_dict()}


@router.get("/entity/find/{name}")
async def find_entity(graph_id: str = "default", name: str = ""):
    """Find entity by name."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    entity = graph.find_entity(name)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"success": True, "data": entity.to_dict()}


@router.get("/entities")
async def query_entities(
    graph_id: str = "default",
    entity_type: Optional[str] = None,
    name_contains: Optional[str] = None,
    min_importance: float = 0.0,
    limit: int = 100,
):
    """Query entities with filters."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    entity_type_enum = None
    if entity_type:
        entity_type_enum = data["entity_types"].get(entity_type)
        if entity_type_enum is None:
            raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")

    entities = graph.query_entities(
        entity_type=entity_type_enum,
        name_contains=name_contains,
        min_importance=min_importance,
        limit=limit,
    )
    return {
        "success": True,
        "data": {
            "entities": [e.to_dict() for e in entities],
            "total": len(entities),
        }
    }


@router.delete("/entity/{entity_id}")
async def delete_entity(graph_id: str = "default", entity_id: str = ""):
    """Delete an entity and its edges."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    result = graph.delete_entity(entity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"success": True, "data": {"deleted": True}}


@router.post("/relation")
async def add_relation(
    graph_id: str = "default",
    source_id: str = "",
    target_id: str = "",
    relation_type: str = "related_to",
    weight: float = 1.0,
    direction: str = "directed",
):
    """Add a relationship between entities."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    relation_type_enum = data["relation_types"].get(relation_type)
    if relation_type_enum is None:
        raise HTTPException(status_code=400, detail=f"Unknown relation type: {relation_type}")

    from neshama.soul.entity_graph import EdgeDirection
    direction_enum = EdgeDirection.DIRECTED if direction == "directed" else EdgeDirection.UNDIRECTED

    edge = graph.add_relation(
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type_enum,
        weight=weight,
        direction=direction_enum,
    )
    if edge is None:
        raise HTTPException(status_code=400, detail="Could not create relation (entity not found?)")
    return {"success": True, "data": edge.to_dict()}


@router.get("/relations")
async def get_relations(
    graph_id: str = "default",
    entity_id: Optional[str] = None,
    relation_type: Optional[str] = None,
    direction: str = "outgoing",
):
    """Get relations for an entity or by type."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    relation_type_enum = None
    if relation_type:
        relation_type_enum = data["relation_types"].get(relation_type)

    relations = graph.get_relations(
        entity_id=entity_id,
        relation_type=relation_type_enum,
        direction=direction,
    )
    return {
        "success": True,
        "data": {
            "relations": [r.to_dict() for r in relations],
            "total": len(relations),
        }
    }


@router.get("/neighbors/{entity_id}")
async def get_neighbors(
    graph_id: str = "default",
    entity_id: str = "",
    relation_type: Optional[str] = None,
    direction: str = "outgoing",
):
    """Get neighboring entities."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    relation_type_enum = None
    if relation_type:
        relation_type_enum = data["relation_types"].get(relation_type)

    neighbors = graph.get_neighbors(
        entity_id=entity_id,
        relation_type=relation_type_enum,
        direction=direction,
    )
    return {
        "success": True,
        "data": {
            "neighbors": [
                {"entity": n[0].to_dict(), "edge": n[1].to_dict()}
                for n in neighbors
            ],
            "total": len(neighbors),
        }
    }


@router.get("/paths/{source_id}/{target_id}")
async def find_paths(
    graph_id: str = "default",
    source_id: str = "",
    target_id: str = "",
    max_depth: int = 3,
):
    """Find paths between two entities."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    paths = graph.find_paths(source_id, target_id, max_depth=max_depth)
    return {
        "success": True,
        "data": {
            "paths": [
                [
                    {"entity": node.to_dict(), "edge": edge.to_dict()}
                    for node, edge in path
                ]
                for path in paths
            ],
            "count": len(paths),
        }
    }


@router.post("/memory/link")
async def link_to_memory(
    graph_id: str = "default",
    entity_id: str = "",
    memory_id: str = "",
):
    """Link an entity to a memory entry."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    result = graph.link_to_memory(entity_id, memory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"success": True, "data": {"linked": True}}


@router.get("/stats")
async def get_stats(graph_id: str = "default"):
    """Get graph statistics."""
    data = get_or_create_graph(graph_id)
    graph = data["graph"]
    stats = graph.get_stats()
    return {"success": True, "data": stats}
