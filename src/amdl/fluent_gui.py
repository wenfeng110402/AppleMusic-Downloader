# fluent ui
import sys
import os
import io
import re
import traceback
import ctypes
import subprocess
import shutil
from pathlib import Path

import amdl.cli
import platform
from amdl.gui_conversion import (
    convert_audio_file as shared_convert_audio_file,
    convert_downloaded_files as shared_convert_downloaded_files,
    convert_video_file as shared_convert_video_file,
    resolve_ffmpeg_executable,
)

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


I18N = {
    "zh_CN": {
        "window_title": "Apple Music Downloader",
        "nav_download": "下载",
        "nav_settings": "设置",
        "settings_mode": "下载模式",
        "settings_codec": "编码格式",
        "settings_cover": "封面和歌词",
        "settings_path": "路径设置",
        "settings_template": "模板设置",
        "settings_quality": "视频质量",
        "settings_log": "日志",
        "download_urls": "下载链接",
        "download_paths": "文件路径",
        "download_options": "下载选项",
        "placeholder_urls": "在此输入Apple Music链接，每行一个...\n例如:\nhttps://music.apple.com/us/album/album-name/album-id\nhttps://music.apple.com/us/music-video/video-name/video-id",
        "label_cookie": "Cookie文件:",
        "label_output": "输出目录:",
        "placeholder_cookie": "选择您的Cookie文件",
        "placeholder_output": "选择输出目录",
        "btn_browse": "浏览...",
        "opt_overwrite": "覆盖已存在文件",
        "opt_disable_mv_skip": "禁用音乐视频跳过",
        "opt_save_playlist": "保存播放列表",
        "opt_synced_only": "仅下载同步歌词",
        "opt_no_synced": "不下载同步歌词",
        "opt_read_urls_txt": "将URL作为TXT文件读取",
        "opt_no_exceptions": "禁用例外处理",
        "label_audio_convert": "音频格式转换:",
        "label_video_convert": "视频格式转换:",
        "btn_start": "开始下载",
        "btn_downloading": "下载中...",
        "page_mode_title": "下载模式",
        "label_download_mode": "下载模式:",
        "label_remux_mode": "混流模式:",
        "page_codec_title": "编码格式",
        "label_codec_song": "音频编码格式:",
        "label_codec_mv": "音乐视频编码格式:",
        "page_cover_title": "封面和歌词",
        "label_cover_format": "封面格式:",
        "label_cover_size": "封面尺寸:",
        "label_truncate": "截断长度:",
        "page_path_title": "路径设置",
        "label_temp_path": "临时文件路径:",
        "label_wvd_path": "WVD文件路径:",
        "page_template_title": "模板设置",
        "label_tpl_album": "专辑文件夹模板:",
        "label_tpl_comp": "合辑文件夹模板:",
        "label_tpl_single": "单碟文件模板:",
        "label_tpl_multi": "多碟文件模板:",
        "page_quality_title": "视频质量",
        "label_quality_post": "帖子视频质量:",
        "page_log_title": "日志",
        "btn_clear_log": "清除日志",
        "label_language": "界面语言:",
        "lang_zh": "简体中文",
        "lang_en": "English",
        "btn_save_settings": "保存设置",
        "warn": "警告",
        "error": "错误",
        "success": "成功",
        "msg_need_url": "请输入至少一个下载链接",
        "msg_invalid_url": "请输入有效的下载链接",
        "msg_need_cookie": "请选择Cookie文件",
        "msg_cookie_missing": "指定的Cookie文件不存在",
        "msg_start_error": "启动下载时发生错误，请查看日志",
        "msg_download_done": "下载已完成!",
        "msg_download_failed": "下载过程中发生错误，请查看日志!",
        "dialog_cookie": "选择Cookie文件",
        "dialog_output": "选择输出目录",
        "msg_lang_saved": "语言设置已保存，重启程序后将完整生效。",
    },
    "en_US": {
        "window_title": "Apple Music Downloader",
        "nav_download": "Download",
        "nav_settings": "Settings",
        "settings_mode": "Download Mode",
        "settings_codec": "Codecs",
        "settings_cover": "Cover & Lyrics",
        "settings_path": "Path Settings",
        "settings_template": "Templates",
        "settings_quality": "Video Quality",
        "settings_log": "Logs",
        "download_urls": "URLs",
        "download_paths": "Paths",
        "download_options": "Options",
        "placeholder_urls": "Enter Apple Music URLs here, one per line...\nExample:\nhttps://music.apple.com/us/album/album-name/album-id\nhttps://music.apple.com/us/music-video/video-name/video-id",
        "label_cookie": "Cookie file:",
        "label_output": "Output directory:",
        "placeholder_cookie": "Select your cookie file",
        "placeholder_output": "Select output directory",
        "btn_browse": "Browse...",
        "opt_overwrite": "Overwrite existing files",
        "opt_disable_mv_skip": "Disable music video skip",
        "opt_save_playlist": "Save playlist",
        "opt_synced_only": "Synced lyrics only",
        "opt_no_synced": "Do not download synced lyrics",
        "opt_read_urls_txt": "Read URLs as TXT",
        "opt_no_exceptions": "Disable exceptions",
        "label_audio_convert": "Audio convert:",
        "label_video_convert": "Video convert:",
        "btn_start": "Start Download",
        "btn_downloading": "Downloading...",
        "page_mode_title": "Download Mode",
        "label_download_mode": "Download mode:",
        "label_remux_mode": "Remux mode:",
        "page_codec_title": "Codecs",
        "label_codec_song": "Song codec:",
        "label_codec_mv": "Music video codec:",
        "page_cover_title": "Cover & Lyrics",
        "label_cover_format": "Cover format:",
        "label_cover_size": "Cover size:",
        "label_truncate": "Truncate length:",
        "page_path_title": "Path Settings",
        "label_temp_path": "Temp path:",
        "label_wvd_path": "WVD path:",
        "page_template_title": "Templates",
        "label_tpl_album": "Album folder template:",
        "label_tpl_comp": "Compilation folder template:",
        "label_tpl_single": "Single-disc file template:",
        "label_tpl_multi": "Multi-disc file template:",
        "page_quality_title": "Video Quality",
        "label_quality_post": "Post video quality:",
        "page_log_title": "Logs",
        "btn_clear_log": "Clear Log",
        "label_language": "UI language:",
        "lang_zh": "简体中文",
        "lang_en": "English",
        "btn_save_settings": "Save Settings",
        "warn": "Warning",
        "error": "Error",
        "success": "Success",
        "msg_need_url": "Please enter at least one URL",
        "msg_invalid_url": "Please enter valid URL(s)",
        "msg_need_cookie": "Please select a cookie file",
        "msg_cookie_missing": "Selected cookie file does not exist",
        "msg_start_error": "Failed to start download, check logs",
        "msg_download_done": "Download completed!",
        "msg_download_failed": "Errors occurred during download, check logs.",
        "dialog_cookie": "Select cookie file",
        "dialog_output": "Select output directory",
        "msg_lang_saved": "Language saved. Restart app for full effect.",
    },
}


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
        # 可替换的 ffmpeg 可执行文件名/路径（便于在打包后修改或替换）
        # 检查是否在打包环境中运行
        if getattr(sys, 'frozen', False):
            # 在打包环境中，使用PyInstaller的临时目录
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller创建的临时目录
                self.ffmpeg_exe = os.path.join(sys._MEIPASS, "tools", "ffmpeg.exe")
            else:
                # 备用方案：exe同级目录
                self.ffmpeg_exe = os.path.join(os.path.dirname(sys.executable), "tools", "ffmpeg.exe")
        else:
            # 在开发环境中，使用系统PATH中的ffmpeg
            self.ffmpeg_exe = "ffmpeg"

        fallback_paths = None
        if getattr(sys, 'frozen', False):
            fallback_paths = [
                os.path.join(os.path.dirname(sys.executable), "tools", "ffmpeg.exe"),
                os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe"),
                "ffmpeg",
                "ffmpeg.exe",
            ]
        self.ffmpeg_exe = resolve_ffmpeg_executable(self.ffmpeg_exe, fallback_paths)
        
        if not self.ffmpeg_exe:
            self.log_callback.emit(f"    警告: FFmpeg不可用: {self.ffmpeg_exe}")
    
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
                    amdl.cli.main(args, standalone_mode=False)
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
            try:
                uname_info = platform.uname()
            except Exception:
                uname_info = "N/A"
            self.log_callback.emit(f"Python版本: {sys.version}")
            self.log_callback.emit(f"操作系统: {os.name}")
            self.log_callback.emit(f"系统信息: {uname_info}")
            
            self.finished_signal.emit(False)
    
    def extract_downloaded_file_path(self, log_line):
        """
        从日志行中提取下载的文件路径
        :param log_line: 日志行
        """
        # 合并匹配模式，按优先级依次尝试
        patterns = [
            r"[Dd]ownload.*completed.*[:：]\s*(.+?\.(?:m4a|mp4|mov))",
            r"(?:已保存到|保存到|Saved to).*[:：]\s*(.+?\.(?:m4a|mp4|mov))",
            r"(?:已完成|完成).*[:：]\s*(.+?\.(?:m4a|mp4|mov))",
            r"([A-Za-z]:[/\\][^\s]*?\.(?:m4a|mp4|mov))(?:\s|$)",
        ]

        file_path = None
        for pat in patterns:
            m = re.search(pat, log_line)
            if not m:
                continue
            candidate = m.group(1).strip()
            # 最后一条宽泛匹配需要额外确认日志附近存在成功标志
            if pat == patterns[-1]:
                if not ("saved" in log_line.lower() or "完成" in log_line or "success" in log_line.lower() or "Done" in log_line):
                    continue
            file_path = candidate
            break
        
        # 特殊处理：如果看到"Done"消息，检查最近是否有文件路径
        if not file_path and "Done" in log_line and self.downloaded_files:
            # 如果已经有一些文件路径，不需要额外操作
            pass
            
        if file_path:
            # 转换为绝对路径
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
            # 避免重复添加
            if file_path not in self.downloaded_files:
                self.downloaded_files.append(file_path)
                self.log_callback.emit(f"    检测到下载文件: {file_path}")
                
        # 当看到"Done"消息时，如果我们还没有任何文件路径，尝试从输出目录中查找最近创建的媒体文件
        if "Done" in log_line and not self.downloaded_files and self.output_dir:
            try:
                # 查找输出目录中最近创建的媒体文件
                media_files = []
                for ext in [".m4a", ".mp4", ".mov"]:
                    media_files.extend(Path(self.output_dir).rglob(f"*{ext}"))
                
                # 按修改时间排序，获取最新的文件
                if media_files:
                    latest_file = max(media_files, key=lambda x: x.stat().st_mtime)
                    file_path = str(latest_file)
                    if file_path not in self.downloaded_files:
                        self.downloaded_files.append(file_path)
                        self.log_callback.emit(f"    检测到下载文件: {file_path}")
            except Exception as e:
                self.log_callback.emit(f"    检测下载文件时出错: {str(e)}")
    
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
            self.log_callback.emit,
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
            self.log_callback.emit,
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
            self.log_callback.emit,
        )

    def run_subprocess(self, cmd):
        """
        统一运行外部命令并返回 (returncode, stdout, stderr)。
        在 Windows 上隐藏控制台窗口。所有调用应通过该函数执行以减少重复代码。
        """
        try:
            self.log_callback.emit(f"    执行转换命令: {' '.join(cmd)}")
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)


class FluentMainWindow(FluentWindow):
    # 定义日志信号
    append_log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("AppleMusicDownloader", "Config")
        self.current_language = self.settings.value("ui_language", "zh_CN")
        if self.current_language not in I18N:
            self.current_language = "zh_CN"

        self.setWindowTitle(self.tr_text("window_title"))
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # 设置窗口图标
        self._setup_icons()
        
        # 连接日志信号到处理函数
        self.append_log_signal.connect(self.append_log)
        
        # 初始化UI
        self.init_ui()
        
        # 加载保存的设置
        self.load_settings()
        
        # 初始化下载线程为空
        self.download_thread = None
        
        # 日志窗口展开状态
        self.log_expanded = True

    def tr_text(self, key: str) -> str:
        return I18N.get(self.current_language, I18N["zh_CN"]).get(key, key)

    def _setup_icons(self):
        """设置窗口和任务栏图标"""
        # 查找图标文件
        icon_paths = [
            "icon.ico",  # 当前目录
            os.path.join(os.path.dirname(sys.executable), "icon.ico"),  # exe所在目录
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icon.ico"),  # 项目根目录
        ]
        
        # 如果是打包后的程序，检查_MEIPASS目录
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            icon_paths.insert(0, os.path.join(sys._MEIPASS, "icon.ico"))
        
        icon_path = None
        for path in icon_paths:
            if os.path.exists(path):
                icon_path = path
                break
        
        if icon_path:
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            
            # 设置应用程序图标
            app = QApplication.instance()
            if app:
                app.setWindowIcon(icon)
            
            # 特别设置FluentWindow的标题栏图标
            if hasattr(self, 'titleBar') and hasattr(self.titleBar, 'setIcon'):
                self.titleBar.setIcon(icon)
            
            # Windows任务栏图标设置
            if sys.platform == "win32":
                try:
                    import ctypes
                    myappid = 'AppleMusicDownloader.3.1.0'  # 任意字符串
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                except Exception:
                    pass  # 忽略错误，继续执行

    def showEvent(self, event):
        """窗口显示事件，确保任务栏图标正确显示"""
        super().showEvent(event)
        # 在窗口显示后再次设置图标，确保任务栏图标正确显示
        self._setup_icons()
        
    def init_ui(self):
        """初始化用户界面"""
        # 创建下载界面
        self.download_interface = QWidget()
        self.download_interface.setObjectName("downloadInterface")
        
        # 创建设置界面
        self.settings_interface = QWidget()
        self.settings_interface.setObjectName("settingsInterface")
        
        # 初始化界面
        self.init_download_interface()
        self.init_settings_interface()
        
        # 添加到导航栏
        self.addSubInterface(self.download_interface, FluentIcon.DOWNLOAD, self.tr_text("nav_download"))
        self.addSubInterface(self.settings_interface, FluentIcon.SETTING, self.tr_text("nav_settings"), NavigationItemPosition.BOTTOM)

        self.apply_runtime_translations()

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
        self.add_sub_interface("mode_interface", "settings_mode")
        self.add_sub_interface("codec_interface", "settings_codec")
        self.add_sub_interface("cover_interface", "settings_cover")
        self.add_sub_interface("path_interface", "settings_path")
        self.add_sub_interface("template_interface", "settings_template")
        self.add_sub_interface("quality_interface", "settings_quality")
        self.add_sub_interface("log_interface", "settings_log")
        
        # 添加到布局
        layout.addWidget(self.settings_pivot)
        layout.addWidget(self.settings_stacked_widget)
        
        # 默认显示第一个页面
        self.settings_pivot.setCurrentItem("mode_interface")

    def add_sub_interface(self, object_name, text_key):
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
            text=self.tr_text(text_key),
            onClick=lambda: self.settings_stacked_widget.setCurrentWidget(widget)
        )

    def init_download_interface(self):
        """初始化下载界面"""
        # 创建主布局
        layout = QVBoxLayout(self.download_interface)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 下载链接区域标题
        self.url_title = SubtitleLabel(self.tr_text("download_urls"))
        layout.addWidget(self.url_title)
        
        # URL输入区域
        self.url_input = TextEdit()
        self.url_input.setPlaceholderText(self.tr_text("placeholder_urls"))
        self.url_input.setMaximumHeight(100)
        layout.addWidget(self.url_input)
        
        # 添加分割线
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line1)
        
        # 文件路径区域标题
        self.path_title = SubtitleLabel(self.tr_text("download_paths"))
        layout.addWidget(self.path_title)
        
        # 文件路径选择区域
        path_layout = QGridLayout()
        path_layout.setSpacing(10)
        
        # Cookie文件选择
        self.cookie_label_widget = QLabel(self.tr_text("label_cookie"))
        path_layout.addWidget(self.cookie_label_widget, 0, 0)
        self.cookie_path = LineEdit()
        self.cookie_path.setPlaceholderText(self.tr_text("placeholder_cookie"))
        path_layout.addWidget(self.cookie_path, 0, 1)
        self.cookie_button = PushButton(self.tr_text("btn_browse"))
        self.cookie_button.clicked.connect(self.select_cookie_file)
        path_layout.addWidget(self.cookie_button, 0, 2)
        
        # 输出目录选择
        self.output_label_widget = QLabel(self.tr_text("label_output"))
        path_layout.addWidget(self.output_label_widget, 1, 0)
        self.output_path = LineEdit()
        self.output_path.setPlaceholderText(self.tr_text("placeholder_output"))
        path_layout.addWidget(self.output_path, 1, 1)
        self.output_button = PushButton(self.tr_text("btn_browse"))
        self.output_button.clicked.connect(self.select_output_directory)
        path_layout.addWidget(self.output_button, 1, 2)
        
        layout.addLayout(path_layout)
        
        # 添加分割线
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line2)
        
        # 下载选项区域标题
        self.options_title = SubtitleLabel(self.tr_text("download_options"))
        layout.addWidget(self.options_title)
        
        # 下载选项区域
        options_layout = QVBoxLayout()
        options_layout.setSpacing(10)
        
        # 复选框选项
        checkboxes_layout = QGridLayout()
        checkboxes_layout.setSpacing(10)
        
        self.overwrite = CheckBox(self.tr_text("opt_overwrite"))
        self.disable_music_video_skip = CheckBox(self.tr_text("opt_disable_mv_skip"))
        self.save_playlist = CheckBox(self.tr_text("opt_save_playlist"))
        self.synced_lyrics_only = CheckBox(self.tr_text("opt_synced_only"))
        self.no_synced_lyrics = CheckBox(self.tr_text("opt_no_synced"))
        self.read_urls_as_txt = CheckBox(self.tr_text("opt_read_urls_txt"))
        self.no_exceptions = CheckBox(self.tr_text("opt_no_exceptions"))
        
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
        self.audio_convert_label = QLabel(self.tr_text("label_audio_convert"))
        format_layout.addWidget(self.audio_convert_label)
        
        self.audio_format = ComboBox()
        self.audio_format.addItems([
            "保持原格式", "mp3", "flac", "wav", "aac", "m4a", "ogg", "wma"
        ])
        format_layout.addWidget(self.audio_format)
        
        self.video_convert_label = QLabel(self.tr_text("label_video_convert"))
        format_layout.addWidget(self.video_convert_label)
        
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
        self.download_btn = PrimaryPushButton(self.tr_text("btn_start"))
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
        title_label = SubtitleLabel(self.tr_text("page_mode_title"))
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 下载模式设置
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(10)
        
        mode_layout.addWidget(QLabel(self.tr_text("label_download_mode")))
        self.download_mode = ComboBox()
        self.download_mode.addItems(["ytdlp", "nm3u8dlre"])
        mode_layout.addWidget(self.download_mode)
        
        mode_layout.addWidget(QLabel(self.tr_text("label_remux_mode")))
        self.remux_mode = ComboBox()
        self.remux_mode.addItems(["ffmpeg", "mp4box"])
        mode_layout.addWidget(self.remux_mode)
        
        layout.addLayout(mode_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton(self.tr_text("btn_save_settings"))
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_codec_settings_page(self, parent):
        """创建编码格式设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel(self.tr_text("page_codec_title"))
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 编码格式设置
        codec_layout = QGridLayout()
        codec_layout.setSpacing(10)
        
        codec_layout.addWidget(QLabel(self.tr_text("label_codec_song")), 0, 0)
        self.codec_song = ComboBox()
        self.codec_song.addItems(["aac-legacy", "aac", "atmos"])
        codec_layout.addWidget(self.codec_song, 0, 1)
        
        codec_layout.addWidget(QLabel(self.tr_text("label_codec_mv")), 1, 0)
        self.codec_music_video = ComboBox()
        self.codec_music_video.addItems(["h264", "h265", "vp9"])
        codec_layout.addWidget(self.codec_music_video, 1, 1)
        
        layout.addLayout(codec_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton(self.tr_text("btn_save_settings"))
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_cover_settings_page(self, parent):
        """创建封面和歌词设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel(self.tr_text("page_cover_title"))
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 封面和歌词设置
        cover_layout = QGridLayout()
        cover_layout.setSpacing(10)
        
        cover_layout.addWidget(QLabel(self.tr_text("label_cover_format")), 0, 0)
        self.cover_format = ComboBox()
        self.cover_format.addItems(["jpg", "png", "webp"])
        cover_layout.addWidget(self.cover_format, 0, 1)
        
        cover_layout.addWidget(QLabel(self.tr_text("label_cover_size")), 1, 0)
        self.cover_size = SpinBox()
        self.cover_size.setRange(90, 10000)
        self.cover_size.setValue(1200)
        cover_layout.addWidget(self.cover_size, 1, 1)
        
        cover_layout.addWidget(QLabel(self.tr_text("label_truncate")), 2, 0)
        self.truncate = SpinBox()
        self.truncate.setRange(0, 1000)
        self.truncate.setValue(0)
        cover_layout.addWidget(self.truncate, 2, 1)
        
        layout.addLayout(cover_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton(self.tr_text("btn_save_settings"))
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_path_settings_page(self, parent):
        """创建路径设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel(self.tr_text("page_path_title"))
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 路径设置
        path_layout = QGridLayout()
        path_layout.setSpacing(10)
        
        path_layout.addWidget(QLabel(self.tr_text("label_temp_path")), 0, 0)
        self.temp_path = LineEdit()
        self.temp_path.setText("./temp")
        path_layout.addWidget(self.temp_path, 0, 1)
        
        path_layout.addWidget(QLabel(self.tr_text("label_wvd_path")), 1, 0)
        self.wvd_path = LineEdit()
        path_layout.addWidget(self.wvd_path, 1, 1)
        
        layout.addLayout(path_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton(self.tr_text("btn_save_settings"))
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_template_settings_page(self, parent):
        """创建模板设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel(self.tr_text("page_template_title"))
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 模板设置
        template_layout = QGridLayout()
        template_layout.setSpacing(10)
        
        template_layout.addWidget(QLabel(self.tr_text("label_tpl_album")), 0, 0)
        self.template_folder_album = LineEdit()
        self.template_folder_album.setText("{album_artist}/{album}")
        template_layout.addWidget(self.template_folder_album, 0, 1)
        
        template_layout.addWidget(QLabel(self.tr_text("label_tpl_comp")), 1, 0)
        self.template_folder_compilation = LineEdit()
        self.template_folder_compilation.setText("Compilations/{album}")
        template_layout.addWidget(self.template_folder_compilation, 1, 1)
        
        template_layout.addWidget(QLabel(self.tr_text("label_tpl_single")), 2, 0)
        self.template_file_single_disc = LineEdit()
        self.template_file_single_disc.setText("{track:02d} {title}")
        template_layout.addWidget(self.template_file_single_disc, 2, 1)
        
        template_layout.addWidget(QLabel(self.tr_text("label_tpl_multi")), 3, 0)
        self.template_file_multi_disc = LineEdit()
        self.template_file_multi_disc.setText("{disc}-{track:02d} {title}")
        template_layout.addWidget(self.template_file_multi_disc, 3, 1)
        
        layout.addLayout(template_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton(self.tr_text("btn_save_settings"))
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_quality_settings_page(self, parent):
        """创建视频质量设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel(self.tr_text("page_quality_title"))
        layout.addWidget(title_label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 视频质量设置
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(10)
        
        quality_layout.addWidget(QLabel(self.tr_text("label_quality_post")))
        self.quality_post = ComboBox()
        self.quality_post.addItems(["best", "1080p", "720p", "480p", "360p"])
        quality_layout.addWidget(self.quality_post)
        
        layout.addLayout(quality_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton(self.tr_text("btn_save_settings"))
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)

    def create_log_settings_page(self, parent):
        """创建日志设置页面"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = SubtitleLabel(self.tr_text("page_log_title"))
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
        self.clear_log_btn = PushButton(self.tr_text("btn_clear_log"))
        self.clear_log_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_log_btn)

        self.language_label = QLabel(self.tr_text("label_language"))
        button_layout.addWidget(self.language_label)
        self.language_combo = ComboBox()
        self.language_combo.addItem(self.tr_text("lang_zh"))
        self.language_combo.addItem(self.tr_text("lang_en"))
        if self.current_language == "en_US":
            self.language_combo.setCurrentIndex(1)
        else:
            self.language_combo.setCurrentIndex(0)
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        button_layout.addWidget(self.language_combo)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch(1)

    def select_cookie_file(self):
        """选择Cookie文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr_text("dialog_cookie"), "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.cookie_path.setText(file_path)

    def select_output_directory(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, self.tr_text("dialog_output"))
        if directory:
            self.output_path.setText(directory)

    def start_download(self):
        """开始下载"""
        try:
            # 获取输入的URL列表
            urls_text = self.url_input.toPlainText().strip()
            if not urls_text:
                InfoBar.warning(
                    title=self.tr_text("warn"),
                    content=self.tr_text("msg_need_url"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    parent=self
                )
                return
                
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
            if not urls:
                InfoBar.warning(
                    title=self.tr_text("warn"),
                    content=self.tr_text("msg_invalid_url"),
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
                    title=self.tr_text("warn"),
                    content=self.tr_text("msg_need_cookie"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    parent=self
                )
                return
                
            if not os.path.exists(cookie_file):
                InfoBar.warning(
                    title=self.tr_text("warn"),
                    content=self.tr_text("msg_cookie_missing"),
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
            self.download_btn.setText(self.tr_text("btn_downloading"))
            
            # 创建并启动下载线程
            self.download_thread = DownloadThread(urls, cookie_file, output_dir, download_options, self.append_log_signal)
            self.download_thread.progress_signal.connect(self.update_progress)
            self.download_thread.finished_signal.connect(self.download_finished)
            self.download_thread.start()
        except Exception as e:
            error_msg = f"启动下载时发生错误: {str(e)}\n{traceback.format_exc()}"
            self.append_log(error_msg)
            InfoBar.error(
                title=self.tr_text("error"),
                content=self.tr_text("msg_start_error"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=-1,
                parent=self
            )
            # 恢复下载按钮
            self.download_btn.setEnabled(True)
            self.download_btn.setText(self.tr_text("btn_start"))
        
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

    def on_language_changed(self, index):
        new_language = "en_US" if index == 1 else "zh_CN"
        if new_language == self.current_language:
            return
        self.current_language = new_language
        self.settings.setValue("ui_language", self.current_language)
        self.apply_runtime_translations()
        InfoBar.success(
            title=self.tr_text("success"),
            content=self.tr_text("msg_lang_saved"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def apply_runtime_translations(self):
        self.setWindowTitle(self.tr_text("window_title"))

        if hasattr(self, "url_title"):
            self.url_title.setText(self.tr_text("download_urls"))
        if hasattr(self, "path_title"):
            self.path_title.setText(self.tr_text("download_paths"))
        if hasattr(self, "options_title"):
            self.options_title.setText(self.tr_text("download_options"))
        if hasattr(self, "url_input"):
            self.url_input.setPlaceholderText(self.tr_text("placeholder_urls"))
        if hasattr(self, "cookie_label_widget"):
            self.cookie_label_widget.setText(self.tr_text("label_cookie"))
        if hasattr(self, "output_label_widget"):
            self.output_label_widget.setText(self.tr_text("label_output"))
        if hasattr(self, "cookie_path"):
            self.cookie_path.setPlaceholderText(self.tr_text("placeholder_cookie"))
        if hasattr(self, "output_path"):
            self.output_path.setPlaceholderText(self.tr_text("placeholder_output"))
        if hasattr(self, "cookie_button"):
            self.cookie_button.setText(self.tr_text("btn_browse"))
        if hasattr(self, "output_button"):
            self.output_button.setText(self.tr_text("btn_browse"))
        if hasattr(self, "overwrite"):
            self.overwrite.setText(self.tr_text("opt_overwrite"))
        if hasattr(self, "disable_music_video_skip"):
            self.disable_music_video_skip.setText(self.tr_text("opt_disable_mv_skip"))
        if hasattr(self, "save_playlist"):
            self.save_playlist.setText(self.tr_text("opt_save_playlist"))
        if hasattr(self, "synced_lyrics_only"):
            self.synced_lyrics_only.setText(self.tr_text("opt_synced_only"))
        if hasattr(self, "no_synced_lyrics"):
            self.no_synced_lyrics.setText(self.tr_text("opt_no_synced"))
        if hasattr(self, "read_urls_as_txt"):
            self.read_urls_as_txt.setText(self.tr_text("opt_read_urls_txt"))
        if hasattr(self, "no_exceptions"):
            self.no_exceptions.setText(self.tr_text("opt_no_exceptions"))
        if hasattr(self, "audio_convert_label"):
            self.audio_convert_label.setText(self.tr_text("label_audio_convert"))
        if hasattr(self, "video_convert_label"):
            self.video_convert_label.setText(self.tr_text("label_video_convert"))
        if hasattr(self, "download_btn"):
            self.download_btn.setText(
                self.tr_text("btn_downloading") if not self.download_btn.isEnabled() else self.tr_text("btn_start")
            )
        if hasattr(self, "clear_log_btn"):
            self.clear_log_btn.setText(self.tr_text("btn_clear_log"))
        if hasattr(self, "language_label"):
            self.language_label.setText(self.tr_text("label_language"))
        if hasattr(self, "language_combo"):
            current = self.language_combo.currentIndex()
            self.language_combo.blockSignals(True)
            self.language_combo.setItemText(0, self.tr_text("lang_zh"))
            self.language_combo.setItemText(1, self.tr_text("lang_en"))
            self.language_combo.setCurrentIndex(current)
            self.language_combo.blockSignals(False)
        
    def download_finished(self, success):
        """下载完成回调"""
        try:
            # 恢复下载按钮
            self.download_btn.setEnabled(True)
            self.download_btn.setText(self.tr_text("btn_start"))
            
            if success:
                InfoBar.success(
                    title=self.tr_text("success"),
                    content=self.tr_text("msg_download_done"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title=self.tr_text("error"),
                    content=self.tr_text("msg_download_failed"),
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
            self.settings.setValue("ui_language", self.current_language)
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
            self.current_language = self.settings.value("ui_language", self.current_language)
            if self.current_language not in I18N:
                self.current_language = "zh_CN"
            if hasattr(self, "language_combo"):
                self.language_combo.blockSignals(True)
                self.language_combo.setCurrentIndex(1 if self.current_language == "en_US" else 0)
                self.language_combo.blockSignals(False)
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
        # 在应用启动时优先将内置 tools 目录加入 PATH，这样 subprocess 与 shutil.which 能找到捆绑的可执行文件
        try:
            from .utils import prepend_tools_to_path
            prepend_tools_to_path(["tools"])
        except Exception:
            # 忽略工具注入失败，程序仍可尝试使用系统 PATH
            pass

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