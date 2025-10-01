# fluent ui
# 9/14修改到628行，添加info界面
import sys
import os
import io
import re
import traceback
import ctypes
import subprocess
from pathlib import Path

import gamdl.cli

# PyQt6 imports for Fluent UI
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, 
    QCheckBox, QGroupBox, QMessageBox, QProgressBar, QSizePolicy,
    QTabWidget, QComboBox, QSpinBox, QDoubleSpinBox, QScrollArea, QFrame, QStatusBar,
    QListWidget, QStackedWidget, QSplitter, QToolBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QAction, QIcon

# Fluent UI imports for PyQt6
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, InfoBar, InfoBarPosition,
    PushButton, CheckBox, ComboBox, SpinBox, DoubleSpinBox, LineEdit, TextEdit,
    ProgressBar, SettingCardGroup, PushSettingCard, ScrollArea, ExpandLayout,
    TransparentToolButton, FluentIcon, CardWidget, SubtitleLabel, BodyLabel,
    HyperlinkButton, PrimaryPushButton, ToggleButton, SwitchButton, 
    FolderListSettingCard, OptionsSettingCard, CustomColorSettingCard, Theme, setTheme,
    TransparentTogglePushButton, Pivot, SegmentedWidget
)


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
    # 定义信号，用于向主线程发送进度信息和完成状态
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, urls, cookie_file, output_dir, download_options, log_callback):
        super().__init__()
        self.urls = urls
        self.cookie_file = cookie_file
        self.output_dir = output_dir
        self.download_options = download_options
        self.downloaded_files = []  # 跟踪下载的文件
        self.log_callback = log_callback  # 直接日志回调函数
        
    def run(self):
        """执行下载任务"""
        try:
            success = True
            success_count = 0
            total = len(self.urls)
            
            # 发送开始下载信号
            self.log_callback.emit(f"开始下载 {total} 个项目...")
            
            # 清空下载文件列表
            self.downloaded_files = []
            
            # 遍历所有URL进行下载
            for i, url in enumerate(self.urls, 1):
                self.log_callback.emit(f"正在处理 ({i}/{total}): {url}")
                
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
                    self.log_callback.emit(f"    传递给CLI的参数: {' '.join(args)}")
                    
                    # 调用CLI功能执行下载
                    gamdl.cli.main(args, standalone_mode=False)
                    success_count += 1
                    self.log_callback.emit(f"    下载完成!")
                except SystemExit as e:
                    # click通过SystemExit来处理完成状态
                    if e.code == 0:
                        success_count += 1
                        self.log_callback.emit(f"    下载完成!")
                    else:
                        self.log_callback.emit(f"    下载失败! 错误代码: {e.code}")
                        success = False
                        # 捕获并显示错误信息
                        log_output = log_stream.getvalue()
                        if log_output:
                            for line in log_output.splitlines():
                                if line.strip():  # 只显示非空行
                                    self.log_callback.emit(line)
                except Exception as e:
                    self.log_callback.emit(f"    下载失败! 异常: {str(e)}")
                    success = False
                    # 捕获并显示错误信息
                    log_output = log_stream.getvalue()
                    if log_output:
                        for line in log_output.splitlines():
                            if line.strip():  # 只显示非空行
                                self.log_callback.emit(line)
                    # 记录异常类型和堆栈跟踪
                    self.log_callback.emit(f"    异常类型: {type(e).__name__}")
                    self.log_callback.emit(f"    堆栈跟踪: {traceback.format_exc()}")
                finally:
                    # 恢复stdout和stderr
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    
                    # 显示捕获的日志并提取下载的文件路径
                    log_output = log_stream.getvalue()
                    if log_output:
                        for line in log_output.splitlines():
                            if line.strip():  # 只显示非空行
                                # 直接输出原始日志，不添加额外的前缀
                                self.log_callback.emit(line)
                                # 尝试从日志中提取下载的文件路径
                                self.extract_downloaded_file_path(line)
                    else:
                        self.log_callback.emit("    没有捕获到日志输出")
                    
                    # 更新进度
                    progress = int((i / total) * 100)
                    self.progress_signal.emit(progress)
            
            # 所有下载完成后，执行格式转换（如果需要）
            audio_format = self.download_options.get('audio_format')
            video_format = self.download_options.get('video_format')
            
            self.log_callback.emit(f"准备转换 {len(self.downloaded_files)} 个下载的文件")
            for file_path in self.downloaded_files:
                self.log_callback.emit(f"  待转换文件: {file_path}")
            
            if (audio_format and audio_format != "保持原格式") or (video_format and video_format != "保持原格式"):
                self.log_callback.emit("开始执行格式转换...")
                self.convert_downloaded_files(audio_format, video_format)
            
            # 发送完成信号
            self.finished_signal.emit(success and success_count > 0)
        except MemoryError as e:
            error_msg = "内存不足错误: 下载过程中发生内存不足"
            self.log_callback.emit(error_msg)
            self.log_callback.emit("请尝试以下解决方案:")
            self.log_callback.emit("1. 关闭其他占用内存的程序")
            self.log_callback.emit("2. 减少同时下载的项目数量")
            self.log_callback.emit("3. 使用更低的封面尺寸设置")
            self.finished_signal.emit(False)
        except TimeoutError as e:
            error_msg = "操作超时: 下载过程中发生超时"
            self.log_callback.emit(error_msg)
            self.log_callback.emit("请检查网络连接是否正常")
            self.finished_signal.emit(False)
        except PermissionError as e:
            error_msg = f"权限错误: 无法访问文件或目录 - {str(e)}"
            self.log_callback.emit(error_msg)
            self.log_callback.emit("请确保有权限访问指定的文件和目录")
            self.finished_signal.emit(False)
        except Exception as e:
            error_msg = f"下载过程中发生未知错误: {str(e)}\n{traceback.format_exc()}"
            self.log_callback.emit(error_msg)
            
            # 记录系统信息用于调试
            self.log_callback.emit(f"Python版本: {sys.version}")
            self.log_callback.emit(f"操作系统: {os.name}")
            self.log_callback.emit(f"系统信息: {os.uname() if hasattr(os, 'uname') else 'N/A'}")
            
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
                self.log_callback.emit(f"    检测到下载文件: {file_path}")
    
    def convert_downloaded_files(self, audio_format, video_format):
        """
        在下载完成后执行格式转换，只转换实际下载的文件
        :param audio_format: 目标音频格式
        :param video_format: 目标视频格式
        """
        try:
            # 获取输出目录
            output_dir = self.output_dir if self.output_dir else "./"
            self.log_callback.emit(f"在目录中查找最近下载的文件: {output_dir}")
            
            # 查找最近修改的媒体文件（假设在下载过程中创建的）
            import time
            current_time = time.time()
            recently_modified_files = []
            
            # 查找最近10分钟内修改的媒体文件
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file.endswith((".m4a", ".mp4", ".mov")):
                        file_path = os.path.join(root, file)
                        file_modified_time = os.path.getmtime(file_path)
                        # 如果文件是最近10分钟内修改的，认为是刚刚下载的
                        if current_time - file_modified_time < 600:  # 600秒 = 10分钟
                            recently_modified_files.append(file_path)
                            self.log_callback.emit(f"    检测到最近下载的文件: {file_path}")
            
            self.log_callback.emit(f"准备转换 {len(recently_modified_files)} 个最近下载的文件")
            
            # 查找需要转换的文件
            converted_count = 0
            
            if audio_format and audio_format != "保持原格式":
                # 处理音频文件
                for file_path in recently_modified_files:
                    if file_path.endswith((".m4a", ".mp4")):
                        converted_path = os.path.splitext(file_path)[0] + f".{audio_format}"
                        
                        # 检查目标文件是否已存在
                        if os.path.exists(converted_path):
                            self.log_callback.emit(f"    跳过 {os.path.basename(file_path)} (目标文件已存在)")
                            continue
                        
                        # 执行音频转换
                        if self.convert_audio_file(file_path, converted_path, audio_format):
                            converted_count += 1
                            self.log_callback.emit(f"    成功转换 {os.path.basename(file_path)} 为 {audio_format}")
                            # 转换成功后删除原文件
                            try:
                                os.remove(file_path)
                                self.log_callback.emit(f"    已删除原文件 {os.path.basename(file_path)}")
                            except Exception as e:
                                self.log_callback.emit(f"    删除原文件失败 {os.path.basename(file_path)}: {str(e)}")
                        else:
                            self.log_callback.emit(f"    转换失败 {os.path.basename(file_path)}")
            
            if video_format and video_format != "保持原格式":
                # 处理视频文件
                for file_path in recently_modified_files:
                    if file_path.endswith((".mov", ".mp4")):
                        converted_path = os.path.splitext(file_path)[0] + f".{video_format}"
                        
                        # 检查目标文件是否已存在
                        if os.path.exists(converted_path):
                            self.log_callback.emit(f"    跳过 {os.path.basename(file_path)} (目标文件已存在)")
                            continue
                        
                        # 执行视频转换
                        if self.convert_video_file(file_path, converted_path, video_format):
                            converted_count += 1
                            self.log_callback.emit(f"    成功转换 {os.path.basename(file_path)} 为 {video_format}")
                            # 转换成功后删除原文件
                            try:
                                os.remove(file_path)
                                self.log_callback.emit(f"    已删除原文件 {os.path.basename(file_path)}")
                            except Exception as e:
                                self.log_callback.emit(f"    删除原文件失败 {os.path.basename(file_path)}: {str(e)}")
                        else:
                            self.log_callback.emit(f"    转换失败 {os.path.basename(file_path)}")
            
            self.log_callback.emit(f"格式转换完成，共转换 {converted_count} 个文件")
        except Exception as e:
            error_msg = f"格式转换过程中发生错误: {str(e)}\n{traceback.format_exc()}"
            self.log_callback.emit(error_msg)
    
    def convert_audio_file(self, source_path, target_path, target_format):
        """
        转换音频文件格式
        :param source_path: 源文件路径
        :param target_path: 目标文件路径
        :param target_format: 目标格式
        :return: 转换是否成功
        """
        try:
            # 构建FFmpeg命令，使用-map 0来保留所有流，包括元数据
            if target_format == "mp3":
                # MP3格式，使用320kbps比特率，并确保保留元数据
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:a", "libmp3lame", "-b:a", "320k", 
                    "-map_metadata", "0", "-id3v2_version", "3", "-write_id3v1", "1",
                    "-f", "mp3",
                    target_path
                ]
            elif target_format == "flac":
                # FLAC无损格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:a", "flac", 
                    "-map_metadata", "0",
                    "-f", "flac",
                    target_path
                ]
            elif target_format == "wav":
                # WAV格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:a", "pcm_s16le", 
                    "-map_metadata", "0",
                    "-f", "wav",
                    target_path
                ]
            elif target_format == "aac":
                # AAC格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:a", "aac", "-b:a", "256k",
                    "-map_metadata", "0",
                    target_path
                ]
            elif target_format == "m4a":
                # M4A格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:a", "aac", "-b:a", "256k",
                    "-map_metadata", "0",
                    "-f", "mp4",
                    target_path
                ]
            elif target_format == "ogg":
                # OGG格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:a", "libvorbis", "-q:a", "5",
                    "-map_metadata", "0",
                    target_path
                ]
            elif target_format == "wma":
                # WMA格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:a", "wmav2", "-b:a", "192k",
                    "-map_metadata", "0",
                    target_path
                ]
            else:
                # 默认AAC格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:a", "aac", "-b:a", "256k",
                    "-map_metadata", "0",
                    target_path
                ]
            
            # 执行FFmpeg命令
            self.log_callback.emit(f"    执行转换命令: {' '.join(cmd)}")
            
            # 隐藏控制台窗口
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            
            if result.returncode == 0:
                self.log_callback.emit(f"    FFmpeg输出: {result.stdout}")
                return True
            else:
                self.log_callback.emit(f"    FFmpeg错误: {result.stderr}")
                return False
        except Exception as e:
            self.log_callback.emit(f"    执行音频转换时出错: {str(e)}")
            return False
    
    def convert_video_file(self, source_path, target_path, target_format):
        """
        转换视频文件格式
        :param source_path: 源文件路径
        :param target_path: 目标文件路径
        :param target_format: 目标格式
        :return: 转换是否成功
        """
        try:
            # 构建FFmpeg命令
            if target_format == "mp4":
                # MP4格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart",
                    target_path
                ]
            elif target_format == "mkv":
                # MKV格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                    target_path
                ]
            elif target_format == "avi":
                # AVI格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                    target_path
                ]
            elif target_format == "mov":
                # MOV格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                    target_path
                ]
            elif target_format == "wmv":
                # WMV格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:v", "wmv2", "-c:a", "wmav2", "-b:a", "192k",
                    target_path
                ]
            elif target_format == "flv":
                # FLV格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                    target_path
                ]
            elif target_format == "webm":
                # WebM格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:v", "libvpx-vp9", "-c:a", "libvorbis", "-b:a", "192k",
                    target_path
                ]
            else:
                # 默认MP4格式
                cmd = [
                    "ffmpeg", "-i", source_path,
                    "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart",
                    target_path
                ]
            
            # 执行FFmpeg命令
            self.log_callback.emit(f"    执行转换命令: {' '.join(cmd)}")
            
            # 隐藏控制台窗口
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            
            if result.returncode == 0:
                self.log_callback.emit(f"    FFmpeg输出: {result.stdout}")
                return True
            else:
                self.log_callback.emit(f"    FFmpeg错误: {result.stderr}")
                return False
        except Exception as e:
            self.log_callback.emit(f"    执行视频转换时出错: {str(e)}")
            return False


class FluentMainWindow(FluentWindow):
    # 定义日志信号
    append_log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apple Music Downloader")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # 设置窗口图标
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
        elif os.path.exists(os.path.join(os.path.dirname(sys.executable), "icon.ico")):
            self.setWindowIcon(QIcon(os.path.join(os.path.dirname(sys.executable), "icon.ico")))
        elif os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icon.ico")):
            self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icon.ico")))
        
        # 连接日志信号到处理函数
        self.append_log_signal.connect(self.append_log)
        
        # 创建设置对象用于保存和加载用户配置
        self.settings = QSettings("AppleMusicDownloader", "Config")
        
        # 初始化UI
        self.init_ui()
        
        # 加载保存的设置
        self.load_settings()
        
        # 初始化下载线程为空
        self.download_thread = None
        
        # 日志窗口展开状态
        self.log_expanded = True

    def init_ui(self):
        """初始化用户界面"""
        # 创建下载界面
        self.download_interface = QWidget()
        self.download_interface.setObjectName("downloadInterface")
        
        # 创建设置界面
        self.settings_interface = QWidget()
        self.settings_interface.setObjectName("settingsInterface")

        # 创建关于界面
        self.info_interface = QWidget()
        self.info_interface.setObjectName("infoInterface")
        
        # 初始化界面
        self.init_download_interface()
        self.init_settings_interface()
        
        # 添加到导航栏
        self.addSubInterface(self.download_interface, FluentIcon.DOWNLOAD, "下载")
        self.addSubInterface(self.settings_interface, FluentIcon.SETTING, "设置", NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.info_interface, FluentIcon.INFO, "关于", NavigationItemPosition.BOTTOM)

    def init_settings_interface(self):
        """初始化设置界面"""
        # 创建主布局
        layout = QVBoxLayout(self.settings_interface)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建顶部导航栏
        self.settings_pivot = Pivot(self)
        self.settings_stacked_widget = QStackedWidget()
        
        # 创建导航项
        self.add_sub_interface("mode_interface", "下载模式")
        self.add_sub_interface("codec_interface", "编码格式")
        self.add_sub_interface("cover_interface", "封面和歌词")
        self.add_sub_interface("path_interface", "路径设置")
        self.add_sub_interface("template_interface", "模板设置")
        self.add_sub_interface("quality_interface", "视频质量")
        self.add_sub_interface("log_interface", "日志")
        
        # 添加到布局
        layout.addWidget(self.settings_pivot)
        layout.addWidget(self.settings_stacked_widget)
        
        # 默认显示第一个页面
        self.settings_pivot.setCurrentItem("mode_interface")

    def add_sub_interface(self, object_name, text):
        """添加设置子界面"""
        # 创建界面widget
        widget = QWidget()
        widget.setObjectName(object_name)
        
        # 根据不同的界面创建内容
        if object_name == "mode_interface":
            self.create_mode_settings_page(widget)
        elif object_name == "codec_interface":
            self.create_codec_settings_page(widget)
        elif object_name == "cover_interface":
            self.create_cover_settings_page(widget)
        elif object_name == "path_interface":
            self.create_path_settings_page(widget)
        elif object_name == "template_interface":
            self.create_template_settings_page(widget)
        elif object_name == "quality_interface":
            self.create_quality_settings_page(widget)
        elif object_name == "log_interface":
            self.create_log_settings_page(widget)
        
        # 添加到stacked widget
        self.settings_stacked_widget.addWidget(widget)
        
        # 添加到pivot
        self.settings_pivot.addItem(
            routeKey=object_name,
            text=text,
            onClick=lambda: self.settings_stacked_widget.setCurrentWidget(widget)
        )

    def init_download_interface(self):
        """初始化下载界面"""
        # 创建主布局
        layout = QVBoxLayout(self.download_interface)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 下载链接区域标题
        url_title = SubtitleLabel("下载链接")
        layout.addWidget(url_title)
        
        # URL输入区域
        self.url_input = TextEdit()
        self.url_input.setPlaceholderText("在此输入Apple Music链接，每行一个...\n例如:\nhttps://music.apple.com/us/album/album-name/album-id\nhttps://music.apple.com/us/music-video/video-name/video-id")
        self.url_input.setMaximumHeight(100)
        layout.addWidget(self.url_input)
        
        # 添加分割线
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line1)
        
        # 文件路径区域标题
        path_title = SubtitleLabel("文件路径")
        layout.addWidget(path_title)
        
        # 文件路径选择区域
        path_layout = QGridLayout()
        path_layout.setSpacing(10)
        
        # Cookie文件选择
        path_layout.addWidget(QLabel("Cookie文件:"), 0, 0)
        self.cookie_path = LineEdit()
        self.cookie_path.setPlaceholderText("选择您的Cookie文件")
        path_layout.addWidget(self.cookie_path, 0, 1)
        cookie_button = PushButton("浏览...")
        cookie_button.clicked.connect(self.select_cookie_file)
        path_layout.addWidget(cookie_button, 0, 2)
        
        # 输出目录选择
        path_layout.addWidget(QLabel("输出目录:"), 1, 0)
        self.output_path = LineEdit()
        self.output_path.setPlaceholderText("选择输出目录")
        path_layout.addWidget(self.output_path, 1, 1)
        output_button = PushButton("浏览...")
        output_button.clicked.connect(self.select_output_directory)
        path_layout.addWidget(output_button, 1, 2)
        
        layout.addLayout(path_layout)
        
        # 添加分割线
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line2)
        
        # 下载选项区域标题
        options_title = SubtitleLabel("下载选项")
        layout.addWidget(options_title)
        
        # 下载选项区域
        options_layout = QVBoxLayout()
        options_layout.setSpacing(10)
        
        # 复选框选项
        checkboxes_layout = QGridLayout()
        checkboxes_layout.setSpacing(10)
        
        self.overwrite = CheckBox("覆盖已存在文件")
        self.disable_music_video_skip = CheckBox("禁用音乐视频跳过")
        self.save_playlist = CheckBox("保存播放列表")
        self.synced_lyrics_only = CheckBox("仅下载同步歌词")
        self.no_synced_lyrics = CheckBox("不下载同步歌词")
        self.read_urls_as_txt = CheckBox("将URL作为TXT文件读取")
        self.no_exceptions = CheckBox("禁用例外处理")
        
        checkboxes_layout.addWidget(self.overwrite, 0, 0)
        checkboxes_layout.addWidget(self.disable_music_video_skip, 0, 1)
        checkboxes_layout.addWidget(self.save_playlist, 1, 0)
        checkboxes_layout.addWidget(self.synced_lyrics_only, 1, 1)
        checkboxes_layout.addWidget(self.no_synced_lyrics, 2, 0)
        checkboxes_layout.addWidget(self.read_urls_as_txt, 2, 1)
        checkboxes_layout.addWidget(self.no_exceptions, 3, 0)
        
        options_layout.addLayout(checkboxes_layout)
        
        # 格式转换选项
        format_layout = QHBoxLayout()
        format_layout.setSpacing(10)
        format_layout.addWidget(QLabel("音频格式转换:"))
        
        self.audio_format = ComboBox()
        self.audio_format.addItems([
            "保持原格式", "mp3", "flac", "wav", "aac", "m4a", "ogg", "wma"
        ])
        format_layout.addWidget(self.audio_format)
        
        format_layout.addWidget(QLabel("视频格式转换:"))
        
        self.video_format = ComboBox()
        self.video_format.addItems([
            "保持原格式", "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm"
        ])
        format_layout.addWidget(self.video_format)
        
        options_layout.addLayout(format_layout)
        
        layout.addLayout(options_layout)
        
        # 添加分割线
        line3 = QFrame()
        line3.setFrameShape(QFrame.Shape.HLine)
        line3.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line3)
        
        # 下载按钮
        self.download_btn = PrimaryPushButton("开始下载")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)
        
        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch(1)
        
    def toggle_log(self):
        """切换日志窗口的显示/隐藏状态"""
        if self.log_expanded:
            self.log_widget.setVisible(False)
            self.toggle_log_btn.setText("展开")
        else:
            self.log_widget.setVisible(True)
            self.toggle_log_btn.setText("收起")
        self.log_expanded = not self.log_expanded

    def create_mode_settings_page(self, parent):
        """创建下载模式设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel("下载模式")
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 下载模式设置
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(10)
        
        mode_layout.addWidget(QLabel("下载模式:"))
        self.download_mode = ComboBox()
        self.download_mode.addItems(["ytdlp", "nm3u8dlre"])
        mode_layout.addWidget(self.download_mode)
        
        mode_layout.addWidget(QLabel("混流模式:"))
        self.remux_mode = ComboBox()
        self.remux_mode.addItems(["ffmpeg", "mp4box"])
        mode_layout.addWidget(self.remux_mode)
        
        layout.addLayout(mode_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton("保存设置")
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_codec_settings_page(self, parent):
        """创建编码格式设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel("编码格式")
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 编码格式设置
        codec_layout = QGridLayout()
        codec_layout.setSpacing(10)
        
        codec_layout.addWidget(QLabel("音频编码格式:"), 0, 0)
        self.codec_song = ComboBox()
        self.codec_song.addItems(["aac-legacy", "aac", "alac"])
        codec_layout.addWidget(self.codec_song, 0, 1)
        
        codec_layout.addWidget(QLabel("音乐视频编码格式:"), 1, 0)
        self.codec_music_video = ComboBox()
        self.codec_music_video.addItems(["h264", "h265", "vp9"])
        codec_layout.addWidget(self.codec_music_video, 1, 1)
        
        layout.addLayout(codec_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton("保存设置")
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_cover_settings_page(self, parent):
        """创建封面和歌词设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel("封面和歌词")
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 封面和歌词设置
        cover_layout = QGridLayout()
        cover_layout.setSpacing(10)
        
        cover_layout.addWidget(QLabel("封面格式:"), 0, 0)
        self.cover_format = ComboBox()
        self.cover_format.addItems(["jpg", "png", "webp"])
        cover_layout.addWidget(self.cover_format, 0, 1)
        
        cover_layout.addWidget(QLabel("封面尺寸:"), 1, 0)
        self.cover_size = SpinBox()
        self.cover_size.setRange(90, 10000)
        self.cover_size.setValue(1200)
        cover_layout.addWidget(self.cover_size, 1, 1)
        
        cover_layout.addWidget(QLabel("截断长度:"), 2, 0)
        self.truncate = SpinBox()
        self.truncate.setRange(0, 1000)
        self.truncate.setValue(0)
        cover_layout.addWidget(self.truncate, 2, 1)
        
        layout.addLayout(cover_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton("保存设置")
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_path_settings_page(self, parent):
        """创建路径设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel("路径设置")
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 路径设置
        path_layout = QGridLayout()
        path_layout.setSpacing(10)
        
        path_layout.addWidget(QLabel("临时文件路径:"), 0, 0)
        self.temp_path = LineEdit()
        self.temp_path.setText("./temp")
        path_layout.addWidget(self.temp_path, 0, 1)
        
        path_layout.addWidget(QLabel("WVD文件路径:"), 1, 0)
        self.wvd_path = LineEdit()
        path_layout.addWidget(self.wvd_path, 1, 1)
        
        layout.addLayout(path_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton("保存设置")
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_template_settings_page(self, parent):
        """创建模板设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel("模板设置")
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 模板设置
        template_layout = QGridLayout()
        template_layout.setSpacing(10)
        
        template_layout.addWidget(QLabel("专辑文件夹模板:"), 0, 0)
        self.template_folder_album = LineEdit()
        self.template_folder_album.setText("{album_artist}/{album}")
        template_layout.addWidget(self.template_folder_album, 0, 1)
        
        template_layout.addWidget(QLabel("合辑文件夹模板:"), 1, 0)
        self.template_folder_compilation = LineEdit()
        self.template_folder_compilation.setText("Compilations/{album}")
        template_layout.addWidget(self.template_folder_compilation, 1, 1)
        
        template_layout.addWidget(QLabel("单碟文件模板:"), 2, 0)
        self.template_file_single_disc = LineEdit()
        self.template_file_single_disc.setText("{track:02d} {title}")
        template_layout.addWidget(self.template_file_single_disc, 2, 1)
        
        template_layout.addWidget(QLabel("多碟文件模板:"), 3, 0)
        self.template_file_multi_disc = LineEdit()
        self.template_file_multi_disc.setText("{disc}-{track:02d} {title}")
        template_layout.addWidget(self.template_file_multi_disc, 3, 1)
        
        layout.addLayout(template_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton("保存设置")
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_quality_settings_page(self, parent):
        """创建视频质量设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel("视频质量")
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 视频质量设置
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(10)
        
        quality_layout.addWidget(QLabel("帖子视频质量:"))
        self.quality_post = ComboBox()
        self.quality_post.addItems(["best", "1080p", "720p", "480p", "360p"])
        quality_layout.addWidget(self.quality_post)
        
        layout.addLayout(quality_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton("保存设置")
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_log_settings_page(self, parent):
        """创建日志设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel("日志")
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 日志文本区域
        self.status_text = TextEdit()
        self.status_text.setMinimumHeight(300)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 清除日志按钮
        clear_log_btn = PushButton("清除日志")
        clear_log_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_log_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch(1)

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

    def start_download(self):
        """开始下载"""
        try:
            # 获取输入的URL列表
            urls_text = self.url_input.toPlainText().strip()
            if not urls_text:
                InfoBar.warning(
                    title="警告",
                    content="请输入至少一个下载链接",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    parent=self
                )
                return
                
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
            if not urls:
                InfoBar.warning(
                    title="警告",
                    content="请输入有效的下载链接",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    parent=self
                )
                return
            
            # 获取Cookie文件路径
            cookie_file = self.cookie_path.text().strip()
            if not cookie_file:
                InfoBar.warning(
                    title="警告",
                    content="请选择Cookie文件",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    parent=self
                )
                return
                
            if not os.path.exists(cookie_file):
                InfoBar.warning(
                    title="警告",
                    content="指定的Cookie文件不存在",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    parent=self
                )
                return
            
            # 获取输出目录
            output_dir = self.output_path.text().strip()
            if not output_dir:
                output_dir = "."
            
            # 确保输出目录存在
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # 收集所有下载选项
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
            self.download_thread = DownloadThread(urls, cookie_file, output_dir, download_options, self.append_log_signal)
            self.download_thread.progress_signal.connect(self.update_progress)
            self.download_thread.finished_signal.connect(self.download_finished)
            self.download_thread.start()
        except Exception as e:
            error_msg = f"启动下载时发生错误: {str(e)}\n{traceback.format_exc()}"
            self.append_log(error_msg)
            InfoBar.error(
                title="错误",
                content="启动下载时发生错误，请查看日志",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=-1,
                parent=self
            )
            # 恢复下载按钮
            self.download_btn.setEnabled(True)
            self.download_btn.setText("开始下载")
        
    def append_log(self, message):
        """添加日志信息"""
        try:
            self.status_text.append(message)
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
                InfoBar.success(
                    title="成功",
                    content="下载已完成!",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="错误",
                    content="下载过程中发生错误，请查看日志!",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=-1,
                    parent=self
                )
        except Exception as e:
            error_msg = f"处理下载完成时发生错误: {str(e)}\n{traceback.format_exc()}"
            self.append_log(error_msg)
            
    def clear_log(self):
        """清除日志"""
        try:
            self.status_text.clear()
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
        
        # 设置主题
        setTheme(Theme.AUTO)
        
        # 设置应用程序属性
        app.setApplicationName("AppleMusic Downloader")
        app.setApplicationVersion("3.1.0")
        
        # 创建并显示主窗口
        window = FluentMainWindow()
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