import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, 
    QCheckBox, QGroupBox, QMessageBox, QProgressBar, QSizePolicy,
    QTabWidget, QComboBox, QSpinBox, QDoubleSpinBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

try:
    from qfluentwidgets import (
        FluentWindow, NavigationItemPosition, MessageBox, InfoBar, InfoBarPosition,
        PushButton, CheckBox, ComboBox, SpinBox, DoubleSpinBox, LineEdit, TextEdit,
        ProgressBar, SettingCardGroup, PushSettingCard, ScrollArea, ExpandLayout,
        TransparentToolButton, FluentIcon, CardWidget, SubtitleLabel
    )
    FLUENT_UI_AVAILABLE = True
except ImportError:
    FLUENT_UI_AVAILABLE = False
    print("Fluent UI not available. Please install PyQt-Fluent-Widgets to use Fluent UI.")
    print("Run: pip install PyQt-Fluent-Widgets")

class FluentMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apple Music Downloader - Fluent UI")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # 创建设置对象用于保存和加载用户配置
        self.settings = QSettings("AppleMusicDownloader", "Config")
        
        # 初始化UI
        self.init_ui()
        
        # 加载保存的设置
        self.load_settings()
        
        # 设置定时器定期检查许可证状态
        self.license_timer = QTimer(self)
        self.license_timer.timeout.connect(self.check_license_status)
        self.license_timer.start(10000)  # 每10秒检查一次
        
        # 初始化许可证状态
        self.check_license_status()

    def init_ui(self):
        """初始化用户界面"""
        if not FLUENT_UI_AVAILABLE:
            self.init_basic_ui()
            return
            
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel("Apple Music Downloader")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建下载标签页
        self.create_download_tab()
        
        # 创建设置标签页
        self.create_settings_tab()
        
        # 创建许可证标签页
        self.create_license_tab()
        
        # 状态栏
        self.status_text = TextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        main_layout.addWidget(self.status_text)
        
        # 进度条
        self.progress_bar = ProgressBar()
        main_layout.addWidget(self.progress_bar)

    def init_basic_ui(self):
        """初始化基础UI（当Fluent UI不可用时）"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("Apple Music Downloader (Basic UI - Fluent UI not available)")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建下载标签页
        self.create_download_tab()
        
        # 创建设置标签页
        self.create_settings_tab()
        
        # 创建许可证标签页
        self.create_license_tab()
        
        # 状态栏
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        main_layout.addWidget(self.status_text)
        
        # 进度条
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

    def create_download_tab(self):
        """创建下载标签页"""
        download_widget = QWidget()
        layout = QVBoxLayout(download_widget)
        
        # URL输入区域
        url_group = QGroupBox("下载链接")
        url_layout = QVBoxLayout(url_group)
        
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("在此输入Apple Music链接，每行一个...\n例如:\nhttps://music.apple.com/us/album/album-name/album-id\nhttps://music.apple.com/us/music-video/video-name/video-id")
        self.url_input.setMaximumHeight(100)
        url_layout.addWidget(self.url_input)
        
        layout.addWidget(url_group)
        
        # 文件路径选择区域
        path_group = QGroupBox("文件路径")
        path_layout = QGridLayout(path_group)
        
        # Cookie文件选择
        self.cookie_path = QLineEdit()
        self.cookie_path.setPlaceholderText("选择您的Cookie文件")
        cookie_button = QPushButton("浏览...")
        cookie_button.clicked.connect(self.select_cookie_file)
        path_layout.addWidget(QLabel("Cookie文件:"), 0, 0)
        path_layout.addWidget(self.cookie_path, 0, 1)
        path_layout.addWidget(cookie_button, 0, 2)
        
        # 输出目录选择
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择输出目录")
        output_button = QPushButton("浏览...")
        output_button.clicked.connect(self.select_output_directory)
        path_layout.addWidget(QLabel("输出目录:"), 1, 0)
        path_layout.addWidget(self.output_path, 1, 1)
        path_layout.addWidget(output_button, 1, 2)
        
        layout.addWidget(path_group)
        
        # 下载选项区域
        options_group = QGroupBox("下载选项")
        options_layout = QVBoxLayout(options_group)
        
        # 复选框选项
        checkboxes_layout = QGridLayout()
        
        self.overwrite_checkbox = QCheckBox("覆盖已存在文件")
        self.disable_music_video_skip_checkbox = QCheckBox("禁用音乐视频跳过")
        self.save_playlist_checkbox = QCheckBox("保存播放列表")
        self.synced_lyrics_only_checkbox = QCheckBox("仅下载同步歌词")
        self.no_synced_lyrics_checkbox = QCheckBox("不下载同步歌词")
        self.read_urls_as_txt_checkbox = QCheckBox("将URL作为TXT文件读取")
        self.no_exceptions_checkbox = QCheckBox("禁用例外处理")
        
        checkboxes_layout.addWidget(self.overwrite_checkbox, 0, 0)
        checkboxes_layout.addWidget(self.disable_music_video_skip_checkbox, 0, 1)
        checkboxes_layout.addWidget(self.save_playlist_checkbox, 1, 0)
        checkboxes_layout.addWidget(self.synced_lyrics_only_checkbox, 1, 1)
        checkboxes_layout.addWidget(self.no_synced_lyrics_checkbox, 2, 0)
        checkboxes_layout.addWidget(self.read_urls_as_txt_checkbox, 2, 1)
        checkboxes_layout.addWidget(self.no_exceptions_checkbox, 3, 0)
        
        options_layout.addLayout(checkboxes_layout)
        
        # 格式转换选项
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("音频格式转换:"))
        
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems([
            "保持原格式", "mp3", "flac", "wav", "aac", "m4a", "ogg", "wma"
        ])
        format_layout.addWidget(self.audio_format_combo)
        
        format_layout.addWidget(QLabel("视频格式转换:"))
        
        self.video_format_combo = QComboBox()
        self.video_format_combo.addItems([
            "保持原格式", "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm"
        ])
        format_layout.addWidget(self.video_format_combo)
        
        options_layout.addLayout(format_layout)
        
        layout.addWidget(options_group)
        
        # 下载按钮
        self.download_button = QPushButton("开始下载")
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.download_button)
        
        self.tab_widget.addTab(download_widget, "下载")

    def create_settings_tab(self):
        """创建设置标签页"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # 下载模式设置
        mode_group = QGroupBox("下载模式")
        mode_layout = QHBoxLayout(mode_group)
        
        mode_layout.addWidget(QLabel("下载模式:"))
        self.download_mode_combo = QComboBox()
        self.download_mode_combo.addItems(["default", "legacy"])
        mode_layout.addWidget(self.download_mode_combo)
        
        mode_layout.addWidget(QLabel("混流模式:"))
        self.remux_mode_combo = QComboBox()
        self.remux_mode_combo.addItems(["default", "ffmpeg", "mp4box"])
        mode_layout.addWidget(self.remux_mode_combo)
        
        layout.addWidget(mode_group)
        
        # 编码格式设置
        codec_group = QGroupBox("编码格式")
        codec_layout = QGridLayout(codec_group)
        
        codec_layout.addWidget(QLabel("音频编码格式:"), 0, 0)
        self.codec_song_combo = QComboBox()
        self.codec_song_combo.addItems(["auto", "aac", "alac"])
        codec_layout.addWidget(self.codec_song_combo, 0, 1)
        
        codec_layout.addWidget(QLabel("音乐视频编码格式:"), 1, 0)
        self.codec_music_video_combo = QComboBox()
        self.codec_music_video_combo.addItems(["auto", "h264", "h265", "vp9"])
        codec_layout.addWidget(self.codec_music_video_combo, 1, 1)
        
        layout.addWidget(codec_group)
        
        # 封面和歌词设置
        cover_group = QGroupBox("封面和歌词")
        cover_layout = QGridLayout(cover_group)
        
        cover_layout.addWidget(QLabel("封面格式:"), 0, 0)
        self.cover_format_combo = QComboBox()
        self.cover_format_combo.addItems(["default", "jpg", "png", "webp"])
        cover_layout.addWidget(self.cover_format_combo, 0, 1)
        
        cover_layout.addWidget(QLabel("封面尺寸:"), 1, 0)
        self.cover_size_spin = QSpinBox()
        self.cover_size_spin.setRange(90, 3000)
        self.cover_size_spin.setValue(90)
        cover_layout.addWidget(self.cover_size_spin, 1, 1)
        
        cover_layout.addWidget(QLabel("截断长度:"), 2, 0)
        self.truncate_spin = QSpinBox()
        self.truncate_spin.setRange(0, 1000)
        self.truncate_spin.setValue(0)
        cover_layout.addWidget(self.truncate_spin, 2, 1)
        
        cover_layout.addWidget(QLabel("同步歌词格式:"), 3, 0)
        self.synced_lyrics_format_combo = QComboBox()
        self.synced_lyrics_format_combo.addItems(["default", "lrc", "srt", "ttml"])
        cover_layout.addWidget(self.synced_lyrics_format_combo, 3, 1)
        
        layout.addWidget(cover_group)
        
        # 视频质量设置
        quality_group = QGroupBox("视频质量")
        quality_layout = QHBoxLayout(quality_group)
        
        quality_layout.addWidget(QLabel("帖子视频质量:"))
        self.quality_post_combo = QComboBox()
        self.quality_post_combo.addItems(["auto", "360p", "480p", "720p", "1080p", "2160p"])
        quality_layout.addWidget(self.quality_post_combo)
        
        layout.addWidget(quality_group)
        
        # 保存设置按钮
        save_settings_button = QPushButton("保存设置")
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        self.tab_widget.addTab(settings_widget, "设置")

    def create_license_tab(self):
        """创建许可证标签页"""
        license_widget = QWidget()
        layout = QVBoxLayout(license_widget)
        
        # 说明文本
        info_label = QLabel(
            "许可证信息:\n"
            "1. 请确保您已购买许可证\n"
            "2. 选择您的许可证文件进行验证\n"
            "3. 许可证状态将定期自动检查"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_label.setStyleSheet("margin-bottom: 20px;")
        layout.addWidget(info_label)
        
        # 许可证文件选择
        license_layout = QHBoxLayout()
        self.license_path = QLineEdit()
        self.license_path.setPlaceholderText("选择您的许可证文件")
        license_button = QPushButton("浏览...")
        license_button.clicked.connect(self.select_license_file)
        license_layout.addWidget(QLabel("许可证文件:"))
        license_layout.addWidget(self.license_path)
        license_layout.addWidget(license_button)
        layout.addLayout(license_layout)
        
        # 许可证信息显示区域
        self.license_info = QTextEdit()
        self.license_info.setReadOnly(True)
        layout.addWidget(self.license_info)
        
        # 验证按钮
        validate_button = QPushButton("验证许可证")
        validate_button.clicked.connect(self.validate_license)
        layout.addWidget(validate_button)
        
        self.tab_widget.addTab(license_widget, "许可证")

    def select_cookie_file(self):
        """选择Cookie文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Cookie文件", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.cookie_path.setText(file_path)

    def select_output_directory(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_path.setText(directory)

    def select_license_file(self):
        """选择许可证文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择许可证文件", "", "Key Files (*.key);;All Files (*)"
        )
        if file_path:
            self.license_path.setText(file_path)

    def start_download(self):
        """开始下载"""
        # 这里应该连接到下载逻辑
        self.status_text.append("开始下载...")

    def save_settings(self):
        """保存设置"""
        self.settings.setValue("cookie_path", self.cookie_path.text())
        self.settings.setValue("output_path", self.output_path.text())
        self.settings.setValue("license_path", self.license_path.text())
        
        # 保存选项设置
        self.settings.setValue("overwrite", self.overwrite_checkbox.isChecked())
        self.settings.setValue("disable_music_video_skip", self.disable_music_video_skip_checkbox.isChecked())
        self.settings.setValue("save_playlist", self.save_playlist_checkbox.isChecked())
        self.settings.setValue("synced_lyrics_only", self.synced_lyrics_only_checkbox.isChecked())
        self.settings.setValue("no_synced_lyrics", self.no_synced_lyrics_checkbox.isChecked())
        self.settings.setValue("read_urls_as_txt", self.read_urls_as_txt_checkbox.isChecked())
        self.settings.setValue("no_exceptions", self.no_exceptions_checkbox.isChecked())
        
        # 保存组合框设置
        self.settings.setValue("audio_format", self.audio_format_combo.currentText())
        self.settings.setValue("video_format", self.video_format_combo.currentText())
        self.settings.setValue("download_mode", self.download_mode_combo.currentText())
        self.settings.setValue("remux_mode", self.remux_mode_combo.currentText())
        self.settings.setValue("codec_song", self.codec_song_combo.currentText())
        self.settings.setValue("codec_music_video", self.codec_music_video_combo.currentText())
        self.settings.setValue("cover_format", self.cover_format_combo.currentText())
        self.settings.setValue("cover_size", self.cover_size_spin.value())
        self.settings.setValue("truncate", self.truncate_spin.value())
        self.settings.setValue("synced_lyrics_format", self.synced_lyrics_format_combo.currentText())
        self.settings.setValue("quality_post", self.quality_post_combo.currentText())
        
        self.status_text.append("设置已保存")

    def load_settings(self):
        """加载设置"""
        self.cookie_path.setText(self.settings.value("cookie_path", ""))
        self.output_path.setText(self.settings.value("output_path", ""))
        self.license_path.setText(self.settings.value("license_path", ""))
        
        # 加载选项设置
        self.overwrite_checkbox.setChecked(self.settings.value("overwrite", False, type=bool))
        self.disable_music_video_skip_checkbox.setChecked(self.settings.value("disable_music_video_skip", False, type=bool))
        self.save_playlist_checkbox.setChecked(self.settings.value("save_playlist", False, type=bool))
        self.synced_lyrics_only_checkbox.setChecked(self.settings.value("synced_lyrics_only", False, type=bool))
        self.no_synced_lyrics_checkbox.setChecked(self.settings.value("no_synced_lyrics", False, type=bool))
        self.read_urls_as_txt_checkbox.setChecked(self.settings.value("read_urls_as_txt", False, type=bool))
        self.no_exceptions_checkbox.setChecked(self.settings.value("no_exceptions", False, type=bool))
        
        # 加载组合框设置
        audio_format = self.settings.value("audio_format", "保持原格式")
        index = self.audio_format_combo.findText(audio_format)
        if index >= 0:
            self.audio_format_combo.setCurrentIndex(index)
            
        video_format = self.settings.value("video_format", "保持原格式")
        index = self.video_format_combo.findText(video_format)
        if index >= 0:
            self.video_format_combo.setCurrentIndex(index)
            
        download_mode = self.settings.value("download_mode", "default")
        index = self.download_mode_combo.findText(download_mode)
        if index >= 0:
            self.download_mode_combo.setCurrentIndex(index)
            
        remux_mode = self.settings.value("remux_mode", "default")
        index = self.remux_mode_combo.findText(remux_mode)
        if index >= 0:
            self.remux_mode_combo.setCurrentIndex(index)
            
        codec_song = self.settings.value("codec_song", "auto")
        index = self.codec_song_combo.findText(codec_song)
        if index >= 0:
            self.codec_song_combo.setCurrentIndex(index)
            
        codec_music_video = self.settings.value("codec_music_video", "auto")
        index = self.codec_music_video_combo.findText(codec_music_video)
        if index >= 0:
            self.codec_music_video_combo.setCurrentIndex(index)
            
        cover_format = self.settings.value("cover_format", "default")
        index = self.cover_format_combo.findText(cover_format)
        if index >= 0:
            self.cover_format_combo.setCurrentIndex(index)
            
        self.cover_size_spin.setValue(self.settings.value("cover_size", 90, type=int))
        self.truncate_spin.setValue(self.settings.value("truncate", 0, type=int))
        
        synced_lyrics_format = self.settings.value("synced_lyrics_format", "default")
        index = self.synced_lyrics_format_combo.findText(synced_lyrics_format)
        if index >= 0:
            self.synced_lyrics_format_combo.setCurrentIndex(index)
            
        quality_post = self.settings.value("quality_post", "auto")
        index = self.quality_post_combo.findText(quality_post)
        if index >= 0:
            self.quality_post_combo.setCurrentIndex(index)

    def validate_license(self):
        """验证许可证"""
        license_path = self.license_path.text()
        if not license_path:
            self.license_info.setPlainText("请先选择许可证文件")
            return
            
        try:
            with open(license_path, 'r') as f:
                license_content = f.read().strip()
                
            # 解码Base64
            import base64
            decoded_content = base64.b64decode(license_content).decode('utf-8')
            
            # 解析JSON
            import json
            license_data = json.loads(decoded_content)
            
            # 检查必要字段
            if 'created_at' not in license_data:
                self.license_info.setPlainText("许可证格式无效: 缺少created_at字段")
                return
                
            # 检查是否为永久许可证
            if 'permanent' in license_data and license_data['permanent']:
                license_text = "许可证状态: 有效 (永久许可证)\n"
                license_text += f"创建时间: {license_data['created_at']}\n"
                if 'user' in license_data:
                    license_text += f"用户: {license_data['user']}\n"
                self.license_info.setPlainText(license_text)
            else:
                # 检查过期时间
                from datetime import datetime
                created_time = datetime.fromisoformat(license_data['created_at'].replace('Z', '+00:00'))
                expiry_time = created_time.replace(year=created_time.year + 1)
                current_time = datetime.utcnow()
                
                if current_time < expiry_time:
                    remaining_days = (expiry_time - current_time).days
                    license_text = f"许可证状态: 有效\n"
                    license_text += f"创建时间: {license_data['created_at']}\n"
                    license_text += f"过期时间: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                    license_text += f"剩余天数: {remaining_days} 天\n"
                    if 'user' in license_data:
                        license_text += f"用户: {license_data['user']}\n"
                    self.license_info.setPlainText(license_text)
                else:
                    license_text = f"许可证状态: 已过期\n"
                    license_text += f"创建时间: {license_data['created_at']}\n"
                    license_text += f"过期时间: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                    self.license_info.setPlainText(license_text)
        except Exception as e:
            self.license_info.setPlainText(f"许可证验证失败: {str(e)}")

    def check_license_status(self):
        """检查许可证状态"""
        # 这里可以实现定期检查许可证状态的逻辑
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FluentMainWindow()
    window.show()
    sys.exit(app.exec())