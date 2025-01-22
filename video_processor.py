import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QLineEdit, QSlider, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PIL import Image
import os


class VideoProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.video_path = ''
        self.lut_path = ''
        self.cap = None
        self.total_frames = 0
        self.fps = 0
        self.current_frame = None
        self.load_state()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_playing = False
        self.playback_speed = 1.0

    def initUI(self):
        self.setWindowTitle('视频处理工具')
        self.setGeometry(100, 100, 800, 600)

        # 创建主窗口部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 360)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.video_label)

        # 预览区域布局
        preview_layout = QHBoxLayout()

        # 图片预览区布局
        image_preview_layout = QVBoxLayout()
        self.image_preview = QLabel()
        self.image_preview.setMinimumSize(320, 180)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_preview_layout.addWidget(self.image_preview)

        # 删除按钮
        self.delete_frame_btn = QPushButton('删除')
        self.delete_frame_btn.clicked.connect(self.delete_frame)
        self.delete_frame_btn.setVisible(False)
        image_preview_layout.addWidget(self.delete_frame_btn)
        preview_layout.addLayout(image_preview_layout)

        # LUT预览区
        self.lut_preview = QLabel()
        self.lut_preview.setMinimumSize(320, 180)
        self.lut_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.lut_preview)

        layout.addLayout(preview_layout)

        # 进度条
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.slider_changed)
        layout.addWidget(self.slider)

        # 播放控制区域
        playback_layout = QHBoxLayout()

        # 播放/暂停按钮
        self.play_btn = QPushButton('播放')
        self.play_btn.clicked.connect(self.toggle_play)
        playback_layout.addWidget(self.play_btn)

        # 倍速控制下拉框
        self.speed_combo = QComboBox()
        speeds = ['0.5x', '1.0x', '1.5x', '2.0x', '3.0x']
        self.speed_combo.addItems(speeds)
        self.speed_combo.setCurrentText('1.0x')
        self.speed_combo.currentTextChanged.connect(self.speed_changed)
        playback_layout.addWidget(self.speed_combo)

        layout.addLayout(playback_layout)

        # 控制按钮区域
        controls_layout = QHBoxLayout()

        # 选择视频按钮
        self.select_video_btn = QPushButton('选择视频')
        self.select_video_btn.clicked.connect(self.select_video)
        controls_layout.addWidget(self.select_video_btn)

        # 选择LUT按钮
        self.select_lut_btn = QPushButton('选择LUT')
        self.select_lut_btn.clicked.connect(self.select_lut)
        controls_layout.addWidget(self.select_lut_btn)

        # 时间戳输入框和确认按钮布局
        timestamp_layout = QHBoxLayout()
        self.timestamp_input = QLineEdit()
        self.timestamp_input.setPlaceholderText('输入时间戳（秒）')
        timestamp_layout.addWidget(self.timestamp_input)

        # 确认时间戳按钮
        self.confirm_timestamp_btn = QPushButton('确认')
        self.confirm_timestamp_btn.clicked.connect(self.confirm_timestamp)
        timestamp_layout.addWidget(self.confirm_timestamp_btn)
        controls_layout.addLayout(timestamp_layout)

        # 截帧按钮
        self.capture_btn = QPushButton('截帧')
        self.capture_btn.clicked.connect(self.capture_frame)
        controls_layout.addWidget(self.capture_btn)

        # 应用LUT按钮
        self.apply_lut_btn = QPushButton('应用LUT')
        self.apply_lut_btn.clicked.connect(self.apply_lut)
        self.apply_lut_btn.setVisible(False)
        controls_layout.addWidget(self.apply_lut_btn)

        # 导出原始图片按钮
        self.export_original_btn = QPushButton('导出原图')
        self.export_original_btn.clicked.connect(self.export_original)
        self.export_original_btn.setVisible(False)
        controls_layout.addWidget(self.export_original_btn)

        # 导出LUT图片按钮
        self.export_lut_btn = QPushButton('导出LUT图')
        self.export_lut_btn.clicked.connect(self.export_lut)
        self.export_lut_btn.setVisible(False)
        controls_layout.addWidget(self.export_lut_btn)

        layout.addLayout(controls_layout)

    def load_state(self):
        try:
            if os.path.exists('app_state.txt'):
                with open('app_state.txt', 'r') as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        self.video_path = lines[0].strip()
                        self.lut_path = lines[1].strip()
                        if os.path.exists(self.video_path):
                            self.load_video()
        except Exception as e:
            print(f'加载状态失败: {e}')

    def save_state(self):
        try:
            with open('app_state.txt', 'w') as f:
                f.write(f'{self.video_path}\n')
                f.write(f'{self.lut_path}\n')
        except Exception as e:
            print(f'保存状态失败: {e}')

    def select_video(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择视频文件', '',
                                                   'Video Files (*.mp4 *.avi *.mkv)')
        if file_name:
            self.video_path = file_name
            self.load_video()
            self.save_state()

    def select_lut(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择LUT文件', '',
                                                   'LUT Files (*.cube)')
        if file_name:
            self.lut_path = file_name
            self.save_state()
            # 只有在已经截帧的情况下才显示应用LUT按钮
            if self.delete_frame_btn.isVisible():
                self.apply_lut_btn.setVisible(True)

    def load_video(self):
        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(self.video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.slider.setMaximum(self.total_frames - 1)

        # 读取第一帧
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            self.display_frame(frame)

    def slider_changed(self):
        if self.cap is not None:
            frame_pos = self.slider.value()
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
                self.display_frame(frame)

    def update_frame(self):
        if self.cap is not None and self.is_playing:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
                self.display_frame(frame)
                current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.slider.setValue(current_frame)
                # 更新时间戳输入框，但不触发确认操作
                current_time = current_frame / self.fps
                self.timestamp_input.setText(f'{current_time:.2f}')
            else:
                self.stop_playback()
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.timestamp_input.setText('0.00')

    def toggle_play(self):
        if self.cap is not None:
            if self.is_playing:
                self.stop_playback()
            else:
                self.start_playback()

    def start_playback(self):
        self.is_playing = True
        self.play_btn.setText('暂停')
        # 根据播放速度设置定时器间隔
        interval = int(1000 / (self.fps * self.playback_speed))
        self.timer.start(interval)

    def stop_playback(self):
        self.is_playing = False
        self.play_btn.setText('播放')
        self.timer.stop()

    def speed_changed(self, speed_text):
        self.playback_speed = float(speed_text.replace('x', ''))
        if self.is_playing:
            # 更新定时器间隔
            interval = int(1000 / (self.fps * self.playback_speed))
            self.timer.start(interval)

    def display_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line,
                          QImage.Format.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(self.video_label.size(),
                                                           Qt.AspectRatioMode.KeepAspectRatio)
        self.video_label.setPixmap(scaled_pixmap)

    def confirm_timestamp(self):
        if self.cap is not None:
            try:
                timestamp = float(self.timestamp_input.text())
                frame_number = int(timestamp * self.fps)
                if 0 <= frame_number < self.total_frames:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                    ret, frame = self.cap.read()
                    if ret:
                        self.current_frame = frame
                        self.display_frame(frame)
                        self.slider.setValue(frame_number)
                else:
                    print('时间戳超出视频范围')
            except ValueError:
                print('请输入有效的时间戳')

    def capture_frame(self):
        if self.current_frame is not None:
            # 先确认时间戳
            self.confirm_timestamp()
            # 显示在预览区
            self.display_preview(self.current_frame)
            # 显示导出按钮
            self.export_original_btn.setVisible(True)

    def display_preview(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line,
                          QImage.Format.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(self.image_preview.size(),
                                                           Qt.AspectRatioMode.KeepAspectRatio)
        self.image_preview.setPixmap(scaled_pixmap)
        # 显示删除按钮
        self.delete_frame_btn.setVisible(True)
        # 如果已经选择了LUT文件，显示应用LUT按钮
        if self.lut_path:
            self.apply_lut_btn.setVisible(True)

    def display_lut_preview(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line,
                          QImage.Format.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(self.lut_preview.size(),
                                                           Qt.AspectRatioMode.KeepAspectRatio)
        self.lut_preview.setPixmap(scaled_pixmap)

    def delete_frame(self):
        # 清除预览区域
        self.image_preview.clear()
        self.lut_preview.clear()
        # 隐藏所有相关按钮
        self.delete_frame_btn.setVisible(False)
        self.apply_lut_btn.setVisible(False)
        self.export_original_btn.setVisible(False)
        self.export_lut_btn.setVisible(False)

    def apply_lut(self):
        if self.current_frame is not None and self.lut_path:
            # 将当前帧转换为PIL Image
            frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            # 应用LUT并显示在预览区
            self.display_lut_preview(self.current_frame)
            # 显示导出LUT图片按钮
            self.export_lut_btn.setVisible(True)

    def export_original(self):
        if self.current_frame is not None:
            timestamp = self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.fps
            directory = QFileDialog.getExistingDirectory(self, '选择保存目录')
            if directory:
                output_path = os.path.join(
                    directory, f'frame_{timestamp:.2f}.png')
                cv2.imwrite(output_path, self.current_frame)

    def export_lut(self):
        if self.current_frame is not None:
            timestamp = self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.fps
            directory = QFileDialog.getExistingDirectory(self, '选择保存目录')
            if directory:
                output_path = os.path.join(
                    directory, f'frame_{timestamp:.2f}_with_lut.png')
                cv2.imwrite(output_path, self.current_frame)


def main():
    app = QApplication(sys.argv)
    window = VideoProcessor()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
