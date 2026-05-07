#include "SoulEngine/Entity/EntityGraph.h"

UEntityGraph::UEntityGraph()
{
}

FEntityNode UEntityGraph::AddEntity(const FString& Name, EEntityType EntityType,
	const FString& Description, const FString& EntityId, float Importance)
{
	FEntityNode Node;
	Node.Id = EntityId.IsEmpty() ? FGuid::NewGuid().ToString() : EntityId;
	Node.Name = Name;
	Node.EntityType = EntityType;
	Node.Description = Description;
	Node.Importance = Importance;
	Entities.Add(Node.Id, Node);

	if (!Outgoing.Contains(Node.Id)) Outgoing.Add(Node.Id, TArray<FString>());
	if (!Incoming.Contains(Node.Id)) Incoming.Add(Node.Id, TArray<FString>());

	return Node;
}

bool UEntityGraph::GetEntity(const FString& EntityId, FEntityNode& OutEntity)
{
	FEntityNode* Node = Entities.Find(EntityId);
	if (!Node) return false;
	OutEntity = *Node;
	return true;
}

bool UEntityGraph::FindEntity(const FString& Name, FEntityNode& OutEntity)
{
	FString NameLower = Name.ToLower();
	for (auto& KV : Entities)
	{
		if (KV.Value.Name.ToLower() == NameLower)
		{
			OutEntity = KV.Value;
			return true;
		}
	}
	return false;
}

bool UEntityGraph::DeleteEntity(const FString& EntityId)
{
	if (!Entities.Contains(EntityId)) return false;

	TArray<FString>* OutEdges = Outgoing.Find(EntityId);
	if (OutEdges)
	{
		for (const FString& EdgeId : *OutEdges)
			RemoveEdgeUnsafe(EdgeId);
	}

	TArray<FString>* InEdges = Incoming.Find(EntityId);
	if (InEdges)
	{
		for (const FString& EdgeId : *InEdges)
			RemoveEdgeUnsafe(EdgeId);
	}

	Entities.Remove(EntityId);
	return true;
}

TArray<FEntityNode> UEntityGraph::QueryEntities(EEntityType EntityType,
	const FString& NameContains, float MinImportance, int32 Limit)
{
	TArray<FEntityNode> Results;
	FString NameLower = NameContains.ToLower();

	for (const auto& KV : Entities)
	{
		if (KV.Value.EntityType != EntityType) continue;
		if (KV.Value.Importance < MinImportance) continue;
		if (!NameContains.IsEmpty() && !KV.Value.Name.ToLower().Contains(NameLower)) continue;
		Results.Add(KV.Value);
		if (Results.Num() >= Limit) break;
	}
	return Results;
}

FGraphEdge UEntityGraph::AddRelation(const FString& SourceId, const FString& TargetId,
	ERelationType RelationType, float Weight, EEdgeDirection Direction,
	const FString& Description, const FString& EdgeId)
{
	FGraphEdge EmptyEdge;
	if (!Entities.Contains(SourceId) || !Entities.Contains(TargetId)) return EmptyEdge;

	FGraphEdge Edge;
	Edge.Id = EdgeId.IsEmpty() ? FGuid::NewGuid().ToString() : EdgeId;
	Edge.SourceId = SourceId;
	Edge.TargetId = TargetId;
	Edge.RelationType = RelationType;
	Edge.Direction = Direction;
	Edge.Weight = Weight;
	Edge.Description = Description;

	Edges.Add(Edge.Id, Edge);
	Outgoing.FindOrAdd(SourceId).Add(Edge.Id);
	Incoming.FindOrAdd(TargetId).Add(Edge.Id);

	// For undirected, add reverse edge
	if (Direction == EEdgeDirection::Undirected)
	{
		FGraphEdge RevEdge;
		RevEdge.Id = FGuid::NewGuid().ToString();
		RevEdge.SourceId = TargetId;
		RevEdge.TargetId = SourceId;
		RevEdge.RelationType = RelationType;
		RevEdge.Direction = EEdgeDirection::Undirected;
		RevEdge.Weight = Weight;
		RevEdge.Description = Description;

		Edges.Add(RevEdge.Id, RevEdge);
		Outgoing.FindOrAdd(TargetId).Add(RevEdge.Id);
		Incoming.FindOrAdd(SourceId).Add(RevEdge.Id);
	}

	return Edge;
}

bool UEntityGraph::RemoveRelation(const FString& EdgeId)
{
	if (!Edges.Contains(EdgeId)) return false;
	RemoveEdgeUnsafe(EdgeId);
	return true;
}

TArray<FGraphEdge> UEntityGraph::GetEdgesFrom(const FString& SourceId)
{
	TArray<FGraphEdge> Results;
	TArray<FString>* EdgeIds = Outgoing.Find(SourceId);
	if (!EdgeIds) return Results;

	for (const FString& EdgeId : *EdgeIds)
	{
		FGraphEdge* Edge = Edges.Find(EdgeId);
		if (Edge) Results.Add(*Edge);
	}
	return Results;
}

TArray<FGraphEdge> UEntityGraph::GetRelations(const FString& EntityId,
	ERelationType RelationType, bool bFilterRelationType, const FString& Direction)
{
	TArray<FGraphEdge> Results;

	if (!EntityId.IsEmpty())
	{
		TSet<FString> Candidates;
		TArray<FString>* OutIds = Outgoing.Find(EntityId);
		TArray<FString>* InIds = Incoming.Find(EntityId);

		if (Direction == TEXT("outgoing") && OutIds)
			for (const FString& Id : *OutIds) Candidates.Add(Id);
		else if (Direction == TEXT("incoming") && InIds)
			for (const FString& Id : *InIds) Candidates.Add(Id);
		else
		{
			if (OutIds) for (const FString& Id : *OutIds) Candidates.Add(Id);
			if (InIds) for (const FString& Id : *InIds) Candidates.Add(Id);
		}

		for (const FString& Eid : Candidates)
		{
			FGraphEdge* Edge = Edges.Find(Eid);
			if (Edge && (!bFilterRelationType || Edge->RelationType == RelationType))
				Results.Add(*Edge);
		}
	}
	else
	{
		for (const auto& KV : Edges)
		{
			if (!bFilterRelationType || KV.Value.RelationType == RelationType)
				Results.Add(KV.Value);
		}
	}

	return Results;
}

TArray<TArray<FPathStep>> UEntityGraph::FindPaths(const FString& SourceId, const FString& TargetId,
	int32 MaxDepth, const TArray<ERelationType>& RelationTypes)
{
	if (!Entities.Contains(SourceId) || !Entities.Contains(TargetId))
		return TArray<TArray<FPathStep>>();

	TArray<TArray<FPathStep>> AllPaths;
	TSet<FString> Visited;
	Visited.Add(SourceId);

	TArray<TPair<FString, FString>> Path;
	DFS(SourceId, TargetId, MaxDepth, Visited, Path, AllPaths, RelationTypes);
	return AllPaths;
}

bool UEntityGraph::ShortestPath(const FString& SourceId, const FString& TargetId,
	TArray<FPathStep>& OutPath, int32 MaxDepth)
{
	TArray<TArray<FPathStep>> Paths = FindPaths(SourceId, TargetId, MaxDepth);
	if (Paths.Num() == 0) return false;

	// Find shortest
	int32 MinIdx = 0;
	for (int32 i = 1; i < Paths.Num(); ++i)
	{
		if (Paths[i].Num() < Paths[MinIdx].Num()) MinIdx = i;
	}
	OutPath = Paths[MinIdx];
	return true;
}

bool UEntityGraph::LinkToMemory(const FString& EntityId, const FString& MemoryId)
{
	FEntityNode* Entity = Entities.Find(EntityId);
	if (!Entity) return false;
	if (!Entity->MemoryIds.Contains(MemoryId))
		Entity->MemoryIds.Add(MemoryId);
	return true;
}

bool UEntityGraph::UnlinkFromMemory(const FString& EntityId, const FString& MemoryId)
{
	FEntityNode* Entity = Entities.Find(EntityId);
	if (!Entity) return false;
	return Entity->MemoryIds.Remove(MemoryId) > 0;
}

void UEntityGraph::RemoveEdgeUnsafe(const FString& EdgeId)
{
	FGraphEdge* Edge = Edges.Find(EdgeId);
	if (!Edge) return;

	TArray<FString>* OutList = Outgoing.Find(Edge->SourceId);
	if (OutList) OutList->Remove(EdgeId);

	TArray<FString>* InList = Incoming.Find(Edge->TargetId);
	if (InList) InList->Remove(EdgeId);

	Edges.Remove(EdgeId);
}

void UEntityGraph::DFS(const FString& CurrentId, const FString& TargetId, int32 MaxDepth,
	TSet<FString>& Visited, TArray<TPair<FString, FString>>& Path,
	TArray<TArray<FPathStep>>& AllPaths, const TArray<ERelationType>& RelationTypes)
{
	if (CurrentId == TargetId)
	{
		TArray<FPathStep> FullPath;
		for (const auto& P : Path)
		{
			FEntityNode* Node = Entities.Find(P.Key);
			FGraphEdge* Edge = Edges.Find(P.Value);
			if (Node && Edge)
			{
				FPathStep Step;
				Step.Node = *Node;
				Step.Edge = *Edge;
				FullPath.Add(Step);
			}
		}
		AllPaths.Add(FullPath);
		return;
	}

	if (Path.Num() >= MaxDepth) return;

	TArray<FString>* EdgeIds = Outgoing.Find(CurrentId);
	if (!EdgeIds) return;

	for (const FString& EdgeId : *EdgeIds)
	{
		FGraphEdge* Edge = Edges.Find(EdgeId);
		if (!Edge) continue;
		if (RelationTypes.Num() > 0 && !RelationTypes.Contains(Edge->RelationType)) continue;
		if (Visited.Contains(Edge->TargetId)) continue;

		Visited.Add(Edge->TargetId);
		Path.Add(TPair<FString, FString>(Edge->TargetId, EdgeId));
		DFS(Edge->TargetId, TargetId, MaxDepth, Visited, Path, AllPaths, RelationTypes);
		Path.Pop();
		Visited.Remove(Edge->TargetId);
	}
}
