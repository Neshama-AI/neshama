using System;
using System.Collections.Generic;
using UnityEngine;

namespace Neshama.SDK.Models
{
    /// <summary>
    /// NPC档案数据类
    /// 包含NPC的基本信息、人格设定等
    /// </summary>
    [Serializable]
    public class NPCProfile
    {
        /// <summary>
        /// NPC名称
        /// </summary>
        [SerializeField]
        public string name;

        /// <summary>
        /// NPC唯一标识符
        /// </summary>
        [SerializeField]
        public string npc_id;

        /// <summary>
        /// NPC预设模板类型（如 tavern_keeper, guard_captain 等）
        /// </summary>
        [SerializeField]
        public string preset;

        /// <summary>
        /// 人格特质描述
        /// </summary>
        [SerializeField]
        public Personality personality;

        /// <summary>
        /// 创建时间
        /// </summary>
        [SerializeField]
        public string created_at;

        /// <summary>
        /// 最后更新时间
        /// </summary>
        [SerializeField]
        public string updated_at;

        /// <summary>
        /// 额外元数据（运行时使用，不参与JSON序列化）
        /// </summary>
        [System.NonSerialized]
        public Dictionary<string, object> metadata;

        /// <summary>
        /// 获取NPC显示名称
        /// </summary>
        public string GetDisplayName()
        {
            return string.IsNullOrEmpty(name) ? "Unknown NPC" : name;
        }

        /// <summary>
        /// 获取NPC的预设类型
        /// </summary>
        public string GetPresetType()
        {
            return preset ?? "default";
        }

        public override string ToString()
        {
            return $"NPCProfile: {name} (ID: {npc_id}, Preset: {preset})";
        }
    }

    /// <summary>
    /// 人格特质数据类
    /// </summary>
    [Serializable]
    public class Personality
    {
        /// <summary>
        /// 主要性格标签列表
        /// </summary>
        [SerializeField]
        public List<string> traits;

        /// <summary>
        /// 说话风格描述
        /// </summary>
        [SerializeField]
        public string speaking_style;

        /// <summary>
        /// 价值观描述
        /// </summary>
        [SerializeField]
        public List<string> values;

        /// <summary>
        /// 背景故事
        /// </summary>
        [SerializeField]
        public string backstory;

        /// <summary>
        /// 目标/动机描述
        /// </summary>
        [SerializeField]
        public List<string> goals;

        /// <summary>
        /// 获取第一个性格标签
        /// </summary>
        public string GetPrimaryTrait()
        {
            return traits != null && traits.Count > 0 ? traits[0] : "neutral";
        }

        /// <summary>
        /// 获取NPC的默认对话风格
        /// </summary>
        public string GetDefaultDialogueStyle()
        {
            return speaking_style ?? "friendly";
        }

        public override string ToString()
        {
            return $"Personality: {string.Join(", ", traits ?? new List<string>())}";
        }
    }

    /// <summary>
    /// 创建NPC的请求数据类
    /// </summary>
    [Serializable]
    public class CreateNPCRequest
    {
        /// <summary>
        /// NPC名称
        /// </summary>
        [SerializeField]
        public string name;

        /// <summary>
        /// 预设模板类型
        /// </summary>
        [SerializeField]
        public string preset;

        /// <summary>
        /// 额外配置（运行时使用，不参与JSON序列化）
        /// </summary>
        [System.NonSerialized]
        public Dictionary<string, object> config;

        /// <summary>
        /// 创建NPC请求
        /// </summary>
        /// <param name="name">NPC名称</param>
        /// <param name="preset">预设类型</param>
        public CreateNPCRequest(string name, string preset)
        {
            this.name = name;
            this.preset = preset;
            this.config = new Dictionary<string, object>();
        }

        /// <summary>
        /// 创建NPC请求（带额外配置）
        /// </summary>
        public CreateNPCRequest(string name, string preset, Dictionary<string, object> config)
        {
            this.name = name;
            this.preset = preset;
            this.config = config ?? new Dictionary<string, object>();
        }
    }

    /// <summary>
    /// 创建NPC的响应数据类
    /// </summary>
    [Serializable]
    public class CreateNPCResponse
    {
        /// <summary>
        /// 创建的NPC ID
        /// </summary>
        [SerializeField]
        public string npc_id;

        /// <summary>
        /// NPC档案
        /// </summary>
        [SerializeField]
        public NPCProfile profile;

        /// <summary>
        /// 是否创建成功
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
