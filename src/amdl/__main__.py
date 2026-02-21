import base64
import datetime
import json
import sys
import os
import logging
import io
import subprocess
import re
import ctypes
import traceback
import shutil
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
#2025 wenfeng110402
#2025 CrEAttivviTTy
# 正确导入cli模块
import amdl.cli
from amdl.gui_conversion import (
    convert_audio_file as shared_convert_audio_file,
    convert_downloaded_files as shared_convert_downloaded_files,
    convert_video_file as shared_convert_video_file,
    resolve_ffmpeg_executable,
)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, 
    QCheckBox, QGroupBox, QMessageBox, QProgressBar, QSizePolicy,
    QTabWidget, QComboBox, QSpinBox, QDoubleSpinBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette


def is_admin():
    """
    检查当前进程是否具有管理员权限
    :return: 如果具有管理员权限返回True，否则返回False  前提：导出文件夹在需要管理员权限的文件夹中
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def request_admin_privileges():
    """
    请求管理员权限并重新启动程序
    """
    try:
        # 获取当前Python可执行文件路径和脚本路径
        if getattr(sys, 'frozen', False):
            # 打包后的exe文件
            executable = sys.executable
            script_path = executable
        else:
            # Python脚本
            executable = sys.executable
            script_path = os.path.abspath(__file__)
        
        # 使用ShellExecuteW以管理员权限重新运行程序
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            executable, 
            f'"{script_path}"' if not getattr(sys, 'frozen', False) else '', 
            None, 
            1  # SW_SHOWNORMAL
        )
        return True
    except Exception as e:
        print(f"请求管理员权限时出错: {e}")
        return False



class DownloadThread(QThread):
    # 定义信号，用于向主线程发送日志信息、进度信息和完成状态
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, urls, cookie_file, output_dir, download_options):
        super().__init__()
        self.urls = urls
        self.cookie_file = cookie_file
        self.output_dir = output_dir
        self.download_options = download_options
        self.downloaded_files = []  # 跟踪下载的文件
        self.ffmpeg_exe = resolve_ffmpeg_executable("ffmpeg")
        
    def run(self):
        """执行下载任务"""
        try:
            success = True
            success_count = 0
            total = len(self.urls)
            
            # 发送开始下载信号
            self.log_signal.emit(f"开始下载 {total} 个项目...")
            
            # 清空下载文件列表
            self.downloaded_files = []
            
            # 遍历所有URL进行下载
            for i, url in enumerate(self.urls, 1):
                self.log_signal.emit(f"正在处理 ({i}/{total}): {url}")
                
                # 构建传递给CLI的参数列表
                args = [
                    '--cookies-path', self.cookie_file,
                    url
                ]
                
                # 添加输出路径（如果指定了）
                if self.output_dir:
                    args.extend(['--output-path', self.output_dir])
                    
                # 根据选项添加其他参数
                
                    
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
                    
                # 添加音乐视频解码格式选项
                if self.download_options.get('codec_music_video'):
                    args.extend(['--codec-music-video', self.download_options.get('codec_music_video')])
                    
                # 添加帖子视频质量选项
                if self.download_options.get('quality_post'):
                    args.extend(['--quality-post', self.download_options.get('quality_post')])
                
                # 确保传递所有必需的参数
                # 添加下载模式
                if self.download_options.get('download_mode'):
                    args.extend(['--download-mode', self.download_options.get('download_mode')])
                    
                # 添加混流模式
                if self.download_options.get('remux_mode'):
                    args.extend(['--remux-mode', self.download_options.get('remux_mode')])
                    
                # 添加封面格式
                if self.download_options.get('cover_format'):
                    args.extend(['--cover-format', self.download_options.get('cover_format')])
                    
                # 添加封面尺寸
                if self.download_options.get('cover_size'):
                    args.extend(['--cover-size', str(self.download_options.get('cover_size'))])
                    
                # 添加截断长度
                if self.download_options.get('truncate'):
                    args.extend(['--truncate', str(self.download_options.get('truncate'))])
                    
                # 添加同步歌词格式
                if self.download_options.get('synced_lyrics_format'):
                    args.extend(['--synced-lyrics-format', self.download_options.get('synced_lyrics_format')])
                
                # 创建字符串IO对象来捕获日志输出
                log_stream = io.StringIO()
                
                try:
                    # 重定向stdout和stderr以捕获CLI输出
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = log_stream
                    sys.stderr = log_stream
                    
                    # 添加调试信息，打印实际传递给CLI的参数
                    self.log_signal.emit(f"    传递给CLI的参数: {' '.join(args)}")
                    
                    # 调用CLI功能执行下载
                    amdl.cli.main(args, standalone_mode=False)
                    success_count += 1
                    self.log_signal.emit(f"    下载完成!")
                except SystemExit as e:
                    # click通过SystemExit来处理完成状态
                    if e.code == 0:
                        success_count += 1
                        self.log_signal.emit(f"    下载完成!")
                    else:
                        self.log_signal.emit(f"    下载失败! 错误代码: {e.code}")
                        success = False
                        # 捕获并显示错误信息
                        log_output = log_stream.getvalue()
                        if log_output:
                            self.log_signal.emit(f"    错误详情: {log_output}")
                            
                        # 检查是否是认证错误
                        if "Authentication required" in log_output or "Invalid cookie" in log_output:
                            self.log_signal.emit("    错误: Cookie文件无效或需要重新登录Apple Music账户")
                            
                        # 检查是否是网络错误
                        if "ERROR: Unable to extract video data" in log_output or "HTTP Error 403" in log_output:
                            self.log_signal.emit("    错误: 网络连接问题或Apple Music服务器错误")
                except Exception as e:
                    self.log_signal.emit(f"    下载失败! 异常: {str(e)}")
                    success = False
                    # 捕获并显示错误信息
                    log_output = log_stream.getvalue()
                    if log_output:
                        self.log_signal.emit(f"    错误详情: {log_output}")
                        
                    # 记录异常类型和堆栈跟踪
                    self.log_signal.emit(f"    异常类型: {type(e).__name__}")
                    self.log_signal.emit(f"    堆栈跟踪: {traceback.format_exc()}")
                finally:
                    # 恢复stdout和stderr
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    
                    # 显示捕获的日志并提取下载的文件路径
                    log_output = log_stream.getvalue()
                    if log_output:
                        for line in log_output.splitlines():
                            if line.strip():  # 只显示非空行
                                self.log_signal.emit(f"    {line}")
                                # 尝试从日志中提取下载的文件路径
                                self.extract_downloaded_file_path(line)
                    else:
                        self.log_signal.emit("    没有捕获到日志输出")
                    
                    # 更新进度
                    progress = int((i / total) * 100)
                    self.progress_signal.emit(progress)
            
            # 所有下载完成后，执行格式转换（如果需要）
            audio_format = self.download_options.get('audio_format')
            video_format = self.download_options.get('video_format')
            
            self.log_signal.emit(f"准备转换 {len(self.downloaded_files)} 个下载的文件")
            for file_path in self.downloaded_files:
                self.log_signal.emit(f"  待转换文件: {file_path}")
            
            if (audio_format and audio_format != "保持原格式") or (video_format and video_format != "保持原格式"):
                self.log_signal.emit("开始执行格式转换...")
                self.convert_downloaded_files(audio_format, video_format)
            
            # 发送完成信号
            self.finished_signal.emit(success and success_count > 0)
        except MemoryError as e:
            error_msg = "内存不足错误: 下载过程中发生内存不足"
            self.log_signal.emit(error_msg)
            self.log_signal.emit("请尝试以下解决方案:")
            self.log_signal.emit("1. 关闭其他占用内存的程序")
            self.log_signal.emit("2. 减少同时下载的项目数量")
            self.log_signal.emit("3. 使用更低的封面尺寸设置")
            self.finished_signal.emit(False)
        except TimeoutError as e:
            error_msg = "操作超时: 下载过程中发生超时"
            self.log_signal.emit(error_msg)
            self.log_signal.emit("请检查网络连接是否正常")
            self.finished_signal.emit(False)
        except PermissionError as e:
            error_msg = f"权限错误: 无法访问文件或目录 - {str(e)}"
            self.log_signal.emit(error_msg)
            self.log_signal.emit("请确保有权限访问指定的文件和目录")
            self.finished_signal.emit(False)
        except Exception as e:
            error_msg = f"下载过程中发生未知错误: {str(e)}\n{traceback.format_exc()}"
            self.log_signal.emit(error_msg)
            
            # 记录系统信息用于调试
            self.log_signal.emit(f"Python版本: {sys.version}")
            self.log_signal.emit(f"操作系统: {os.name}")
            self.log_signal.emit(f"系统信息: {os.uname() if hasattr(os, 'uname') else 'N/A'}")
            
            self.finished_signal.emit(False)
    
    def extract_downloaded_file_path(self, log_line):
        """
        从日志行中提取下载的文件路径
        :param log_line: 日志行
        """
        # 尝试匹配多种可能的下载完成消息格式
        # 匹配类似 "Download completed: path/to/file.m4a" 的模式
        match1 = re.search(r"[Dd]ownload.*completed.*[:：]\s*(.+?\.(?:m4a|mp4|mov))", log_line)
        # 匹配类似 "已保存到: path/to/file.m4a" 的模式
        match2 = re.search(r"(?:已保存到|保存到|Saved to).*[:：]\s*(.+?\.(?:m4a|mp4|mov))", log_line)
        # 匹配类似 "已完成: path/to/file.m4a" 的模式
        match3 = re.search(r"(?:已完成|完成).*[:：]\s*(.+?\.(?:m4a|mp4|mov))", log_line)
        # 匹配可能的文件路径模式
        match4 = re.search(r"([^\s]+?\.(?:m4a|mp4|mov))", log_line)
        
        file_path = None
        if match1:
            file_path = match1.group(1).strip()
        elif match2:
            file_path = match2.group(1).strip()
        elif match3:
            file_path = match3.group(1).strip()
        elif match4 and ('saved' in log_line.lower() or '完成' in log_line or 'success' in log_line.lower()):
            # 只有在日志行包含成功相关关键词时才考虑这种匹配
            file_path = match4.group(1).strip()
        
        if file_path:
            # 转换为绝对路径
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
            # 避免重复添加
            if file_path not in self.downloaded_files:
                self.downloaded_files.append(file_path)
                self.log_signal.emit(f"    检测到下载文件: {file_path}")
    
    def convert_downloaded_files(self, audio_format, video_format):
        """
        在下载完成后执行格式转换，只转换实际下载的文件
        :param audio_format: 目标音频格式
        :param video_format: 目标视频格式
        """
        self.downloaded_files = shared_convert_downloaded_files(
            self.downloaded_files,
            audio_format,
            video_format,
            self.ffmpeg_exe,
            self.log_signal.emit,
        )
    
    def convert_audio_file(self, source_path, target_path, target_format):
        """
        转换音频文件格式
        :param source_path: 源文件路径
        :param target_path: 目标文件路径
        :param target_format: 目标格式
        :return: 转换是否成功
        """
        return shared_convert_audio_file(
            source_path,
            target_path,
            target_format,
            self.ffmpeg_exe,
            self.log_signal.emit,
        )
    
    def convert_video_file(self, source_path, target_path, target_format):
        """
        转换视频文件格式
        :param source_path: 源文件路径
        :param target_path: 目标文件路径
        :param target_format: 目标格式
        :return: 转换是否成功
        """
        return shared_convert_video_file(
            source_path,
            target_path,
            target_format,
            self.ffmpeg_exe,
            self.log_signal.emit,
        )

class GamdlGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apple Music Downloader")
        self.setGeometry(100, 100, 1000, 700)
        
        # 应用设置
        self.settings = QSettings('amdl', 'AppleMusicDownloader')
        
        # 下载线程
        self.download_thread = None
        
        # 创建界面
        self.create_widgets()
        
        # 加载保存的设置
        self.load_settings()
        
    def get_default_tool_path(self, tool_name):
        """
        获取工具的默认路径
        首先检查当前目录下的tools文件夹，如果找不到则返回默认名称
        """
        try:
            # 获取程序所在目录
            if getattr(sys, 'frozen', False):
                # 打包环境
                app_path = Path(sys.executable).parent.absolute()
            else:
                # 开发环境
                app_path = Path(__file__).parent.absolute()
            
            # 检查tools目录下的工具
            tool_path = app_path / "tools" / tool_name
            if tool_path.exists():
                return str(tool_path)
            
            # 如果tools目录中没有找到，则返回默认名称
            # 让系统在PATH中查找
            return tool_name.split('.')[0]
        except Exception as e:
            print(f"获取工具路径时出错: {e}")
            return tool_name.split('.')[0]
        
    def get_default_cookie_path(self):
        """
        获取默认的cookie文件路径
        自动查找程序目录下的cookie文件
        """
        try:
            # 获取程序所在目录
            if getattr(sys, 'frozen', False):
                # 打包环境
                app_path = Path(sys.executable).parent.absolute()
            else:
                # 开发环境
                app_path = Path(__file__).parent.absolute()
            
            # 常见的cookie文件名
            cookie_filenames = ["cookies.txt", "cookie.txt", "cookies", "cookie"]
            
            # 查找目录下的cookie文件
            for filename in cookie_filenames:
                cookie_path = app_path / filename
                if cookie_path.exists():
                    return str(cookie_path)
            
            # 如果没找到，返回默认路径
            return str(app_path / "cookies.txt")
        except Exception as e:
            print(f"获取cookie路径时出错: {e}")
            return "./cookies.txt"
        
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
        self.overwrite = QCheckBox("覆盖已存在文件")
        self.disable_music_video_skip = QCheckBox("不跳过音乐视频")
        self.save_playlist = QCheckBox("保存播放列表")
        self.synced_lyrics_only = QCheckBox("仅下载同步歌词")
        self.no_synced_lyrics = QCheckBox("不下载同步歌词")
        self.read_urls_as_txt = QCheckBox("将URL作为文本文件读取")
        self.no_exceptions = QCheckBox("不显示异常信息")
        
        
        options_layout.addWidget(self.overwrite, 3, 0)
        options_layout.addWidget(self.disable_music_video_skip, 0, 0)
        options_layout.addWidget(self.save_playlist, 1, 0)
        options_layout.addWidget(self.synced_lyrics_only, 0, 1)
        options_layout.addWidget(self.no_synced_lyrics, 1, 1)
        options_layout.addWidget(self.read_urls_as_txt, 2, 0)
        options_layout.addWidget(self.no_exceptions, 2, 1)
        
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
        
        # 音乐视频解码格式
        advanced_layout.addWidget(QLabel("音乐视频解码格式:"), 8, 0)
        self.codec_music_video = QComboBox()
        self.codec_music_video.addItems(["h264", "h265", "ask"])
        advanced_layout.addWidget(self.codec_music_video, 8, 1)
        
        # 帖子视频质量
        advanced_layout.addWidget(QLabel("帖子视频质量:"), 9, 0)
        self.quality_post = QComboBox()
        self.quality_post.addItems(["best", "ask"])
        advanced_layout.addWidget(self.quality_post, 9, 1)
        
        # 添加音频格式转换选项
        advanced_layout.addWidget(QLabel("音频格式转换:"), 10, 0)
        self.audio_format = QComboBox()
        self.audio_format.addItems(["保持原格式", "mp3", "flac", "wav", "aac", "m4a", "ogg", "wma"])
        advanced_layout.addWidget(self.audio_format, 10, 1)
        
        # 添加视频格式转换选项
        advanced_layout.addWidget(QLabel("视频格式转换:"), 11, 0)
        self.video_format = QComboBox()
        self.video_format.addItems(["保持原格式", "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm"])
        advanced_layout.addWidget(self.video_format, 11, 1)
        
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
        
    def reset_settings(self):
        """重置设置到默认值"""
        reply = QMessageBox.question(
            self, 
            "重置设置", 
            "确定要将所有设置重置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 重置所有设置控件到默认值
            self.temp_path.setText("./temp")
            self.wvd_path.setText("")
            self.download_mode.setCurrentText("ytdlp")
            self.remux_mode.setCurrentText("ffmpeg")
            self.cover_format.setCurrentText("jpg")
            self.cover_size.setValue(1200)
            self.truncate.setValue(0)
            self.codec_song.setCurrentText("aac-legacy")
            self.codec_music_video.setCurrentText("h264")
            self.quality_post.setCurrentText("best")
            self.template_folder_album.setText("{album_artist}/{album}")
            self.template_folder_compilation.setText("Compilations/{album}")
            self.template_file_single_disc.setText("{track:02d} {title}")
            self.template_file_multi_disc.setText("{disc}-{track:02d} {title}")
            self.audio_format.setCurrentText("保持原格式")
            self.video_format.setCurrentText("保持原格式")
            QMessageBox.information(self, "设置已重置", "所有设置已重置为默认值")
        
    def create_license_tab(self, parent):
        # 许可证标签页
        license_widget = QWidget()
        parent.addTab(license_widget, "许可证")
        
        layout = QVBoxLayout(license_widget)
        
        # 许可证信息区域
        license_info_group = QGroupBox("许可证信息")
        license_info_layout = QVBoxLayout(license_info_group)
        
        # 许可证文件上传
        license_file_layout = QHBoxLayout()
        license_file_layout.addWidget(QLabel("许可证文件:"))
        self.license_path = QLineEdit()
        self.license_path.setPlaceholderText("上传许可证文件...")
        license_file_layout.addWidget(self.license_path)
        license_upload_btn = QPushButton("上传")
        license_upload_btn.clicked.connect(self.upload_license)
        license_file_layout.addWidget(license_upload_btn)
        
        # 添加更换许可证按钮
        self.license_change_btn = QPushButton("更换许可证")
        self.license_change_btn.clicked.connect(self.change_license)
        self.license_change_btn.setEnabled(False)  # 初始时禁用
        license_file_layout.addWidget(self.license_change_btn)
        
        license_info_layout.addLayout(license_file_layout)
        
        # 许可证状态
        self.license_status = QLabel("请上传许可证文件")
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
        </ul>
        <p><b>注意：</b>非永久许可证到期后会自动删除，需要重新上传新的许可证文件。</p>
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # 添加弹性空间
        layout.addStretch()
        
    def upload_license(self):
        """上传许可证文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "上传许可证文件", "", "License Files (*.key);;All Files (*)"
        )
        
        if file_path:
            # 将许可证文件复制到程序目录并命名为license.key
            try:
                target_path = os.path.join(os.path.dirname(sys.argv[0]), "license.key")
                shutil.copy2(file_path, target_path)
                self.license_path.setText(target_path)
                is_valid = self.validate_selected_license()
                
                # 如果验证通过，启用更换按钮
                if is_valid:
                    self.license_change_btn.setEnabled(True)
                    # 不再保存许可证路径到设置
                    QMessageBox.information(self, "成功", "许可证文件已成功上传并验证通过!")
                else:
                    QMessageBox.critical(self, "错误", "许可证文件上传失败或验证未通过!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"上传许可证文件失败: {str(e)}")
                
    def change_license(self):
        """更换许可证文件"""
        reply = QMessageBox.question(self, "更换许可证", "确定要更换许可证文件吗？当前许可证将被替换。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.upload_license()
            
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
                # 启用更换许可证按钮
                self.license_change_btn.setEnabled(True)
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
                # 禁用更换许可证按钮
                self.license_change_btn.setEnabled(False)
            return is_valid
        return False
            
    def check_initial_license(self):
        """检查初始许可证"""
        # 始终在当前目录查找license.key文件
        default_license = "license.key"
        
        # 检查当前目录是否存在许可证文件
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
                # 启用更换许可证按钮
                self.license_change_btn.setEnabled(True)
            else:
                self.handle_invalid_license(message)
                # 清除许可证路径输入框
                self.license_path.clear()
        else:
            # 没有找到许可证文件
            current_dir = os.getcwd()
            message = f"请上传许可证文件 (当前目录: {current_dir})"
            self.license_status.setText(message)
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
            # 禁用更换许可证按钮
            self.license_change_btn.setEnabled(False)
            # 清除许可证路径输入框
            self.license_path.clear()
            
    def handle_invalid_license(self, message):
        """处理无效许可证"""
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
        QMessageBox.critical(self, "许可证错误", f"{message}\n请确保上传了有效的许可证文件")
        # 禁用更换许可证按钮
        self.license_change_btn.setEnabled(False)
        
    def check_license_status(self):
        """定期检查许可证状态"""
        # 始终在当前目录查找license.key文件
        default_license = "license.key"
        
        # 检查当前目录是否存在许可证文件
        if os.path.exists(default_license):
            # 如果界面上没有显示许可证路径或者路径不正确，则更新
            if self.license_path.text() != default_license:
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
                # 启用更换许可证按钮
                self.license_change_btn.setEnabled(True)
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
                # 禁用更换许可证按钮
                self.license_change_btn.setEnabled(False)
                
                # 如果许可证无效且不是永久许可证，则删除过期的许可证文件
                try:
                    with open(default_license, "r") as f:
                        key_content = f.read().strip()
                    key_json = base64.b64decode(key_content.encode()).decode()
                    key_data = json.loads(key_json)
                    
                    # 只有非永久许可证才自动删除
                    if not key_data.get("lifetime", False):
                        os.remove(default_license)
                        self.license_path.clear()
                        self.license_status.setText("许可证已过期并自动删除，请上传新许可证")
                        self.license_status.setStyleSheet(""""
                            QLabel {
                                color: red;
                                font-weight: bold;
                                padding: 10px;
                                border: 1px solid #ccc;
                                border-radius: 5px;
                                background-color: #fff0f0;
                            }
                        """)
                except Exception:
                    pass  # 如果删除过程中出错，忽略错误
        else:
            # 没有找到许可证文件
            self.license_path.clear()
            current_dir = os.getcwd()
            message = f"请上传许可证文件 (当前目录: {current_dir})"
            self.license_status.setText(message)
            self.license_status.setStyleSheet(""""
                QLabel {
                    color: blue;
                    font-weight: bold;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    background-color: #f9f9f9;
                }
            """)
            # 禁用更换许可证按钮
            self.license_change_btn.setEnabled(False)
                
    def start_download(self):
        """开始下载"""
        try:
            # 获取URL列表
            urls_text = self.url_input.toPlainText()
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
            
            cookie_file = self.cookie_path.text()
            output_dir = self.output_path.text()
            
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
                'overwrite': self.overwrite.isChecked(),
                'disable_music_video_skip': self.disable_music_video_skip.isChecked(),
                'save_playlist': self.save_playlist.isChecked(),
                'synced_lyrics_only': self.synced_lyrics_only.isChecked(),
                'no_synced_lyrics': self.no_synced_lyrics.isChecked(),
                'read_urls_as_txt': self.read_urls_as_txt.isChecked(),
                'no_exceptions': self.no_exceptions.isChecked(),
                'codec_song': self.codec_song.currentText(),
                'codec_music_video': self.codec_music_video.currentText(),
                'quality_post': self.quality_post.currentText(),
                'download_mode': self.download_mode.currentText(),
                'remux_mode': self.remux_mode.currentText(),
                'cover_format': self.cover_format.currentText(),
                'cover_size': self.cover_size.value(),
                'truncate': self.truncate.value() if self.truncate.value() > 0 else None,
                'synced_lyrics_format': 'lrc',
                'temp_path': self.temp_path.text(),
                'wvd_path': self.wvd_path.text(),
                'template_folder_album': self.template_folder_album.text(),
                'template_folder_compilation': self.template_folder_compilation.text(),
                'template_file_single_disc': self.template_file_single_disc.text(),
                'template_file_multi_disc': self.template_file_multi_disc.text(),
                'audio_format': self.audio_format.currentText(),
                'video_format': self.video_format.currentText()
            }
            
            # 禁用下载按钮，防止重复点击
            self.download_btn.setEnabled(False)
            self.download_btn.setText("下载中...")
            
            # 创建并启动下载线程
            self.download_thread = DownloadThread(urls, cookie_file, output_dir, download_options)
            self.download_thread.log_signal.connect(self.append_log)
            self.download_thread.progress_signal.connect(self.update_progress)
            self.download_thread.finished_signal.connect(self.download_finished)
            self.download_thread.start()
        except Exception as e:
            error_msg = f"启动下载时发生错误: {str(e)}\n{traceback.format_exc()}"
            self.append_log(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            # 恢复下载按钮
            self.download_btn.setEnabled(True)
            self.download_btn.setText("开始下载")
        
    def append_log(self, message):
        """添加日志信息"""
        try:
            self.log_text.append(message)
        except Exception as e:
            print(f"添加日志时出错: {e}")
        
    def update_progress(self, value):
        """更新进度条"""
        try:
            self.progress_bar.setValue(value)
        except Exception as e:
            print(f"更新进度条时出错: {e}")
        
    def download_finished(self, success):
        """下载完成回调"""
        try:
            # 恢复下载按钮
            self.download_btn.setEnabled(True)
            self.download_btn.setText("开始下载")
            
            if success:
                self.statusBar().showMessage("下载完成", 5000)
                QMessageBox.information(self, "成功", "下载已完成!")
            else:
                self.statusBar().showMessage("下载失败", 5000)
                QMessageBox.critical(self, "错误", "下载过程中发生错误，请查看日志!")
        except Exception as e:
            error_msg = f"处理下载完成时发生错误: {str(e)}\n{traceback.format_exc()}"
            self.append_log(error_msg)
            
    def clear_log(self):
        """清除日志"""
        try:
            self.log_text.clear()
        except Exception as e:
            print(f"清除日志时出错: {e}")
        
    def closeEvent(self, event):
        """关闭事件"""
        try:
            # 保存设置
            self.save_settings()
            event.accept()
        except Exception as e:
            print(f"关闭事件处理时出错: {e}")
            event.accept()
        
    def save_settings(self):
        """保存设置"""
        try:
            self.settings.setValue("cookie_path", self.cookie_path.text())
            self.settings.setValue("output_path", self.output_path.text())
            self.settings.setValue("overwrite", self.overwrite.isChecked())
            self.settings.setValue("disable_music_video_skip", self.disable_music_video_skip.isChecked())
            self.settings.setValue("save_playlist", self.save_playlist.isChecked())
            self.settings.setValue("synced_lyrics_only", self.synced_lyrics_only.isChecked())
            self.settings.setValue("no_synced_lyrics", self.no_synced_lyrics.isChecked())
            self.settings.setValue("read_urls_as_txt", self.read_urls_as_txt.isChecked())
            self.settings.setValue("no_exceptions", self.no_exceptions.isChecked())
            self.settings.setValue("codec_song", self.codec_song.currentText())
            self.settings.setValue("codec_music_video", self.codec_music_video.currentText())
            self.settings.setValue("quality_post", self.quality_post.currentText())
            self.settings.setValue("download_mode", self.download_mode.currentText())
            self.settings.setValue("remux_mode", self.remux_mode.currentText())
            self.settings.setValue("cover_format", self.cover_format.currentText())
            self.settings.setValue("cover_size", self.cover_size.value())
            self.settings.setValue("truncate", self.truncate.value())
            self.settings.setValue("temp_path", self.temp_path.text())
            self.settings.setValue("wvd_path", self.wvd_path.text())
            self.settings.setValue("template_folder_album", self.template_folder_album.text())
            self.settings.setValue("template_folder_compilation", self.template_folder_compilation.text())
            self.settings.setValue("template_file_single_disc", self.template_file_single_disc.text())
            self.settings.setValue("template_file_multi_disc", self.template_file_multi_disc.text())
            self.settings.setValue("audio_format", self.audio_format.currentText())
            self.settings.setValue("video_format", self.video_format.currentText())
        except Exception as e:
            print(f"保存设置时出错: {e}")
        
    def load_settings(self):
        """加载设置"""
        try:
            self.cookie_path.setText(self.settings.value("cookie_path", ""))
            self.output_path.setText(self.settings.value("output_path", ""))
            self.overwrite.setChecked(self.settings.value("overwrite", False, type=bool))
            self.disable_music_video_skip.setChecked(self.settings.value("disable_music_video_skip", False, type=bool))
            self.save_playlist.setChecked(self.settings.value("save_playlist", False, type=bool))
            self.synced_lyrics_only.setChecked(self.settings.value("synced_lyrics_only", False, type=bool))
            self.no_synced_lyrics.setChecked(self.settings.value("no_synced_lyrics", False, type=bool))
            self.read_urls_as_txt.setChecked(self.settings.value("read_urls_as_txt", False, type=bool))
            self.no_exceptions.setChecked(self.settings.value("no_exceptions", False, type=bool))
            self.codec_song.setCurrentText(self.settings.value("codec_song", "aac-legacy"))
            self.codec_music_video.setCurrentText(self.settings.value("codec_music_video", "h264"))
            self.quality_post.setCurrentText(self.settings.value("quality_post", "best"))
            self.download_mode.setCurrentText(self.settings.value("download_mode", "ytdlp"))
            self.remux_mode.setCurrentText(self.settings.value("remux_mode", "ffmpeg"))
            self.cover_format.setCurrentText(self.settings.value("cover_format", "jpg"))
            self.cover_size.setValue(self.settings.value("cover_size", 1200, type=int))
            self.truncate.setValue(self.settings.value("truncate", 0, type=int))
            self.temp_path.setText(self.settings.value("temp_path", "./temp"))
            self.wvd_path.setText(self.settings.value("wvd_path", ""))
            self.template_folder_album.setText(self.settings.value("template_folder_album", "{album_artist}/{album}"))
            self.template_folder_compilation.setText(self.settings.value("template_folder_compilation", "Compilations/{album}"))
            self.template_file_single_disc.setText(self.settings.value("template_file_single_disc", "{track:02d} {title}"))
            self.template_file_multi_disc.setText(self.settings.value("template_file_multi_disc", "{disc}-{track:02d} {title}"))
            self.audio_format.setCurrentText(self.settings.value("audio_format", "保持原格式"))
            self.video_format.setCurrentText(self.settings.value("video_format", "保持原格式"))
        except Exception as e:
            print(f"加载设置时出错: {e}")

def main():
    # 检查是否具有管理员权限，如果没有则请求权限
    if not is_admin():
        print("请求管理员权限...")
        if request_admin_privileges():
            sys.exit(0)  # 成功请求权限，退出当前进程
        else:
            print("无法获取管理员权限，程序将退出")
            input("按回车键退出...")
            sys.exit(1)  # 无法请求权限，退出
    
    try:
        app = QApplication(sys.argv)
        
        # 设置应用程序属性
        app.setApplicationName("AppleMusic Downloader")
        app.setApplicationVersion("3.1.0")
        
        # 创建并显示主窗口
        window = GamdlGUI()
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
    except Exception as e:
        print(f"发生未捕获异常: {str(e)}")
        traceback.print_exc()
        input("按回车键退出...")

# 当脚本作为主程序运行时，调用main函数启动应用程序
# 这是程序的入口点，确保只有直接运行此脚本时才会启动GUI
if __name__ == "__main__":
    main()