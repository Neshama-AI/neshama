namespace Neshama.SDK.Enums
{
    /// <summary>
    /// 行为修改类型枚举，用于描述NPC行为的变化
    /// </summary>
    public enum BehaviorType
    {
        /// <summary>对话风格改变（如变得冷淡、热情等）</summary>
        dialogue_style_change,
        
        /// <summary>任务可用性改变（如锁定/解锁任务）</summary>
        quest_availability_change,
        
        /// <summary>商店价格调整</summary>
        shop_price_modifier,
        
        /// <summary>移动速度改变</summary>
        movement_speed_change,
        
        /// <summary>AI行为模式改变</summary>
        ai_behavior_change
    }
}
