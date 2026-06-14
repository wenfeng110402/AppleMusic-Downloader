# fluent ui
import sys
import os
import traceback
from pathlib import Path
from typing import Any

from amdl.download_worker import DownloadThread
from amdl.i18n import I18N
from amdl.ui_builder import (
    add_settings_sub_interface,
    build_download_ui,
    build_main_ui,
    build_settings_ui,
)
from amdl.settings_store import load_window_settings, save_window_settings

# PyQt6 imports for Fluent UI
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFileDialog, 
    QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QIcon

# Fluent UI imports for PyQt6
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, InfoBar, InfoBarPosition,
    PushButton, CheckBox, ComboBox, SpinBox, LineEdit, TextEdit,
    ProgressBar, FluentIcon, SubtitleLabel, PrimaryPushButton,
    Pivot
)


class FluentMainWindow(FluentWindow):
    # 定义日志信号
    append_log_signal = pyqtSignal(str)
    download_interface: Any
    settings_interface: Any
    settings_pivot: Any
    settings_stacked_widget: Any
    url_title: Any
    path_title: Any
    options_title: Any
    url_input: Any
    cookie_label_widget: Any
    output_label_widget: Any
    cookie_path: Any
    output_path: Any
    cookie_button: Any
    output_button: Any
    overwrite: Any
    disable_music_video_skip: Any
    save_playlist: Any
    synced_lyrics_only: Any
    no_synced_lyrics: Any
    read_urls_as_txt: Any
    no_exceptions: Any
    audio_convert_label: Any
    audio_format: Any
    video_convert_label: Any
    video_format: Any
    download_btn: Any
    stop_btn: Any
    progress_bar: Any
    download_mode: Any
    remux_mode: Any
    codec_song: Any
    codec_music_video: Any
    cover_format: Any
    cover_size: Any
    truncate: Any
    temp_path: Any
    wvd_path: Any
    template_folder_album: Any
    template_folder_compilation: Any
    template_file_single_disc: Any
    template_file_multi_disc: Any
    template_param_label: Any
    template_param_combo: Any
    template_param_insert_btn: Any
    quality_post: Any
    status_text: Any
    language_combo: Any
    
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
        meipass_dir = getattr(sys, '_MEIPASS', None)
        if getattr(sys, 'frozen', False) and meipass_dir:
            icon_paths.insert(0, os.path.join(meipass_dir, "icon.ico"))
        
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
            set_app_icon = getattr(app, 'setWindowIcon', None)
            if callable(set_app_icon):
                set_app_icon(icon)
            
            # 特别设置FluentWindow的标题栏图标
            title_bar = getattr(self, 'titleBar', None)
            set_title_icon = getattr(title_bar, 'setIcon', None)
            if callable(set_title_icon):
                set_title_icon(icon)
            
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
        build_main_ui(self)

    def init_settings_interface(self):
        """初始化设置界面"""
        build_settings_ui(self)

    def add_sub_interface(self, object_name, text_key):
        """添加设置子界面"""
        add_settings_sub_interface(self, object_name, text_key)

    def init_download_interface(self):
        """初始化下载界面"""
        build_download_ui(self)
        
    def stop_download(self):
        """Stop the current download after the current track finishes."""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.stop_btn.setEnabled(False)
            self.append_log("正在停止下载... (等待当前曲目完成)")

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

        param_layout = QHBoxLayout()
        param_layout.setSpacing(10)
        self.template_param_label = QLabel(self.tr_text("label_tpl_available_params"))
        param_layout.addWidget(self.template_param_label)
        self.template_param_combo = ComboBox()
        self.template_param_combo.addItems(
            [
                "{album_artist}",
                "{album}",
                "{artist}",
                "{title}",
                "{track}",
                "{track:02d}",
                "{disc}",
            ]
        )
        param_layout.addWidget(self.template_param_combo)
        self.template_param_insert_btn = PushButton(self.tr_text("btn_tpl_insert_param"))
        self.template_param_insert_btn.clicked.connect(self.insert_selected_template_param)
        param_layout.addWidget(self.template_param_insert_btn)
        param_layout.addStretch(1)
        layout.addLayout(param_layout)
        
        # 保存设置按钮
        save_settings_button = PrimaryPushButton(self.tr_text("btn_save_settings"))
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)
        
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
            
            # 禁用下载按钮，显示停止按钮
            self.download_btn.setEnabled(False)
            self.download_btn.setText(self.tr_text("btn_downloading"))
            self.stop_btn.setEnabled(True)

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
            self.stop_btn.setEnabled(False)
        
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
        if hasattr(self, "template_param_label"):
            self.template_param_label.setText(self.tr_text("label_tpl_available_params"))
        if hasattr(self, "template_param_insert_btn"):
            self.template_param_insert_btn.setText(self.tr_text("btn_tpl_insert_param"))
        if hasattr(self, "download_btn"):
            self.download_btn.setText(
                self.tr_text("btn_downloading") if not self.download_btn.isEnabled() else self.tr_text("btn_start")
            )
        if hasattr(self, "stop_btn"):
            self.stop_btn.setText(self.tr_text("btn_stop"))
        # 更新设置界面中的语言选择器
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
            # 确保进度条到 100%
            self.progress_bar.setValue(100)

            # 恢复下载按钮，隐藏停止按钮
            self.download_btn.setEnabled(True)
            self.download_btn.setText(self.tr_text("btn_start"))
            self.download_btn.repaint()
            self.stop_btn.setEnabled(False)

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

            # 清除下载线程引用
            self.download_thread = None
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
            save_window_settings(self)
        except Exception as e:
            print(f"保存设置时出错: {e}")

    def insert_selected_template_param(self):
        token = self.template_param_combo.currentText()
        for target in (
            self.template_folder_album,
            self.template_folder_compilation,
            self.template_file_single_disc,
            self.template_file_multi_disc,
        ):
            if target.hasFocus():
                target.insert(token)
                return
        InfoBar.warning(
            title=self.tr_text("warn"),
            content=self.tr_text("msg_tpl_focus_needed"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            parent=self,
        )
        
    def load_settings(self):
        """加载设置"""
        try:
            load_window_settings(self)
        except Exception as e:
            print(f"加载设置时出错: {e}")

# 当脚本作为主程序运行时，调用main函数启动应用程序
# 这是程序的入口点，确保只有直接运行此脚本时才会启动GUI
if __name__ == "__main__":
    from amdl.launcher import main

    main()