from ultralytics import YOLO
import numpy as np
import torch


class PoseDetector:
    """YOLOv8-Pose 姿态检测器"""
    
    def __init__(self, model_name="yolov8m-pose", device=0):
        """
        初始化 YOLOv8-Pose 检测器
        
        Args:
            model_name (str): 模型大小 (n, s, m, l, x)
            device (int): GPU 设备号
        """
        print(f"[PoseDetector] 加载模型 {model_name}...")
        self.model = YOLO(model_name)
        
        # 自动检测可用设备
        if torch.cuda.is_available():
            try:
                self.model.to(device)
                print(f"[PoseDetector] ✓ 模型已加载到 GPU {device}")
                self.device = device
            except RuntimeError as e:
                print(f"[PoseDetector] ⚠ GPU 加载失败: {e}")
                print(f"[PoseDetector] 切换到 CPU 推理")
                self.model.to('cpu')
                self.device = 'cpu'
        else:
            print(f"[PoseDetector] ⚠ 未检测到 GPU，使用 CPU 推理（速度会变慢）")
            self.model.to('cpu')
            self.device = 'cpu'
    
    def detect(self, frame):
        """
        对单帧进行姿态检测
        
        Args:
            frame: OpenCV 读取的 RGB 帧
            
        Returns:
            keypoints (ndarray): 关键点坐标 shape=(N_people, 17, 2)
            confidences (ndarray): 置信度 shape=(N_people, 17)
        """
        results = self.model(frame, verbose=False)
        keypoints = results[0].keypoints.xy.cpu().numpy()  # (N, 17, 2)
        confidences = results[0].keypoints.conf.cpu().numpy()  # (N, 17)
        return keypoints, confidences
    
    @staticmethod
    def filter_by_confidence(keypoints, confidences, threshold=0.5):
        """
        过滤低置信度关键点
        
        Args:
            keypoints (ndarray): 关键点坐标
            confidences (ndarray): 置信度
            threshold (float): 置信度阈值
            
        Returns:
            keypoints_filtered (ndarray): 过滤后的关键点（低置信度设为 NaN）
            mask (ndarray): 低置信度掩码
        """
        keypoints_filtered = keypoints.copy()
        mask = confidences < threshold
        # 将低置信度按点标记为 NaN
        for i in range(len(keypoints_filtered)):
            for j in range(len(confidences[i])):
                if confidences[i, j] < threshold:
                    keypoints_filtered[i, j] = np.nan
        return keypoints_filtered, mask
