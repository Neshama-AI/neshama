#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Entity/EntityTypes.h"
#include "EntityGraph.generated.h"

/**
 * Entity node in the knowledge graph.
 */
USTRUCT(BlueprintType)
struct FEntityNode
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EEntityType EntityType = EEntityType::Custom;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Importance = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	int32 AccessCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TArray<FString> MemoryIds;
};

/**
 * Graph edge (relationship) between entities.
 */
USTRUCT(BlueprintType)
struct FGraphEdge
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString SourceId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString TargetId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	ERelationType RelationType = ERelationType::RelatedTo;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EEdgeDirection Direction = EEdgeDirection::Directed;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Weight = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Confidence = 1.0f;
};

/**
 * Path step: (node, edge).
 */
USTRUCT(BlueprintType)
struct FPathStep
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FEntityNode Node;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FGraphEdge Edge;
};

/**
 * Entity Knowledge Graph. Manages entity nodes and their relationships.
 * Ported from Python/C# EntityGraph.
 */
UCLASS(BlueprintType)
class NESHAMASDK_API UEntityGraph : public UObject
{
	GENERATED_BODY()

public:
	UEntityGraph();

	// ── Entity Operations ────────────────────────────────────────────────────

	/** Add an entity to the graph. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	FEntityNode AddEntity(const FString& Name, EEntityType EntityType,
		const FString& Description = TEXT(""), const FString& EntityId = TEXT(""),
		float Importance = 0.5f);

	/** Get an entity by ID. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	bool GetEntity(const FString& EntityId, FEntityNode& OutEntity);

	/** Find an entity by name (case-insensitive). */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	bool FindEntity(const FString& Name, FEntityNode& OutEntity);

	/** Delete an entity and all its edges. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	bool DeleteEntity(const FString& EntityId);

	/** Query entities by type, name substring, and minimum importance. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	TArray<FEntityNode> QueryEntities(EEntityType EntityType, const FString& NameContains,
		float MinImportance = 0.0f, int32 Limit = 100);

	/** Get entity count. */
	UFUNCTION(BlueprintCallable, Category = "Neshama", BlueprintPure)
	int32 GetEntityCount() const { return Entities.Num(); }

	// ── Relation Operations ──────────────────────────────────────────────────

	/** Add a relationship between two entities. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	FGraphEdge AddRelation(const FString& SourceId, const FString& TargetId,
		ERelationType RelationType, float Weight = 1.0f,
		EEdgeDirection Direction = EEdgeDirection::Directed,
		const FString& Description = TEXT(""), const FString& EdgeId = TEXT(""));

	/** Remove a relationship by edge ID. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	bool RemoveRelation(const FString& EdgeId);

	/** Get edges from a specific entity. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	TArray<FGraphEdge> GetEdgesFrom(const FString& SourceId);

	/** Get relations for an entity. */
	TArray<FGraphEdge> GetRelations(const FString& EntityId = TEXT(""),
		ERelationType RelationType = ERelationType::RelatedTo,
		bool bFilterRelationType = false,
		const FString& Direction = TEXT("outgoing"));

	/** Get edge count. */
	UFUNCTION(BlueprintCallable, Category = "Neshama", BlueprintPure)
	int32 GetEdgeCount() const { return Edges.Num(); }

	// ── Graph Queries ────────────────────────────────────────────────────────

	/** Find all paths between two entities up to max depth (DFS). */
	TArray<TArray<FPathStep>> FindPaths(const FString& SourceId, const FString& TargetId,
		int32 MaxDepth, const TArray<ERelationType>& RelationTypes);

	/** Find all paths without filtering by relation type. */
	TArray<TArray<FPathStep>> FindPaths(const FString& SourceId, const FString& TargetId,
		int32 MaxDepth = 3);

	/** Find shortest path (BFS-like). */
	bool ShortestPath(const FString& SourceId, const FString& TargetId,
		TArray<FPathStep>& OutPath, int32 MaxDepth = 5);

	// ── Memory Association ───────────────────────────────────────────────────

	UFUNCTION(BlueprintCallable, Category = "Neshama")
	bool LinkToMemory(const FString& EntityId, const FString& MemoryId);

	UFUNCTION(BlueprintCallable, Category = "Neshama")
	bool UnlinkFromMemory(const FString& EntityId, const FString& MemoryId);

private:
	UPROPERTY()
	TMap<FString, FEntityNode> Entities;

	UPROPERTY()
	TMap<FString, FGraphEdge> Edges;

	TMap<FString, TArray<FString>> Outgoing;
	TMap<FString, TArray<FString>> Incoming;

	void RemoveEdgeUnsafe(const FString& EdgeId);

	void DFS(const FString& CurrentId, const FString& TargetId, int32 MaxDepth,
		TSet<FString>& Visited, TArray<TPair<FString, FString>>& Path,
		TArray<TArray<FPathStep>>& AllPaths, const TArray<ERelationType>& RelationTypes);
};
