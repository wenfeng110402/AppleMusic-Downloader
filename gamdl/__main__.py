import base64
import datetime
import json
import sys
import os
import logging
import io
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
#copyright (c) 2025 wenfeng110402
#copyright (c) 2025 CrEAttivviTTy
# 正确导入cli模块
import gamdl.cli

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, 
    QCheckBox, QGroupBox, QMessageBox, QProgressBar, QSizePolicy,
    QTabWidget, QComboBox, QSpinBox, QDoubleSpinBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QColor, QPalette

def validate_license_key(key):
    """
    验证许可证密钥
    """
    try:
        # 解码密钥
        key_json = base64.b64decode(key.encode()).decode()
        key_data = json.loads(key_json)
        
        # 检查必需字段
        if "created_at" not in key_data:
            return False, "许可证格式无效"
        
        # 检查是否为永久许可证
        if key_data.get("lifetime", False):
            return True, "永久许可证有效"
        
        # 检查是否有过期时间
        if "expires_at" not in key_data:
            return False, "许可证格式无效"
        
        # 检查是否过期
        expires_at = datetime.datetime.fromisoformat(key_data["expires_at"])
        current_time = datetime.datetime.now()
        
        if current_time > expires_at:
            return False, f"许可证已过期，过期时间: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 计算剩余时间
        remaining = expires_at - current_time
        days = remaining.days
        hours = remaining.seconds // 3600
        
        return True, f"许可证有效，剩余时间: {days}天 {hours}小时"
        
    except Exception as e:
        return False, f"许可证验证失败: {str(e)}"

def check_license(license_path):
    """
    检查许可证文件
    """
    # 检查许可证文件是否存在
    if not os.path.exists(license_path):
        return False, "未找到许可证文件"
    
    try:
        # 读取许可证文件
        with open(license_path, "r") as f:
            key = f.read().strip()
        
        # 验证许可证
        is_valid, message = validate_license_key(key)
        return is_valid, message
            
    except Exception as e:
        return False, f"读取许可证文件时出错: {str(e)}"

class DownloadThread(QThread):
    """下载线程类，用于在后台执行下载任务"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)  # 添加成功/失败状态
    
    def __init__(self, urls, cookie_file, output_dir, download_options, license_file):
        super().__init__()
        self.urls = urls
        self.cookie_file = cookie_file
        self.output_dir = output_dir
        self.download_options = download_options
        self.license_file = license_file
    
    def run(self):
        try:
            # 为每个URL创建下载任务
            total = len(self.urls)
            success_count = 0
            
            for i, url in enumerate(self.urls, 1):
                self.log_signal.emit(f"[{i}/{total}] 正在处理: {url}")
                
                # 构建参数
                args = [url]  # URL是必需参数
                
                # 添加Cookie文件参数
                if self.cookie_file:
                    args.extend(['--cookies-path', self.cookie_file])
                
                # 添加输出目录参数
                if self.output_dir:
                    args.extend(['--output-path', self.output_dir])
                
                # 添加其他选项
                if self.download_options.get('save_cover'):
                    args.append('--save-cover')
                    
                if self.download_options.get('overwrite'):
                    args.append('--overwrite')
                    
                if self.download_options.get('disable_music_video_skip'):
                    args.append('--disable-music-video-skip')
                    
                if self.download_options.get('save_playlist'):
                    args.append('--save-playlist')
                    
                if self.download_options.get('synced_lyrics_only'):
                    args.append('--synced-lyrics-only')
                    
                if self.download_options.get('no_synced_lyrics'):
                    args.append('--no-synced-lyrics')
                    
                if self.download_options.get('read_urls_as_txt'):
                    args.append('--read-urls-as-txt')
                    
                if self.download_options.get('no_exceptions'):
                    args.append('--no-exceptions')
                
                # 添加音频解码格式选项
                if self.download_options.get('codec_song'):
                    args.extend(['--codec-song', self.download_options.get('codec_song')])
                # 创建字符串IO对象来捕获日志输出
                log_stream = io.StringIO()
                
                try:
                    # 重定向stdout和stderr以捕获CLI输出
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = log_stream
                    sys.stderr = log_stream
                    
                    # 调用CLI功能执行下载
                    gamdl.cli.main(args, standalone_mode=False)
                    success_count += 1
                    self.log_signal.emit(f"    完成!")
                except SystemExit as e:
                    # click通过SystemExit来处理完成状态
                    if e.code == 0:
                        success_count += 1
                        self.log_signal.emit(f"    完成!")
                    else:
                        self.log_signal.emit(f"    错误: 下载失败，退出码 {e.code}")
                except Exception as e:
                    self.log_signal.emit(f"    错误: {str(e)}")

                finally:
                    # 恢复标准输出
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    
                    # 输出捕获的日志
                    log_content = log_stream.getvalue()
                    if log_content:
                        for line in log_content.splitlines():
                            if line.strip():  # 忽略空行
                                self.log_signal.emit(f"    {line}")
                
                # 更新进度
                progress = int((i / total) * 100)
                self.progress_signal.emit(progress)
            
            self.log_signal.emit("=" * 50)
            self.log_signal.emit(f"下载任务完成: {success_count}/{total} 成功")
            self.progress_signal.emit(100)
            self.finished_signal.emit(success_count == total)
        except Exception as e:
            self.log_signal.emit(f"下载过程中发生严重错误: {str(e)}")
            self.finished_signal.emit(False)

class GamdlGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apple Music Downloader")
        self.setGeometry(100, 100, 1000, 700)
        
        # 应用设置
        self.settings = QSettings('gamdl', 'AppleMusicDownloader')
        
        # 下载线程
        self.download_thread = None
        
        # 创建界面
        self.create_widgets()
        
        # 检查许可证
        self.check_initial_license()
        
        # 加载保存的设置
        self.load_settings()
        
    def get_default_tool_path(self, tool_name):
        """
        获取工具的默认路径
        首先检查当前目录下的tools文件夹，如果找不到则返回默认名称
        """
        # 获取程序所在目录
        app_path = Path(sys.argv[0]).parent.absolute()
        
        # 检查tools目录下的工具
        tool_path = app_path / "tools" / tool_name
        if tool_path.exists():
            return str(tool_path)
        
        # 如果tools目录中没有找到，则返回默认名称
        # 让系统在PATH中查找
        return tool_name.split('.')[0]
        
    def get_default_cookie_path(self):
        """
        获取默认的cookie文件路径
        自动查找程序目录下的cookie文件
        """
        # 获取程序所在目录
        app_path = Path(sys.argv[0]).parent.absolute()
        
        # 常见的cookie文件名
        cookie_filenames = ["cookies.txt", "cookie.txt", "cookies", "cookie"]
        
        # 查找目录下的cookie文件
        for filename in cookie_filenames:
            cookie_path = app_path / filename
            if cookie_path.exists():
                return str(cookie_path)
        
        # 如果没找到，返回默认路径
        return str(app_path / "cookies.txt")
        
    def create_widgets(self):
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(main_widget)
        
        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 创建下载标签页
        self.create_download_tab(tab_widget)
        
        # 创建设置标签页
        self.create_settings_tab(tab_widget)
        
        # 创建许可证标签页
        self.create_license_tab(tab_widget)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
    def create_download_tab(self, parent):
        # 下载标签页
        download_widget = QWidget()
        parent.addTab(download_widget, "下载")
        
        layout = QVBoxLayout(download_widget)
        
        # URL输入区域
        url_group = QGroupBox("URL列表")
        url_layout = QVBoxLayout(url_group)
        
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("在此输入Apple Music URL，每行一个...\n例如: https://music.apple.com/us/album/album-name/album-id")
        url_layout.addWidget(self.url_input)
        
        layout.addWidget(url_group)
        
        # 文件路径区域
        path_group = QGroupBox("文件路径")
        path_layout = QGridLayout(path_group)
        
        # Cookie文件
        path_layout.addWidget(QLabel("Cookie文件:"), 0, 0)
        self.cookie_path = QLineEdit()
        self.cookie_path.setPlaceholderText("选择Cookie文件...")
        path_layout.addWidget(self.cookie_path, 0, 1)
        cookie_browse_btn = QPushButton("浏览")
        cookie_browse_btn.clicked.connect(self.browse_cookie)
        path_layout.addWidget(cookie_browse_btn, 0, 2)
        
        # 输出目录
        path_layout.addWidget(QLabel("输出目录:"), 1, 0)
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择输出目录...")
        path_layout.addWidget(self.output_path, 1, 1)
        output_browse_btn = QPushButton("浏览")
        output_browse_btn.clicked.connect(self.browse_output)
        path_layout.addWidget(output_browse_btn, 1, 2)
        
        layout.addWidget(path_group)
        
        # 下载选项区域
        options_group = QGroupBox("下载选项")
        options_layout = QGridLayout(options_group)
        
        self.save_cover = QCheckBox("保存封面")
        self.overwrite = QCheckBox("覆盖已存在文件")
        self.disable_music_video_skip = QCheckBox("不跳过音乐视频")
        self.save_playlist = QCheckBox("保存播放列表")
        self.synced_lyrics_only = QCheckBox("仅下载同步歌词")
        self.no_synced_lyrics = QCheckBox("不下载同步歌词")
        self.read_urls_as_txt = QCheckBox("将URL作为文本文件读取")
        self.no_exceptions = QCheckBox("不显示异常信息")
        
        options_layout.addWidget(self.save_cover, 0, 0)
        options_layout.addWidget(self.overwrite, 0, 1)
        options_layout.addWidget(self.disable_music_video_skip, 1, 0)
        options_layout.addWidget(self.save_playlist, 1, 1)
        options_layout.addWidget(self.synced_lyrics_only, 2, 0)
        options_layout.addWidget(self.no_synced_lyrics, 2, 1)
        options_layout.addWidget(self.read_urls_as_txt, 3, 0)
        options_layout.addWidget(self.no_exceptions, 3, 1)
        
        layout.addWidget(options_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("开始下载")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 10px; }")
        control_layout.addWidget(self.download_btn)
        
        self.clear_log_btn = QPushButton("清除日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        control_layout.addWidget(self.clear_log_btn)
        
        layout.addLayout(control_layout)
        
        # 进度和日志区域
        progress_group = QGroupBox("下载进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setPlaceholderText("下载日志将显示在这里...")
        progress_layout.addWidget(self.log_text)
        
        layout.addWidget(progress_group)
        
    def create_settings_tab(self, parent):
        # 设置标签页
        settings_widget = QWidget()
        parent.addTab(settings_widget, "设置")
        
        layout = QVBoxLayout(settings_widget)
        
        # 创建滚动区域以容纳所有设置
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QGridLayout(advanced_group)
        
        # 临时目录
        advanced_layout.addWidget(QLabel("临时目录:"), 0, 0)
        self.temp_path = QLineEdit()
        self.temp_path.setPlaceholderText("./temp")
        advanced_layout.addWidget(self.temp_path, 0, 1)
        
        # WVD文件路径
        advanced_layout.addWidget(QLabel(".wvd文件路径:"), 1, 0)
        self.wvd_path = QLineEdit()
        self.wvd_path.setPlaceholderText("可选")
        advanced_layout.addWidget(self.wvd_path, 1, 1)
        wvd_browse_btn = QPushButton("浏览")
        wvd_browse_btn.clicked.connect(self.browse_wvd)
        advanced_layout.addWidget(wvd_browse_btn, 1, 2)
        
        # 下载模式
        advanced_layout.addWidget(QLabel("下载模式:"), 2, 0)
        self.download_mode = QComboBox()
        self.download_mode.addItems(["ytdlp", "nm3u8dlre"])
        advanced_layout.addWidget(self.download_mode, 2, 1)
        
        # 混流模式
        advanced_layout.addWidget(QLabel("混流模式:"), 3, 0)
        self.remux_mode = QComboBox()
        self.remux_mode.addItems(["ffmpeg", "mp4box"])
        advanced_layout.addWidget(self.remux_mode, 3, 1)
        
        # 封面格式
        advanced_layout.addWidget(QLabel("封面格式:"), 4, 0)
        self.cover_format = QComboBox()
        self.cover_format.addItems(["jpg", "png", "raw"])
        advanced_layout.addWidget(self.cover_format, 4, 1)
        
        # 封面尺寸
        advanced_layout.addWidget(QLabel("封面尺寸:"), 5, 0)
        self.cover_size = QSpinBox()
        self.cover_size.setRange(100, 5000)
        self.cover_size.setValue(1200)
        advanced_layout.addWidget(self.cover_size, 5, 1)
        
        # 截断长度
        advanced_layout.addWidget(QLabel("文件名截断长度:"), 6, 0)
        self.truncate = QSpinBox()
        self.truncate.setRange(0, 999)
        self.truncate.setSpecialValueText("无限制")
        self.truncate.setValue(0)
        advanced_layout.addWidget(self.truncate, 6, 1)
        
        # 音频解码格式
        advanced_layout.addWidget(QLabel("音频解码格式:"), 7, 0)
        self.codec_song = QComboBox()
        self.codec_song.addItems([
            "aac-legacy", "aac-he-legacy", "aac", "aac-he", "aac-binaural", 
            "aac-downmix", "aac-he-binaural", "aac-he-downmix", "atmos", 
            "ac3", "alac", "ask"
        ])
        advanced_layout.addWidget(self.codec_song, 7, 1)
        
        scroll_layout.addWidget(advanced_group)
        
        
        # 模板设置
        template_group = QGroupBox("文件命名模板")
        template_layout = QVBoxLayout(template_group)
        
        # 专辑文件夹模板
        template_h_layout1 = QHBoxLayout()
        template_h_layout1.addWidget(QLabel("专辑文件夹模板:"))
        self.template_folder_album = QLineEdit()
        self.template_folder_album.setPlaceholderText("{album_artist}/{album}")
        template_h_layout1.addWidget(self.template_folder_album)
        template_layout.addLayout(template_h_layout1)
        
        # 合辑文件夹模板
        template_h_layout2 = QHBoxLayout()
        template_h_layout2.addWidget(QLabel("合辑文件夹模板:"))
        self.template_folder_compilation = QLineEdit()
        self.template_folder_compilation.setPlaceholderText("Compilations/{album}")
        template_h_layout2.addWidget(self.template_folder_compilation)
        template_layout.addLayout(template_h_layout2)
        
        # 单碟文件模板
        template_h_layout3 = QHBoxLayout()
        template_h_layout3.addWidget(QLabel("单碟文件模板:"))
        self.template_file_single_disc = QLineEdit()
        self.template_file_single_disc.setPlaceholderText("{track:02d} {title}")
        template_h_layout3.addWidget(self.template_file_single_disc)
        template_layout.addLayout(template_h_layout3)
        
        # 多碟文件模板
        template_h_layout4 = QHBoxLayout()
        template_h_layout4.addWidget(QLabel("多碟文件模板:"))
        self.template_file_multi_disc = QLineEdit()
        self.template_file_multi_disc.setPlaceholderText("{disc}-{track:02d} {title}")
        template_h_layout4.addWidget(self.template_file_multi_disc)
        template_layout.addLayout(template_h_layout4)
        
        scroll_layout.addWidget(template_group)
        
        # 路径设置
        path_group = QGroupBox("工具路径设置")
        path_layout = QVBoxLayout(path_group)
        
        # 添加说明标签
        info_label = QLabel("工具已内嵌，无需额外配置路径。")
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: green;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f0fff0;
            }
        """)
        path_layout.addWidget(info_label)
        
        scroll_layout.addWidget(path_group)
        
        # 应用按钮
        button_layout = QHBoxLayout()
        self.save_settings_btn = QPushButton("保存设置")
        self.save_settings_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_settings_btn)
        
        self.reset_settings_btn = QPushButton("重置设置")
        self.reset_settings_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_settings_btn)
        
        scroll_layout.addLayout(button_layout)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
    def create_license_tab(self, parent):
        # 许可证标签页
        license_widget = QWidget()
        parent.addTab(license_widget, "许可证")
        
        layout = QVBoxLayout(license_widget)
        
        # 许可证信息区域
        license_info_group = QGroupBox("许可证信息")
        license_info_layout = QVBoxLayout(license_info_group)
        
        # 许可证文件选择
        license_file_layout = QHBoxLayout()
        license_file_layout.addWidget(QLabel("许可证文件:"))
        self.license_path = QLineEdit()
        self.license_path.setPlaceholderText("选择许可证文件...")
        license_file_layout.addWidget(self.license_path)
        license_browse_btn = QPushButton("浏览")
        license_browse_btn.clicked.connect(self.browse_license)
        license_file_layout.addWidget(license_browse_btn)
        license_info_layout.addLayout(license_file_layout)
        
        # 许可证状态
        self.license_status = QLabel("请选择许可证文件")
        self.license_status.setWordWrap(True)
        self.license_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.license_status.setStyleSheet("""
            QLabel {
                color: blue;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        license_info_layout.addWidget(self.license_status)
        
        layout.addWidget(license_info_group)
        
        # 许可证说明
        info_group = QGroupBox("许可证说明")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml("""
        <h3>关于许可证</h3>
        <p>Apple Music Downloader 需要有效的许可证才能使用。</p>
        <p>请确保您拥有有效的许可证文件，以继续使用本软件。</p>
        <h4>许可证类型:</h4>
        <ul>
            <li><b>临时许可证</b>: 有固定的有效期</li>
            <li><b>永久许可证</b>: 永久有效</li>
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # 添加弹性空间
        layout.addStretch()
        
    def browse_license(self):
        """浏览选择许可证文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择许可证文件", "", "License Files (*.key);;All Files (*)"
        )
        
        if file_path:
            self.license_path.setText(file_path)
            self.validate_selected_license()
            
    def browse_cookie(self):
        """浏览选择cookie文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Cookie文件", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.cookie_path.setText(file_path)
            
    def browse_output(self):
        """浏览选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_path.setText(directory)
            
    def browse_wvd(self):
        """浏览选择WVD文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择.wvd文件", "", "WVD Files (*.wvd);;All Files (*)"
        )
        
        if file_path:
            self.wvd_path.setText(file_path)
            
    def validate_selected_license(self):
        """验证选中的许可证"""
        license_file = self.license_path.text()
        if license_file:
            is_valid, message = check_license(license_file)
            self.license_status.setText(message)
            if is_valid:
                self.license_status.setStyleSheet("""
                    QLabel {
                        color: green;
                        font-weight: bold;
                        padding: 10px;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        background-color: #f0fff0;
                    }
                """)
                self.statusBar().showMessage("许可证验证通过", 3000)
            else:
                self.license_status.setStyleSheet("""
                    QLabel {
                        color: red;
                        font-weight: bold;
                        padding: 10px;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        background-color: #fff0f0;
                    }
                """)
                self.statusBar().showMessage("许可证验证失败", 3000)
            return is_valid
        return False
            
    def check_initial_license(self):
        """检查初始许可证"""
        # 默认查找当前目录下的license.key
        default_license = "license.key"
        if os.path.exists(default_license):
            self.license_path.setText(default_license)
            is_valid, message = check_license(default_license)
            self.license_status.setText(message)
            if is_valid:
                self.license_status.setStyleSheet("""
                    QLabel {
                        color: green;
                        font-weight: bold;
                        padding: 10px;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        background-color: #f0fff0;
                    }
                """)
                self.statusBar().showMessage("许可证已加载并验证通过", 3000)
            else:
                self.license_status.setStyleSheet("""
                    QLabel {
                        color: red;
                        font-weight: bold;
                        padding: 10px;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        background-color: #fff0f0;
                    }
                """)
                QMessageBox.critical(self, "许可证错误", f"{message}\n请确保选择了有效的许可证文件")
        else:
            self.license_status.setText("请选择许可证文件")
            self.license_status.setStyleSheet("""
                QLabel {
                    color: blue;
                    font-weight: bold;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    background-color: #f9f9f9;
                }
            """)
            
    def start_download(self):
        """开始下载"""
        # 获取URL列表
        urls_text = self.url_input.toPlainText()
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        cookie_file = self.cookie_path.text()
        license_file = self.license_path.text()
        output_dir = self.output_path.text()
        
        if not license_file:
            QMessageBox.critical(self, "错误", "请选择许可证文件")
            return
            
        # 验证许可证
        is_valid, message = check_license(license_file)
        if not is_valid:
            QMessageBox.critical(self, "许可证错误", message)
            return
            
        if not urls:
            QMessageBox.critical(self, "错误", "请输入至少一个URL")
            return
            
        if not cookie_file:
            QMessageBox.critical(self, "错误", "请选择Cookie文件")
            return
            
        if not os.path.exists(cookie_file):
            QMessageBox.critical(self, "错误", "Cookie文件不存在")
            return
            
        # 如果指定了输出目录，检查目录是否存在
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建输出目录: {str(e)}")
                return
                
        # 收集下载选项
        download_options = {
            'save_cover': self.save_cover.isChecked(),
            'overwrite': self.overwrite.isChecked(),
            'disable_music_video_skip': self.disable_music_video_skip.isChecked(),
            'save_playlist': self.save_playlist.isChecked(),
            'synced_lyrics_only': self.synced_lyrics_only.isChecked(),
            'no_synced_lyrics': self.no_synced_lyrics.isChecked(),
            'read_urls_as_txt': self.read_urls_as_txt.isChecked(),
            'no_exceptions': self.no_exceptions.isChecked(),
            'codec_song': self.codec_song.currentText()
        }
                
        # 显示开始下载信息
        self.log_text.append(f"开始下载 {len(urls)} 个URL")
        self.log_text.append(f"使用许可证文件: {license_file}")
        self.log_text.append(f"使用Cookie文件: {cookie_file}")
        if output_dir:
            self.log_text.append(f"输出目录: {output_dir}")
        self.log_text.append("-" * 50)
        
        # 创建并启动下载线程
        self.download_thread = DownloadThread(
            urls, cookie_file, output_dir,
            download_options,
            license_file
        )
        
        # 连接信号
        self.download_thread.log_signal.connect(self.append_log)
        self.download_thread.progress_signal.connect(self.progress_bar.setValue)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        
        # 禁用下载按钮，防止重复点击
        self.download_btn.setEnabled(False)
        self.download_btn.setText("下载中...")
        self.statusBar().showMessage("正在下载...", 0)
        self.download_thread.start()
        
    def append_log(self, message):
        """添加日志信息"""
        self.log_text.append(message)
        # 自动滚动到底部
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        
    def on_download_finished(self, success):
        """下载完成后的处理"""
        self.download_btn.setEnabled(True)
        self.download_btn.setText("开始下载")
        self.download_thread = None
        self.statusBar().showMessage("下载完成", 3000)
        
        if success:
            QMessageBox.information(self, "完成", "所有下载任务已完成!")
        else:
            QMessageBox.warning(self, "完成", "下载任务已完成，但部分项目可能失败。请查看日志了解详情。")

    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
    def save_settings(self):
        """保存设置"""
        # 保存路径设置
        self.settings.setValue("paths/cookie", self.cookie_path.text())
        self.settings.setValue("paths/output", self.output_path.text())
        self.settings.setValue("paths/temp", self.temp_path.text())
        self.settings.setValue("paths/wvd", self.wvd_path.text())
        
        # 保存下载选项
        self.settings.setValue("options/save_cover", self.save_cover.isChecked())
        self.settings.setValue("options/overwrite", self.overwrite.isChecked())
        self.settings.setValue("options/disable_music_video_skip", self.disable_music_video_skip.isChecked())
        self.settings.setValue("options/save_playlist", self.save_playlist.isChecked())
        self.settings.setValue("options/synced_lyrics_only", self.synced_lyrics_only.isChecked())
        self.settings.setValue("options/no_synced_lyrics", self.no_synced_lyrics.isChecked())
        self.settings.setValue("options/read_urls_as_txt", self.read_urls_as_txt.isChecked())
        self.settings.setValue("options/no_exceptions", self.no_exceptions.isChecked())
        
        # 保存高级设置
        self.settings.setValue("advanced/download_mode", self.download_mode.currentText())
        self.settings.setValue("advanced/remux_mode", self.remux_mode.currentText())
        self.settings.setValue("advanced/cover_format", self.cover_format.currentText())
        self.settings.setValue("advanced/cover_size", self.cover_size.value())
        self.settings.setValue("advanced/truncate", self.truncate.value())
        self.settings.setValue("advanced/codec_song", self.codec_song.currentText())
        
        # 保存模板设置
        self.settings.setValue("templates/folder_album", self.template_folder_album.text())
        self.settings.setValue("templates/folder_compilation", self.template_folder_compilation.text())
        self.settings.setValue("templates/file_single_disc", self.template_file_single_disc.text())
        self.settings.setValue("templates/file_multi_disc", self.template_file_multi_disc.text())
        
        QMessageBox.information(self, "设置", "设置已保存!")
        
    def load_settings(self):
        """加载设置"""
        # 加载路径设置
        self.cookie_path.setText(self.settings.value("paths/cookie", self.get_default_cookie_path()))
        self.output_path.setText(self.settings.value("paths/output", ""))
        self.temp_path.setText(self.settings.value("paths/temp", "./temp"))
        self.wvd_path.setText(self.settings.value("paths/wvd", ""))
        
        # 加载下载选项
        self.save_cover.setChecked(self.settings.value("options/save_cover", False, type=bool))
        self.overwrite.setChecked(self.settings.value("options/overwrite", False, type=bool))
        self.disable_music_video_skip.setChecked(self.settings.value("options/disable_music_video_skip", False, type=bool))
        self.save_playlist.setChecked(self.settings.value("options/save_playlist", False, type=bool))
        self.synced_lyrics_only.setChecked(self.settings.value("options/synced_lyrics_only", False, type=bool))
        self.no_synced_lyrics.setChecked(self.settings.value("options/no_synced_lyrics", False, type=bool))
        self.read_urls_as_txt.setChecked(self.settings.value("options/read_urls_as_txt", False, type=bool))
        self.no_exceptions.setChecked(self.settings.value("options/no_exceptions", False, type=bool))
        
        # 加载高级设置
        download_mode = self.settings.value("advanced/download_mode", "ytdlp")
        index = self.download_mode.findText(download_mode)
        if index >= 0:
            self.download_mode.setCurrentIndex(index)
            
        remux_mode = self.settings.value("advanced/remux_mode", "ffmpeg")
        index = self.remux_mode.findText(remux_mode)
        if index >= 0:
            self.remux_mode.setCurrentIndex(index)
            
        cover_format = self.settings.value("advanced/cover_format", "jpg")
        index = self.cover_format.findText(cover_format)
        if index >= 0:
            self.cover_format.setCurrentIndex(index)
            
        self.cover_size.setValue(self.settings.value("advanced/cover_size", 1200, type=int))
        self.truncate.setValue(self.settings.value("advanced/truncate", 0, type=int))
        
        codec_song = self.settings.value("advanced/codec_song", "aac-legacy")
        index = self.codec_song.findText(codec_song)
        if index >= 0:
            self.codec_song.setCurrentIndex(index)
            
        # 加载模板设置
        self.template_folder_album.setText(self.settings.value("templates/folder_album", "{album_artist}/{album}"))
        self.template_folder_compilation.setText(self.settings.value("templates/folder_compilation", "Compilations/{album}"))
        self.template_file_single_disc.setText(self.settings.value("templates/file_single_disc", "{track:02d} {title}"))
        self.template_file_multi_disc.setText(self.settings.value("templates/file_multi_disc", "{disc}-{track:02d} {title}"))
        
    def reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(self, "重置设置", "确定要重置所有设置吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 清除所有设置
            self.settings.clear()
            
            # 重置界面元素为默认值
            self.cookie_path.setText(self.get_default_cookie_path())
            self.output_path.clear()
            self.temp_path.setText("./temp")
            self.wvd_path.clear()
            
            self.save_cover.setChecked(False)
            self.overwrite.setChecked(False)
            self.disable_music_video_skip.setChecked(False)
            self.save_playlist.setChecked(False)
            self.synced_lyrics_only.setChecked(False)
            self.no_synced_lyrics.setChecked(False)
            self.read_urls_as_txt.setChecked(False)
            self.no_exceptions.setChecked(False)
            
            self.download_mode.setCurrentIndex(0)  # ytdlp
            self.remux_mode.setCurrentIndex(0)     # ffmpeg
            self.cover_format.setCurrentIndex(0)   # jpg
            self.cover_size.setValue(1200)
            self.truncate.setValue(0)
            self.codec_song.setCurrentIndex(0)     # aac-legacy
            
            self.template_folder_album.setText("{album_artist}/{album}")
            self.template_folder_compilation.setText("Compilations/{album}")
            self.template_file_single_disc.setText("{track:02d} {title}")
            self.template_file_multi_disc.setText("{disc}-{track:02d} {title}")
            
            QMessageBox.information(self, "设置", "设置已重置为默认值!")
        
    def reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(self, "重置设置", "确定要重置所有设置吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 清除所有设置
            self.settings.clear()
            
            # 重置界面元素为默认值
            self.cookie_path.setText(self.get_default_cookie_path())
            self.output_path.clear()
            self.temp_path.setText("./temp")
            self.wvd_path.clear()
            
            self.save_cover.setChecked(False)
            self.overwrite.setChecked(False)
            self.disable_music_video_skip.setChecked(False)
            self.save_playlist.setChecked(False)
            self.synced_lyrics_only.setChecked(False)
            self.no_synced_lyrics.setChecked(False)
            self.read_urls_as_txt.setChecked(False)
            self.no_exceptions.setChecked(False)
            
            self.download_mode.setCurrentIndex(0)  # ytdlp
            self.remux_mode.setCurrentIndex(0)     # ffmpeg
            self.cover_format.setCurrentIndex(0)   # jpg
            self.cover_size.setValue(1200)
            self.truncate.setValue(0)
            self.codec_song.setCurrentIndex(0)     # aac-legacy
            
            self.template_folder_album.setText("{album_artist}/{album}")
            self.template_folder_compilation.setText("Compilations/{album}")
            self.template_file_single_disc.setText("{track:02d} {title}")
            self.template_file_multi_disc.setText("{disc}-{track:02d} {title}")
            
            QMessageBox.information(self, "设置", "设置已重置为默认值!")

def main():
    # 创建GUI应用
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("Apple Music Downloader")
    app.setApplicationVersion("1.0")
    
    # 创建并显示主窗口
    window = GamdlGUI()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

# 当脚本作为主程序运行时，调用main函数启动应用程序
# 这是程序的入口点，确保只有直接运行此脚本时才会启动GUI
if __name__ == "__main__":
    main()