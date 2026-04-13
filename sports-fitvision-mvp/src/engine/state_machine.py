from enum import Enum


class RepState(Enum):
    """二头肌弯举的动作状态"""
    IDLE = "idle"
    PREPARATION = "preparation"
    ECCENTRIC = "eccentric"
    BOTTOM = "bottom"
    CONCENTRIC = "concentric"
    TOP = "top"
    INVALID = "invalid"


class BicepCurlStateMachine:
    """二头肌弯举状态机"""
    
    def __init__(self, config):
        """
        初始化状态机
        
        Args:
            config (dict): 动作配置字典
        """
        self.config = config
        self.state = RepState.IDLE
        self.frame_counter = 0
        self.state_start_frame = 0
        self.rep_count = 0
        self.valid_rep_count = 0
        self.current_rep_data = {}
    
    def update(self, elbow_angle, elbow_confidence, is_arm_away, is_wrist_stable):
        """
        状态机更新逻辑
        
        Args:
            elbow_angle (float): 肘关节角度
            elbow_confidence (float): 肘部置信度
            is_arm_away (bool): 大臂是否脱离躯干
            is_wrist_stable (bool): 腕部是否稳定
            
        Returns:
            RepState: 当前状态
        """
        self.frame_counter += 1
        
        # 置信度过低，保持当前状态
        confidence_threshold = self.config.get('pose_detection', {}).get('confidence_threshold', 0.5)
        if elbow_confidence < confidence_threshold:
            return self.state
        
        # 状态转移逻辑
        old_state = self.state
        
        if self.state == RepState.IDLE:
            new_state = self._from_idle(elbow_angle)
        elif self.state == RepState.PREPARATION:
            new_state = self._from_preparation(elbow_angle)
        elif self.state == RepState.ECCENTRIC:
            new_state = self._from_eccentric(elbow_angle)
        elif self.state == RepState.BOTTOM:
            new_state = self._from_bottom(elbow_angle)
        elif self.state == RepState.CONCENTRIC:
            new_state = self._from_concentric(elbow_angle)
        elif self.state == RepState.TOP:
            new_state = self._from_top(elbow_angle)
        else:
            new_state = self.state
        
        # 状态变化回调
        if new_state != old_state:
            self._on_state_change(old_state, new_state)
            self.state = new_state
            self.state_start_frame = self.frame_counter
        
        return self.state
    
    def _from_idle(self, elbow_angle):
        """静止 → 准备"""
        threshold = self.config['thresholds']['elbow_extension']
        if elbow_angle > threshold - 10:
            return RepState.PREPARATION
        return RepState.IDLE
    
    def _from_preparation(self, elbow_angle):
        """准备 → 离心（开始弯举）"""
        if elbow_angle < self.config['thresholds']['elbow_extension'] - 20:
            return RepState.ECCENTRIC
        return RepState.PREPARATION
    
    def _from_eccentric(self, elbow_angle):
        """离心 → 最低点"""
        flexion = self.config['thresholds']['elbow_flexion']
        if elbow_angle < flexion - 5:
            return RepState.BOTTOM
        return RepState.ECCENTRIC
    
    def _from_bottom(self, elbow_angle):
        """最低点 → 向心（开始上提）"""
        if elbow_angle < self.config['thresholds']['elbow_flexion']:
            return RepState.CONCENTRIC
        return RepState.BOTTOM
    
    def _from_concentric(self, elbow_angle):
        """向心 → 顶点（快要完全收缩）"""
        flexion_min = self.config['thresholds']['elbow_flexion_min']
        if elbow_angle < flexion_min:
            return RepState.TOP
        return RepState.CONCENTRIC
    
    def _from_top(self, elbow_angle):
        """顶点 → 回到准备或完成一次"""
        extension = self.config['thresholds']['elbow_extension']
        if elbow_angle > extension - 10:
            self.rep_count += 1
            return RepState.PREPARATION
        return RepState.TOP
    
    def _on_state_change(self, old_state, new_state):
        """状态变化时的回调（用于调试）"""
        print(f"[StateMachine] 状态变化: {old_state.value} → {new_state.value} (第 {self.rep_count + 1} 次)")
    
    def get_stage_duration(self):
        """获取当前阶段的持续帧数"""
        return self.frame_counter - self.state_start_frame
