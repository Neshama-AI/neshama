namespace Neshama.SDK.Enums
{
    /// <summary>
    /// 游戏事件类型枚举，与后端 game_event.py 中的事件类型完全对齐
    /// 用于描述游戏中发生的各类事件，NPC会根据事件类型调整情绪和行为
    /// </summary>
    public enum GameEventType
    {
        /// <summary>玩家进入NPC视野范围</summary>
        player_entered,
        
        /// <summary>玩家离开NPC视野范围</summary>
        player_left,
        
        /// <summary>玩家攻击了NPC</summary>
        player_attacked,
        
        /// <summary>NPC被治愈</summary>
        npc_healed,
        
        /// <summary>NPC受到伤害</summary>
        npc_damaged,
        
        /// <summary>NPC被赞美</summary>
        npc_complimented,
        
        /// <summary>NPC被侮辱</summary>
        npc_insulted,
        
        /// <summary>NPC收到礼物</summary>
        gift_given,
        
        /// <summary>玩家帮助了NPC</summary>
        npc_helped,
        
        /// <summary>玩家与NPC交易</summary>
        trade_completed,
        
        /// <summary>NPC目睹战斗开始</summary>
        combat_started,
        
        /// <summary>NPC目睹战斗结束</summary>
        combat_ended,
        
        /// <summary>玩家完成了NPC的任务</summary>
        quest_completed,
        
        /// <summary>玩家接受了NPC的任务</summary>
        quest_accepted,
        
        /// <summary>玩家任务失败</summary>
        quest_failed
    }
}
