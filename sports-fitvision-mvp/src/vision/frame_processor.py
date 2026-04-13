import cv2
import numpy as np
from collections import deque


class FrameProcessor:
    """帧处理器，包含坐标平滑、帧读取等功能"""
    
    def __init__(self, smooth_window=5):
        """
        初始化帧处理器
        
        Args:
            smooth_window (int): 平滑窗口大小
        """
        self.smooth_window = smooth_window
        self.keypoint_history = deque(maxlen=smooth_window)
    
    @staticmethod
    def read_frame(cap):
        """
        从摄像头或视频文件读取帧
        
        Args:
            cap: cv2.VideoCapture 对象
            
        Returns:
            ret (bool): 是否成功读取
            frame (ndarray): 读取的帧
        """
        ret, frame = cap.read()
        return ret, frame
    
    def smooth_keypoints(self, keypoints):
        """
        对关键点坐标进行时间平滑（移动平均）
        
        Args:
            keypoints (ndarray): 当前帧的关键点 shape=(17, 2)
            
        Returns:
            ndarray: 平滑后的关键点
        """
        self.keypoint_history.append(keypoints)
        
        if len(self.keypoint_history) < self.smooth_window:
            return keypoints
        
        history_array = np.array(self.keypoint_history)
        # 使用 nanmean 忽略 NaN 值
        smoothed = np.nanmean(history_array, axis=0)
        return smoothed
