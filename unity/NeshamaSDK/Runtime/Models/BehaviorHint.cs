using System;
using System.Collections.Generic;
using UnityEngine;

namespace Neshama.SDK.Models
{
    /// <summary>
    /// 行为建议数据类
    /// 描述NPC应该采取的行为修改
    /// </summary>
    [Serializable]
    public class BehaviorHint
    {
        /// <summary>
        /// 行为类型（如 dialogue_style_change, quest_availability_change 等）
        /// </summary>
        [SerializeField]
        public string type;

        /// <summary>
        /// 行为值（如 "hostile", "locked", "unlocked" 等）
        /// </summary>
        [SerializeField]
        public string value;

        /// <summary>
        /// 行为强度/优先级，可选
        /// </summary>
        [SerializeField]
        public float strength;

        /// <summary>
        /// 建议的行为动作列表（如 refuse_conversation, share_info 等）
        /// </summary>
        [SerializeField]
        public List<string> suggested_actions;

        /// <summary>
        /// 获取行为类型枚举
        /// </summary>
        public Enums.BehaviorType GetBehaviorType()
        {
            if (string.IsNullOrEmpty(type)) return Enums.BehaviorType.dialogue_style_change;
            
            try
            {
                return (Enums.BehaviorType)Enum.Parse(typeof(Enums.BehaviorType), type, true);
            }
            catch
            {
                return Enums.BehaviorType.dialogue_style_change;
            }
        }

        /// <summary>
        /// 判断是否为对话风格改变
        /// </summary>
        public bool IsDialogueStyleChange()
        {
            return type == "dialogue_style_change";
        }

        /// <summary>
        /// 获取对话风格（如果这是对话风格改变类型）
        /// </summary>
        public string GetDialogueStyle()
        {
            return IsDialogueStyleChange() ? value : null;
        }

        /// <summary>
        /// 判断是否为任务可用性改变
        /// </summary>
        public bool IsQuestAvailabilityChange()
        {
            return type == "quest_availability_change";
        }

        /// <summary>
        /// 获取任务是否被锁定
        /// </summary>
        public bool IsQuestLocked()
        {
            return IsQuestAvailabilityChange() && value == "locked";
        }

        /// <summary>
        /// 获取任务是否被解锁
        /// </summary>
        public bool IsQuestUnlocked()
        {
            return IsQuestAvailabilityChange() && value == "unlocked";
        }

        public override string ToString()
        {
            return $"BehaviorHint: {type} = {value}";
        }
    }

    /// <summary>
    /// 行为建议响应数据类
    /// </summary>
    [Serializable]
    public class BehaviorResponse
    {
        /// <summary>
        /// 行为修改列表
        /// </summary>
        [SerializeField]
        public List<BehaviorHint> modifiers;

        /// <summary>
        /// 获取所有对话风格改变建议
        /// </summary>
        public List<string> GetDialogueStyleChanges()
        {
            var styles = new List<string>();
            if (modifiers != null)
            {
                foreach (var modifier in modifiers)
                {
                    if (modifier.IsDialogueStyleChange())
                    {
                        styles.Add(modifier.value);
                    }
                }
            }
            return styles;
        }

        /// <summary>
        /// 获取所有任务锁定状态变化
        /// </summary>
        public List<BehaviorHint> GetQuestAvailabilityChanges()
        {
            var changes = new List<BehaviorHint>();
            if (modifiers != null)
            {
                foreach (var modifier in modifiers)
                {
                    if (modifier.IsQuestAvailabilityChange())
                    {
                        changes.Add(modifier);
                    }
                }
            }
            return changes;
        }

        /// <summary>
        /// 判断是否有关闭对话的建议
        /// </summary>
        public bool ShouldRefuseConversation()
        {
            if (modifiers != null)
            {
                foreach (var modifier in modifiers)
                {
                    if (modifier.suggested_actions != null && 
                        modifier.suggested_actions.Contains("refuse_conversation"))
                    {
                        return true;
                    }
                }
            }
            return false;
        }

        public override string ToString()
        {
            return $"BehaviorResponse: {modifiers?.Count ?? 0} modifiers";
        }
    }

    /// <summary>
    /// 行为变更事件参数
    /// </summary>
    public class BehaviorChangedEventArgs
    {
        public string NpcId { get; set; }
        public List<BehaviorHint> Behaviors { get; set; }
    }
}
