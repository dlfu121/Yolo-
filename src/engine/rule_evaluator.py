import numpy as np


class RuleEvaluator:
    """规则评估引擎"""
    
    def __init__(self, config):
        """
        初始化规则评估器
        
        Args:
            config (dict): 动作配置字典
        """
        self.config = config
        self.deductions = []
        self.score = 100
    
    def evaluate_rep(self, rep_data):
        """
        评估单次动作
        
        Args:
            rep_data (dict): 单次动作数据
                {
                    'elbow_angles': [...],
                    'eccentric_duration': frames,
                    'concentric_duration': frames,
                    'arm_deviation': [...],
                    'wrist_movement': [...],
                    'state_sequence': [...]
                }
        
        Returns:
            dict: 评估结果
                {
                    'score': int (0-100),
                    'is_valid': bool,
                    'deductions': [(issue_name, deduction_points), ...]
                }
        """
        self.score = 100
        self.deductions = []
        
        # 检查离心速度（速度过快）
        ecc_frames = rep_data.get('eccentric_duration', 0)
        if ecc_frames > 0 and ecc_frames < self.config['timing']['eccentric_min_frames']:
            self._deduct("speed_too_fast", 15)
        
        # 检查大臂偏离
        arm_deviations = rep_data.get('arm_deviation', [])
        if arm_deviations and max(arm_deviations) > self.config['thresholds']['arm_deviation']:
            self._deduct("arm_deviation", 10)
        
        # 检查腕部稳定性
        wrist_movements = rep_data.get('wrist_movement', [])
        if wrist_movements and max(wrist_movements) > self.config['thresholds']['wrist_stability']:
            self._deduct("wrist_movement", 8)
        
        # 检查活动范围
        elbow_angles = rep_data.get('elbow_angles', [])
        if elbow_angles:
            min_angle = np.nanmin(elbow_angles)
            if min_angle > self.config['thresholds']['elbow_flexion']:
                self._deduct("incomplete_range", 20)
        
        # 检查离心控制
        if ecc_frames > 0 and ecc_frames > self.config['timing']['eccentric_max_frames']:
            self._deduct("uncontrolled_descent", 15)
        
        self.score = max(0, self.score)
        is_valid = self.score >= self.config['validity']['min_score']
        
        return {
            'score': self.score,
            'is_valid': is_valid,
            'deductions': self.deductions,
            'feedback': self._generate_feedback()
        }
    
    def _deduct(self, issue_name, points):
        """扣分"""
        self.deductions.append((issue_name, points))
        self.score -= points
    
    def _generate_feedback(self):
        """根据扣分生成反馈信息"""
        feedback = []
        deduction_names = {
            'speed_too_fast': '下放速度过快，缺乏控制',
            'arm_deviation': '大臂脱离躯干，存在借力',
            'wrist_movement': '腕部活动，应保持稳定',
            'incomplete_range': '活动范围不足，未充分收缩',
            'uncontrolled_descent': '下放过慢，节奏控制不佳',
        }
        
        for issue, _ in self.deductions:
            if issue in deduction_names:
                feedback.append(deduction_names[issue])
        
        return feedback
