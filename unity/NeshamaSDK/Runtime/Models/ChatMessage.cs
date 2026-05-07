using System;
using System.Collections.Generic;
using UnityEngine;

namespace Neshama.SDK.Models
{
    /// <summary>
    /// 对话消息数据类
    /// 用于描述玩家发送的消息和NPC的回复
    /// </summary>
    [Serializable]
    public class ChatMessage
    {
        /// <summary>
        /// 消息内容
        /// </summary>
        [SerializeField]
        public string message;

        /// <summary>
        /// 发送者ID
        /// </summary>
        [SerializeField]
        public string sender_id;

        /// <summary>
        /// 接收者ID
        /// </summary>
        [SerializeField]
        public string receiver_id;

        /// <summary>
        /// 消息发送时间戳
        /// </summary>
        [SerializeField]
        public long timestamp;

        /// <summary>
        /// 消息类型（player/npc/system）
        /// </summary>
        [SerializeField]
        public string type;

        /// <summary>
        /// 创建一条玩家消息
        /// </summary>
        /// <param name="content">消息内容</param>
        /// <param name="playerId">玩家ID</param>
        /// <param name="npcId">NPC ID</param>
        public ChatMessage(string content, string playerId, string npcId)
        {
            this.message = content;
            this.sender_id = playerId;
            this.receiver_id = npcId;
            this.timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            this.type = "player";
        }

        public override string ToString()
        {
            return $"ChatMessage: [{type}] {sender_id} -> {receiver_id}: {message}";
        }
    }

    /// <summary>
    /// 对话请求数据类
    /// </summary>
    [Serializable]
    public class ChatRequest
    {
        /// <summary>
        /// 玩家发送的消息内容
        /// </summary>
        [SerializeField]
        public string message;

        /// <summary>
        /// 玩家ID
        /// </summary>
        [SerializeField]
        public string player_id;

        /// <summary>
        /// 创建对话请求
        /// </summary>
        /// <param name="message">消息内容</param>
        /// <param name="playerId">玩家ID</param>
        public ChatRequest(string message, string playerId)
        {
            this.message = message;
            this.player_id = playerId;
        }
    }

    /// <summary>
    /// 对话响应数据类
    /// </summary>
    [Serializable]
    public class ChatResponse
    {
        /// <summary>
        /// NPC的回复内容
        /// </summary>
        [SerializeField]
        public string content;

        /// <summary>
        /// 回复后的情绪状态
        /// </summary>
        [SerializeField]
        public EmotionState emotion_after;

        /// <summary>
        /// 回复的紧迫程度
        /// </summary>
        [SerializeField]
        public string urgency;

        /// <summary>
        /// 建议的后续动作
        /// </summary>
        [SerializeField]
        public List<string> suggested_actions;

        /// <summary>
        /// 是否成功获取回复
        /// </summary>
        [SerializeField]
        public bool success;

        /// <summary>
        /// 错误信息（如果有）
        /// </summary>
        [SerializeField]
        public string error;

        /// <summary>
        /// 获取NPC回复内容
        /// </summary>
        public string GetResponse()
        {
            return content ?? (success ? "..." : error);
        }

        /// <summary>
        /// 判断是否应该结束对话
        /// </summary>
        public bool ShouldEndConversation()
        {
            return suggested_actions != null && suggested_actions.Contains("end_conversation");
        }

        /// <summary>
        /// 判断是否应该提供更多信息
        /// </summary>
        public bool ShouldShareInfo()
        {
            return suggested_actions != null && suggested_actions.Contains("share_info");
        }

        public override string ToString()
        {
            return $"ChatResponse: {content?.Substring(0, Math.Min(50, content.Length))}...";
        }
    }

    /// <summary>
    /// 对话响应事件参数
    /// </summary>
    public class ChatResponseEventArgs
    {
        public string NpcId { get; set; }
        public string PlayerId { get; set; }
        public string Response { get; set; }
        public EmotionState EmotionState { get; set; }
        public string Urgency { get; set; }
    }
}
