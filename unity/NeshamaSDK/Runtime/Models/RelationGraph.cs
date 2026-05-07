using System;
using System.Collections.Generic;
using UnityEngine;

namespace Neshama.SDK.Models
{
    /// <summary>
    /// 关系图谱数据类
    /// 描述NPC与其他实体（玩家、其他NPC、物品等）的关系
    /// </summary>
    [Serializable]
    public class RelationGraph
    {
        /// <summary>
        /// 实体列表
        /// </summary>
        [SerializeField]
        public List<RelationEntity> entities;

        /// <summary>
        /// 关系列表
        /// </summary>
        [SerializeField]
        public List<Relation> relations;

        /// <summary>
        /// 获取与指定实体的关系
        /// </summary>
        /// <param name="entityId">实体ID</param>
        /// <returns>关系对象，如果没有则返回null</returns>
        public Relation GetRelationWith(string entityId)
        {
            if (relations == null) return null;
            
            foreach (var relation in relations)
            {
                if (relation.target_id == entityId || relation.source_id == entityId)
                {
                    return relation;
                }
            }
            return null;
        }

        /// <summary>
        /// 获取与指定玩家的关系
        /// </summary>
        public Relation GetPlayerRelation(string playerId)
        {
            return GetRelationWith(playerId);
        }

        /// <summary>
        /// 获取与玩家的关系类型
        /// </summary>
        public string GetPlayerRelationType(string playerId)
        {
            var relation = GetPlayerRelation(playerId);
            return relation?.relation_type ?? "unknown";
        }

        /// <summary>
        /// 判断玩家是否是盟友
        /// </summary>
        public bool IsPlayerAlly(string playerId)
        {
            var type = GetPlayerRelationType(playerId);
            return type == "ally" || type == "friend";
        }

        /// <summary>
        /// 判断玩家是否是敌人
        /// </summary>
        public bool IsPlayerEnemy(string playerId)
        {
            var type = GetPlayerRelationType(playerId);
            return type == "enemy" || type == "hostile";
        }

        /// <summary>
        /// 获取所有盟友
        /// </summary>
        public List<RelationEntity> GetAllies()
        {
            var allies = new List<RelationEntity>();
            if (entities == null || relations == null) return allies;

            foreach (var relation in relations)
            {
                if (relation.relation_type == "ally" || relation.relation_type == "friend")
                {
                    var entity = entities.Find(e => e.entity_id == relation.target_id);
                    if (entity != null && !allies.Contains(entity))
                    {
                        allies.Add(entity);
                    }
                }
            }
            return allies;
        }

        /// <summary>
        /// 获取所有敌人
        /// </summary>
        public List<RelationEntity> GetEnemies()
        {
            var enemies = new List<RelationEntity>();
            if (entities == null || relations == null) return enemies;

            foreach (var relation in relations)
            {
                if (relation.relation_type == "enemy" || relation.relation_type == "hostile")
                {
                    var entity = entities.Find(e => e.entity_id == relation.target_id);
                    if (entity != null && !enemies.Contains(entity))
                    {
                        enemies.Add(entity);
                    }
                }
            }
            return enemies;
        }

        public override string ToString()
        {
            return $"RelationGraph: {entities?.Count ?? 0} entities, {relations?.Count ?? 0} relations";
        }
    }

    /// <summary>
    /// 关系实体数据类
    /// </summary>
    [Serializable]
    public class RelationEntity
    {
        /// <summary>
        /// 实体ID
        /// </summary>
        [SerializeField]
        public string entity_id;

        /// <summary>
        /// 实体名称
        /// </summary>
        [SerializeField]
        public string entity_name;

        /// <summary>
        /// 实体类型（player, npc, item, location 等）
        /// </summary>
        [SerializeField]
        public string entity_type;

        /// <summary>
        /// 实体描述
        /// </summary>
        [SerializeField]
        public string description;

        /// <summary>
        /// 额外属性（运行时使用，不参与JSON序列化）
        /// </summary>
        [System.NonSerialized]
        public Dictionary<string, object> attributes;

        public override string ToString()
        {
            return $"{entity_name} ({entity_type})";
        }
    }

    /// <summary>
    /// 关系数据类
    /// </summary>
    [Serializable]
    public class Relation
    {
        /// <summary>
        /// 关系来源实体ID
        /// </summary>
        [SerializeField]
        public string source_id;

        /// <summary>
        /// 关系目标实体ID
        /// </summary>
        [SerializeField]
        public string target_id;

        /// <summary>
        /// 关系类型（ally, enemy, neutral, friend, hostile 等）
        /// </summary>
        [SerializeField]
        public string relation_type;

        /// <summary>
        /// 关系强度，范围0-1
        /// </summary>
        [SerializeField]
        [Range(0f, 1f)]
        public float strength;

        /// <summary>
        /// 关系备注
        /// </summary>
        [SerializeField]
        public string note;

        /// <summary>
        /// 关系建立时间
        /// </summary>
        [SerializeField]
        public string created_at;

        /// <summary>
        /// 最后更新时间
        /// </summary>
        [SerializeField]
        public string updated_at;

        /// <summary>
        /// 获取关系友好度描述
        /// </summary>
        public string GetFriendlyLevel()
        {
            if (strength > 0.7f) return "密切";
            if (strength > 0.4f) return "一般";
            if (strength > 0.2f) return "疏远";
            return "陌生";
        }

        public override string ToString()
        {
            return $"{source_id} -> {target_id}: {relation_type} ({strength})";
        }
    }

    /// <summary>
    /// 记忆数据类
    /// </summary>
    [Serializable]
    public class Memory
    {
        /// <summary>
        /// 记忆ID
        /// </summary>
        [SerializeField]
        public string memory_id;

        /// <summary>
        /// 记忆内容
        /// </summary>
        [SerializeField]
        public string content;

        /// <summary>
        /// 记忆类型（event, entity, location 等）
        /// </summary>
        [SerializeField]
        public string memory_type;

        /// <summary>
        /// 记忆重要性，范围0-1
        /// </summary>
        [SerializeField]
        [Range(0f, 1f)]
        public float importance;

        /// <summary>
        /// 记忆时间戳
        /// </summary>
        [SerializeField]
        public long timestamp;

        /// <summary>
        /// 相关实体ID
        /// </summary>
        [SerializeField]
        public List<string> related_entities;

        /// <summary>
        /// 记忆情感标签
        /// </summary>
        [SerializeField]
        public List<string> emotion_tags;

        public override string ToString()
        {
            return $"Memory: {content?.Substring(0, Math.Min(50, content.Length))}...";
        }
    }

    /// <summary>
    /// 记忆列表响应
    /// </summary>
    [Serializable]
    public class MemoryListResponse
    {
        /// <summary>
        /// 记忆列表
        /// </summary>
        [SerializeField]
        public List<Memory> memories;

        /// <summary>
        /// 记忆总数
        /// </summary>
        [SerializeField]
        public int total;

        /// <summary>
        /// 是否成功
        /// </summary>
        [SerializeField]
        public bool success;

        /// <summary>
        /// 错误信息
        /// </summary>
        [SerializeField]
        public string error;
    }

    /// <summary>
    /// 记忆请求数据类
    /// </summary>
    [Serializable]
    public class RememberRequest
    {
        /// <summary>
        /// 实体类型（player, npc, item 等）
        /// </summary>
        [SerializeField]
        public string entity_type;

        /// <summary>
        /// 实体名称
        /// </summary>
        [SerializeField]
        public string entity_name;

        /// <summary>
        /// 关系类型
        /// </summary>
        [SerializeField]
        public string relation;

        /// <summary>
        /// 备注信息
        /// </summary>
        [SerializeField]
        public string note;

        /// <summary>
        /// 创建记忆请求
        /// </summary>
        public RememberRequest(string entityType, string entityName, string relation = null, string note = null)
        {
            this.entity_type = entityType;
            this.entity_name = entityName;
            this.relation = relation ?? "neutral";
            this.note = note;
        }
    }

    /// <summary>
    /// 记忆请求响应
    /// </summary>
    [Serializable]
    public class RememberResponse
    {
        /// <summary>
        /// 创建的记忆
        /// </summary>
        [SerializeField]
        public Memory memory;

        /// <summary>
        /// 是否成功
        /// </summary>
        [SerializeField]
        public bool success;

        /// <summary>
        /// 错误信息
        /// </summary>
        [SerializeField]
        public string error;
    }
}
