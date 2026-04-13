import numpy as np


class AngleCalculator:
    """角度和距离计算工具类"""
    
    @staticmethod
    def angle_between_three_points(p1, p2, p3):
        """
        计算三点形成的角度 (p1-p2-p3 的夹角)
        使用向量点积和叉积
        
        Args:
            p1, p2, p3 (array): 三个点的坐标 (x, y)
            
        Returns:
            float: 角度 (0-180 度)
        """
        v1 = p1 - p2
        v2 = p3 - p2
        
        len_v1 = np.linalg.norm(v1)
        len_v2 = np.linalg.norm(v2)
        
        if len_v1 < 1e-6 or len_v2 < 1e-6:
            return 90.0
        
        cos_angle = np.dot(v1, v2) / (len_v1 * len_v2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle) * 180 / np.pi
        return angle
    
    @staticmethod
    def distance_between_points(p1, p2):
        """
        计算两点欧式距离
        
        Args:
            p1, p2 (array): 两个点的坐标
            
        Returns:
            float: 欧式距离（像素）
        """
        return np.linalg.norm(p1 - p2)
    
    @staticmethod
    def horizontal_deviation(shoulder, elbow):
        """
        计算肘部相对肩膀的水平偏离度
        用于检测"大臂脱离躯干"
        
        Args:
            shoulder (array): 肩膀位置 (x, y)
            elbow (array): 肘部位置 (x, y)
            
        Returns:
            float: 水平偏离距离（像素）
        """
        deviation = abs(elbow[0] - shoulder[0])
        return deviation
    
    @staticmethod
    def velocity(p_prev, p_curr, fps=30):
        """
        计算运动速度（像素/秒）
        
        Args:
            p_prev, p_curr (array): 前后两帧坐标
            fps (int): 帧率
            
        Returns:
            float: 速度（像素/秒）
        """
        pixel_distance = np.linalg.norm(p_curr - p_prev)
        velocity = pixel_distance * fps
        return velocity
    
    @staticmethod
    def coordinate_variance(coords_list):
        """
        计算坐标序列的方差（用于检测稳定性）
        
        Args:
            coords_list (list): 多帧坐标列表
            
        Returns:
            float: 坐标方差
        """
        coords_array = np.array(coords_list)
        return np.nanvar(coords_array, axis=0).mean()
