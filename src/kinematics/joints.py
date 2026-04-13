from dataclasses import dataclass
import numpy as np


@dataclass
class Joint:
    """关节信息容器"""
    name: str
    position: np.ndarray  # (x, y)
    confidence: float


class JointManager:
    """管理人体关键关节"""
    
    # YOLOv8-Pose 关键点编号
    KEYPOINT_NAMES = {
        0: "nose", 1: "left_eye", 2: "right_eye",
        3: "left_ear", 4: "right_ear",
        5: "right_shoulder", 6: "left_shoulder",
        7: "right_elbow", 8: "left_elbow",
        9: "right_wrist", 10: "left_wrist",
        11: "right_hip", 12: "left_hip",
        13: "right_knee", 14: "left_knee",
        15: "right_ankle", 16: "left_ankle",
    }
    
    # 弯举相关关键点
    BICEP_CURL_KEYPOINTS = [5, 6, 7, 8, 9, 10]  # 肩膀、肘、腕
    
    def __init__(self, keypoints, confidences, confidence_threshold=0.5):
        """
        初始化关节管理器
        
        Args:
            keypoints (ndarray): 关键点坐标 shape=(17, 2)
            confidences (ndarray): 置信度 shape=(17,)
            confidence_threshold (float): 置信度阈值
        """
        self.keypoints = keypoints
        self.confidences = confidences
        self.confidence_threshold = confidence_threshold
        self.joints = self._extract_joints()
    
    def _extract_joints(self):
        """从检测结果中提取相关关节"""
        joints = {}
        for idx in self.BICEP_CURL_KEYPOINTS:
            name = self.KEYPOINT_NAMES[idx]
            if self.confidences[idx] > self.confidence_threshold:
                joints[name] = Joint(
                    name=name,
                    position=self.keypoints[idx],
                    confidence=self.confidences[idx]
                )
        return joints
    
    def get_side_joints(self, side='right'):
        """
        获取某一侧的关节（左或右）
        
        Args:
            side (str): 'right' 或 'left'
            
        Returns:
            dict: 该侧的关节
        """
        prefix = f"{side}_"
        return {k: v for k, v in self.joints.items() if k.startswith(prefix)}
    
    def is_arm_complete(self, side='right'):
        """
        检查某一侧的手臂是否完整（肩膀、肘、腕都检测到）
        
        Args:
            side (str): 'right' 或 'left'
            
        Returns:
            bool: 是否完整
        """
        required = [f"{side}_shoulder", f"{side}_elbow", f"{side}_wrist"]
        return all(j in self.joints for j in required)
