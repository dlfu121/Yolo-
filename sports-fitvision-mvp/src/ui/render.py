import cv2
import numpy as np


class PoseRenderer:
    """姿态渲染器"""
    
    # YOLOv8-Pose 标准的骨架连接关系
    SKELETON_PAIRS = [
        (0, 1), (0, 2), (1, 3), (2, 4),  # 头部
        (5, 6),  # 肩膀连线
        (5, 7), (7, 9),  # 右臂：肩-肘-腕
        (6, 8), (8, 10),  # 左臂：肩-肘-腕
        (5, 11), (6, 12),  # 躯干：肩-髋
        (11, 12),  # 髋
        (11, 13), (13, 15),  # 右腿：髋-膝-踝
        (12, 14), (14, 16),  # 左腿：髋-膝-踝
    ]
    
    def __init__(self, config=None):
        """
        初始化渲染器
        
        Args:
            config (dict): 配置字典
        """
        self.config = config or {}
    
    def draw_skeleton(self, frame, keypoints, confidences, threshold=0.5):
        """
        绘制骨架（连线和关键点）
        
        Args:
            frame (ndarray): 原始帧
            keypoints (ndarray): 关键点坐标 shape=(17, 2)
            confidences (ndarray): 置信度 shape=(17,)
            threshold (float): 置信度阈值
            
        Returns:
            ndarray: 绘制后的帧
        """
        frame = frame.copy()
        
        # 绘制骨架连线
        for (i, j) in self.SKELETON_PAIRS:
            if keypoints[i] is not None and keypoints[j] is not None:
                if confidences[i] > threshold and confidences[j] > threshold:
                    pt1 = tuple(map(int, keypoints[i]))
                    pt2 = tuple(map(int, keypoints[j]))
                    cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
        
        # 绘制关键点圆圈
        for i, kpt in enumerate(keypoints):
            if kpt is not None and confidences[i] > threshold:
                pt = tuple(map(int, kpt))
                cv2.circle(frame, pt, 5, (0, 255, 0), -1)
        
        return frame
    
    def draw_hud(self, frame, state, rep_count, valid_rep_count, 
                 elbow_angle, score, warnings, frame_idx=0, fps=None):
        """
        绘制 HUD（仪表板）
        
        Args:
            frame (ndarray): 原始帧
            state: 当前动作状态
            rep_count (int): 总次数
            valid_rep_count (int): 有效次数
            elbow_angle (float): 肘关节角度
            score (float): 当前动作得分
            warnings (list): 警告信息列表
            frame_idx (int): 当前帧编号
            
        Returns:
            ndarray: 绘制后的帧
        """
        frame = frame.copy()
        h, w = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # 左上角：状态和计数
        cv2.putText(frame, f"State: {state.value.upper()}", (20, 40), 
                   font, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Reps: {rep_count} | Valid: {valid_rep_count}", 
                   (20, 80), font, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {frame_idx}", 
                   (20, 120), font, 0.6, (200, 200, 200), 1)

        if fps is not None:
            cv2.putText(frame, f"FPS: {fps:.1f}", 
                       (20, 150), font, 0.6, (0, 255, 255), 2)
        
        # 右上角：角度和得分
        angle_color = (255, 255, 0)  # 黄色
        cv2.putText(frame, f"Elbow: {elbow_angle:.1f}°", 
                   (w - 300, 40), font, 0.8, angle_color, 2)
        
        score_color = (0, 255, 0) if score >= 70 else (0, 0, 255)  # 绿或红
        cv2.putText(frame, f"Score: {score:.0f}/100", 
                   (w - 300, 80), font, 0.8, score_color, 2)
        
        # 下方：警告信息
        if warnings:
            y_offset = h - 30
            for warning in warnings[-3:]:  # 显示最后 3 个警告
                color = (0, 0, 255)  # 红色
                cv2.putText(frame, f"⚠ {warning}", (20, y_offset), 
                           font, 0.6, color, 2)
                y_offset -= 30
        
        # 绘制状态条
        self._draw_state_bar(frame, state)
        
        return frame
    
    @staticmethod
    def _draw_state_bar(frame, state):
        """绘制状态指示条"""
        h, w = frame.shape[:2]
        state_colors = {
            'idle': (100, 100, 100),
            'preparation': (150, 150, 0),
            'eccentric': (255, 165, 0),
            'bottom': (255, 0, 0),
            'concentric': (255, 100, 100),
            'top': (0, 255, 0),
        }
        color = state_colors.get(state.value, (128, 128, 128))
        
        bar_height = 20
        cv2.rectangle(frame, (0, 0), (w, bar_height), color, -1)
        cv2.putText(frame, f"  {state.value.upper()}", (10, 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    @staticmethod
    def highlight_error_joints(frame, error_joint_indices, keypoints, confidences):
        """
        高亮错误的关键点（红色闪烁）
        
        Args:
            frame (ndarray): 原始帧
            error_joint_indices (list): 错误关键点的索引
            keypoints (ndarray): 关键点坐标
            confidences (ndarray): 置信度
            
        Returns:
            ndarray: 绘制后的帧
        """
        frame = frame.copy()
        
        for idx in error_joint_indices:
            if keypoints[idx] is not None and confidences[idx] > 0.5:
                pt = tuple(map(int, keypoints[idx]))
                cv2.circle(frame, pt, 8, (0, 0, 255), 3)  # 红色粗圆
        
        return frame
