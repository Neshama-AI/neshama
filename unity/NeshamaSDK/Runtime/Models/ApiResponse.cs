using System;
using System.Collections.Generic;
using UnityEngine;

namespace Neshama.SDK.Models
{
    /// <summary>
    /// 通用API响应包装器
    /// 后端所有响应都使用 {"success": true, "data": {...}} 格式
    /// 由于Unity的JsonUtility不支持泛型反序列化，这里使用具体类型
    /// </summary>

    /// <summary>
    /// NPC创建响应包装器
    /// </summary>
    [Serializable]
    public class CreateNPCApiResponse
    {
        [SerializeField] public bool success;
        [SerializeField] public NPCProfileData data;
        [SerializeField] public string detail;
    }

    /// <summary>
    /// NPC档案数据（从后端data字段提取）
    /// </summary>
    [Serializable]
    public class NPCProfileData
    {
        [SerializeField] public string npc_id;
        [SerializeField] public string name;
        [SerializeField] public string preset;
        [SerializeField] public string created_at;
    }

    /// <summary>
    /// 情绪状态响应包装器
    /// </summary>
    [Serializable]
    public class EmotionApiResponse
    {
        [SerializeField] public bool success;
        [SerializeField] public EmotionApiData data;
        [SerializeField] public string detail;
    }

    /// <summary>
    /// 情绪API数据
    /// </summary>
    [Serializable]
    public class EmotionApiData
    {
        [SerializeField] public string npc_id;
        [SerializeField] public EmotionState emotion_state;
        [SerializeField] public string composite_emotion;
        [SerializeField] public float composite_intensity;
        [SerializeField] public string dominant_emotion;
    }

    /// <summary>
    /// 行为建议响应包装器
    /// </summary>
    [Serializable]
    public class BehaviorApiResponse
    {
        [SerializeField] public bool success;
        [SerializeField] public BehaviorApiData data;
        [SerializeField] public string detail;
    }

    /// <summary>
    /// 行为API数据
    /// </summary>
    [Serializable]
    public class BehaviorApiData
    {
        [SerializeField] public string npc_id;
        [SerializeField] public List<BehaviorHint> modifiers;
    }

    /// <summary>
    /// 事件推送响应包装器
    /// </summary>
    [Serializable]
    public class EventApiResponse
    {
        [SerializeField] public bool success;
        [SerializeField] public EventApiData data;
        [SerializeField] public string detail;
    }

    /// <summary>
    /// 事件API数据
    /// </summary>
    [Serializable]
    public class EventApiData
    {
        [SerializeField] public string npc_id;
        [SerializeField] public EmotionState emotion_state;
        [SerializeField] public ResponseHint response_hint;
    }

    /// <summary>
    /// 对话响应包装器
    /// </summary>
    [Serializable]
    public class ChatApiResponse
    {
        [SerializeField] public bool success;
        [SerializeField] public ChatApiData data;
        [SerializeField] public string detail;
    }

    /// <summary>
    /// 对话API数据
    /// </summary>
    [Serializable]
    public class ChatApiData
    {
        [SerializeField] public string npc_id;
        [SerializeField] public string npc_name;
        [SerializeField] public string message_received;
        [SerializeField] public ChatFormattedResponse formatted_response;
        [SerializeField] public EmotionState emotion_context;
        [SerializeField] public BehaviorApiData behavior_context;
    }

    /// <summary>
    /// 格式化对话响应
    /// </summary>
    [Serializable]
    public class ChatFormattedResponse
    {
        [SerializeField] public string clean;
        [SerializeField] public string convert;
        [SerializeField] public string note;
    }

    /// <summary>
    /// NPC档案响应包装器
    /// </summary>
    [Serializable]
    public class ProfileApiResponse
    {
        [SerializeField] public bool success;
        [SerializeField] public NPCProfileData data;
        [SerializeField] public string detail;
    }

    /// <summary>
    /// 记忆响应包装器
    /// </summary>
    [Serializable]
    public class MemoryApiResponse
    {
        [SerializeField] public bool success;
        [SerializeField] public MemoryApiData data;
        [SerializeField] public string detail;
    }

    /// <summary>
    /// 记忆API数据
    /// </summary>
    [Serializable]
    public class MemoryApiData
    {
        [SerializeField] public string npc_id;
        [SerializeField] public string entity_id;
        [SerializeField] public List<RelationData> relations;
    }

    /// <summary>
    /// 关系数据（简化版，用于记忆API）
    /// </summary>
    [Serializable]
    public class RelationData
    {
        [SerializeField] public string from;
        [SerializeField] public string to;
        [SerializeField] public string relation_type;
        [SerializeField] public float weight;
    }

    /// <summary>
    /// 记住实体响应包装器
    /// </summary>
    [Serializable]
    public class RememberApiResponse
    {
        [SerializeField] public bool success;
        [SerializeField] public RememberApiData data;
        [SerializeField] public string detail;
    }

    /// <summary>
    /// 记住API数据
    /// </summary>
    [Serializable]
    public class RememberApiData
    {
        [SerializeField] public string npc_id;
        [SerializeField] public string entity_id;
        [SerializeField] public string relation_type;
        [SerializeField] public float weight;
    }

    /// <summary>
    /// 关系图谱响应包装器
    /// </summary>
    [Serializable]
    public class RelationsApiResponse
    {
        [SerializeField] public bool success;
        [SerializeField] public RelationsApiData data;
        [SerializeField] public string detail;
    }

    /// <summary>
    /// 关系API数据
    /// </summary>
    [Serializable]
    public class RelationsApiData
    {
        [SerializeField] public string npc_id;
        [SerializeField] public List<RelationData> relations;
        [SerializeField] public int count;
    }

    // 注意: 需要在文件顶部添加 using System.Collections.Generic;
    // 但Unity的JsonUtility不支持Dictionary，List<T>需要显式声明
}
