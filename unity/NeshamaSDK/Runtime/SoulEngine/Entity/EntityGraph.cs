using System;
using System.Collections.Generic;
using System.Linq;

namespace Neshama.SoulEngine.Entity
{
    /// <summary>
    /// Entity node in the knowledge graph.
    /// Ported from Python entity_graph.py EntityNode.
    /// </summary>
    [Serializable]
    public class EntityNode
    {
        public string id;
        public string name;
        public EntityType entityType;
        public string description = "";
        public float importance = 0.5f;
        public int accessCount;
        public List<string> memoryIds = new List<string>();
    }

    /// <summary>
    /// Graph edge (relationship) between entities.
    /// Ported from Python GraphEdge.
    /// </summary>
    [Serializable]
    public class GraphEdge
    {
        public string id;
        public string sourceId;
        public string targetId;
        public RelationType relationType;
        public EdgeDirection direction = EdgeDirection.Directed;
        public float weight = 1.0f;
        public string description = "";
        public float confidence = 1.0f;
    }

    /// <summary>
    /// Entity Knowledge Graph. Manages entity nodes and their relationships.
    /// Ported from Python entity_graph.py EntityGraph.
    /// 
    /// In-memory adjacency-list implementation.
    /// No thread locking needed in Unity (main thread only).
    /// </summary>
    public class EntityGraph
    {
        private Dictionary<string, EntityNode> _entities = new Dictionary<string, EntityNode>();
        private Dictionary<string, GraphEdge> _edges = new Dictionary<string, GraphEdge>();
        private Dictionary<string, List<string>> _outgoing = new Dictionary<string, List<string>>();
        private Dictionary<string, List<string>> _incoming = new Dictionary<string, List<string>>();

        // ── Entity Operations ────────────────────────────────────────────────────

        /// <summary>
        /// Add an entity to the graph.
        /// </summary>
        public EntityNode AddEntity(string name, EntityType entityType, string description = "",
            string entityId = null, float importance = 0.5f)
        {
            var node = new EntityNode
            {
                id = entityId ?? Guid.NewGuid().ToString(),
                name = name,
                entityType = entityType,
                description = description,
                importance = importance,
            };
            _entities[node.id] = node;
            if (!_outgoing.ContainsKey(node.id)) _outgoing[node.id] = new List<string>();
            if (!_incoming.ContainsKey(node.id)) _incoming[node.id] = new List<string>();
            return node;
        }

        /// <summary>
        /// Get an entity by ID.
        /// </summary>
        public EntityNode GetEntity(string entityId)
        {
            EntityNode node;
            return _entities.TryGetValue(entityId, out node) ? node : null;
        }

        /// <summary>
        /// Find an entity by name (case-insensitive).
        /// </summary>
        public EntityNode FindEntity(string name)
        {
            string nameLower = name.ToLower();
            foreach (var entity in _entities.Values)
            {
                if (entity.name.ToLower() == nameLower)
                    return entity;
            }
            return null;
        }

        /// <summary>
        /// Delete an entity and all its edges.
        /// </summary>
        public bool DeleteEntity(string entityId)
        {
            if (!_entities.ContainsKey(entityId)) return false;

            foreach (var edgeId in _outgoing.GetOrCreate(entityId).ToList())
                RemoveEdgeUnsafe(edgeId);
            foreach (var edgeId in _incoming.GetOrCreate(entityId).ToList())
                RemoveEdgeUnsafe(edgeId);

            _entities.Remove(entityId);
            return true;
        }

        /// <summary>
        /// Query entities by type, name substring, and minimum importance.
        /// </summary>
        public List<EntityNode> QueryEntities(EntityType? entityType = null,
            string nameContains = null, float minImportance = 0f, int limit = 100)
        {
            var results = new List<EntityNode>();
            foreach (var entity in _entities.Values)
            {
                if (entityType.HasValue && entity.entityType != entityType.Value) continue;
                if (entity.importance < minImportance) continue;
                if (nameContains != null && !entity.name.ToLower().Contains(nameContains.ToLower())) continue;
                results.Add(entity);
                if (results.Count >= limit) break;
            }
            return results;
        }

        public int EntityCount => _entities.Count;

        // ── Relation Operations ──────────────────────────────────────────────────

        /// <summary>
        /// Add a relationship between two entities.
        /// </summary>
        public GraphEdge AddRelation(string sourceId, string targetId, RelationType relationType,
            float weight = 1.0f, EdgeDirection direction = EdgeDirection.Directed,
            string description = "", string edgeId = null)
        {
            if (!_entities.ContainsKey(sourceId) || !_entities.ContainsKey(targetId)) return null;

            var edge = new GraphEdge
            {
                id = edgeId ?? Guid.NewGuid().ToString(),
                sourceId = sourceId,
                targetId = targetId,
                relationType = relationType,
                direction = direction,
                weight = weight,
                description = description,
            };

            _edges[edge.id] = edge;
            _outgoing.GetOrCreate(sourceId).Add(edge.id);
            _incoming.GetOrCreate(targetId).Add(edge.id);

            // For undirected, add reverse edge
            if (direction == EdgeDirection.Undirected)
            {
                var revEdge = new GraphEdge
                {
                    id = Guid.NewGuid().ToString(),
                    sourceId = targetId,
                    targetId = sourceId,
                    relationType = relationType,
                    direction = EdgeDirection.Undirected,
                    weight = weight,
                    description = description,
                };
                _edges[revEdge.id] = revEdge;
                _outgoing.GetOrCreate(targetId).Add(revEdge.id);
                _incoming.GetOrCreate(sourceId).Add(revEdge.id);
            }

            return edge;
        }

        /// <summary>
        /// Remove a relationship by edge ID.
        /// </summary>
        public bool RemoveRelation(string edgeId)
        {
            if (!_edges.ContainsKey(edgeId)) return false;
            RemoveEdgeUnsafe(edgeId);
            return true;
        }

        /// <summary>
        /// Get edges from a specific entity.
        /// </summary>
        public List<GraphEdge> GetEdgesFrom(string sourceId)
        {
            var results = new List<GraphEdge>();
            foreach (var edgeId in _outgoing.GetOrCreate(sourceId))
            {
                GraphEdge edge;
                if (_edges.TryGetValue(edgeId, out edge))
                    results.Add(edge);
            }
            return results;
        }

        /// <summary>
        /// Get relations for an entity.
        /// </summary>
        public List<GraphEdge> GetRelations(string entityId = null,
            RelationType? relationType = null, string direction = "outgoing")
        {
            var results = new List<GraphEdge>();

            if (entityId != null)
            {
                var outgoingIds = new HashSet<string>(_outgoing.GetOrCreate(entityId));
                var incomingIds = new HashSet<string>(_incoming.GetOrCreate(entityId));

                IEnumerable<string> candidates;
                if (direction == "outgoing") candidates = outgoingIds;
                else if (direction == "incoming") candidates = incomingIds;
                else candidates = outgoingIds.Union(incomingIds);

                foreach (var eid in candidates)
                {
                    GraphEdge edge;
                    if (_edges.TryGetValue(eid, out edge))
                    {
                        if (relationType == null || edge.relationType == relationType.Value)
                            results.Add(edge);
                    }
                }
            }
            else
            {
                foreach (var edge in _edges.Values)
                {
                    if (relationType == null || edge.relationType == relationType.Value)
                        results.Add(edge);
                }
            }

            return results;
        }

        public int EdgeCount => _edges.Count;

        // ── Graph Queries ────────────────────────────────────────────────────────

        /// <summary>
        /// Find all paths between two entities up to max depth (DFS).
        /// Ported from Python find_paths().
        /// </summary>
        public List<List<(EntityNode node, GraphEdge edge)>> FindPaths(
            string sourceId, string targetId, int maxDepth = 3,
            RelationType[] relationTypes = null)
        {
            if (!_entities.ContainsKey(sourceId) || !_entities.ContainsKey(targetId))
                return new List<List<(EntityNode, GraphEdge)>>();

            var allPaths = new List<List<(EntityNode, GraphEdge)>>();
            var visited = new HashSet<string> { sourceId };

            DFS(sourceId, targetId, maxDepth, visited, new List<(string, string)>(), allPaths, relationTypes);
            return allPaths;
        }

        /// <summary>
        /// Find shortest path (BFS-like via find_paths + min).
        /// </summary>
        public List<(EntityNode node, GraphEdge edge)> ShortestPath(
            string sourceId, string targetId, int maxDepth = 5)
        {
            var paths = FindPaths(sourceId, targetId, maxDepth);
            if (paths.Count == 0) return null;
            return paths.OrderBy(p => p.Count).First();
        }

        // ── Memory Association ───────────────────────────────────────────────────

        public bool LinkToMemory(string entityId, string memoryId)
        {
            EntityNode entity;
            if (!_entities.TryGetValue(entityId, out entity)) return false;
            if (!entity.memoryIds.Contains(memoryId))
                entity.memoryIds.Add(memoryId);
            return true;
        }

        public bool UnlinkFromMemory(string entityId, string memoryId)
        {
            EntityNode entity;
            if (!_entities.TryGetValue(entityId, out entity)) return false;
            return entity.memoryIds.Remove(memoryId);
        }

        // ── Private Methods ──────────────────────────────────────────────────────

        private void RemoveEdgeUnsafe(string edgeId)
        {
            GraphEdge edge;
            if (!_edges.TryGetValue(edgeId, out edge)) return;
            _edges.Remove(edgeId);
            _outgoing.GetOrCreate(edge.sourceId).Remove(edgeId);
            _incoming.GetOrCreate(edge.targetId).Remove(edgeId);
        }

        private void DFS(
            string currentId, string targetId, int maxDepth,
            HashSet<string> visited, List<(string nodeId, string edgeId)> path,
            List<List<(EntityNode, GraphEdge)>> allPaths,
            RelationType[] relationTypes)
        {
            if (currentId == targetId)
            {
                var fullPath = new List<(EntityNode, GraphEdge)>();
                foreach (var (nodeId, edgeId) in path)
                {
                    EntityNode node;
                    GraphEdge edge;
                    if (_entities.TryGetValue(nodeId, out node) && _edges.TryGetValue(edgeId, out edge))
                        fullPath.Add((node, edge));
                }
                allPaths.Add(fullPath);
                return;
            }

            if (path.Count >= maxDepth) return;

            foreach (var edgeId in _outgoing.GetOrCreate(currentId))
            {
                GraphEdge edge;
                if (!_edges.TryGetValue(edgeId, out edge)) continue;
                if (relationTypes != null && !relationTypes.Contains(edge.relationType)) continue;
                if (visited.Contains(edge.targetId)) continue;

                visited.Add(edge.targetId);
                path.Add((edge.targetId, edgeId));
                DFS(edge.targetId, targetId, maxDepth, visited, path, allPaths, relationTypes);
                path.RemoveAt(path.Count - 1);
                visited.Remove(edge.targetId);
            }
        }
    }

    // ── Extension ────────────────────────────────────────────────────────────────

    internal static class DictExtensions
    {
        public static List<T> GetOrCreate<T>(this Dictionary<string, List<T>> dict, string key)
        {
            List<T> list;
            if (!dict.TryGetValue(key, out list))
            {
                list = new List<T>();
                dict[key] = list;
            }
            return list;
        }
    }
}
