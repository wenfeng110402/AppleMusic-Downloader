from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QStackedWidget
from qfluentwidgets import (
    FluentIcon,
    NavigationItemPosition,
    PushButton,
    CheckBox,
    ComboBox,
    SpinBox,
    LineEdit,
    TextEdit,
    ProgressBar,
    SubtitleLabel,
    PrimaryPushButton,
    Pivot,
)


def build_main_ui(window):
    window.download_interface = QWidget()
    window.download_interface.setObjectName("downloadInterface")

    window.settings_interface = QWidget()
    window.settings_interface.setObjectName("settingsInterface")

    build_download_ui(window)
    build_settings_ui(window)

    window.addSubInterface(window.download_interface, FluentIcon.DOWNLOAD, window.tr_text("nav_download"))
    window.addSubInterface(
        window.settings_interface,
        FluentIcon.SETTING,
        window.tr_text("nav_settings"),
        NavigationItemPosition.BOTTOM,
    )

    window.apply_runtime_translations()


def build_settings_ui(window):
    layout = QVBoxLayout(window.settings_interface)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    window.settings_pivot = Pivot(window)
    window.settings_stacked_widget = QStackedWidget()

    add_settings_sub_interface(window, "mode_interface", "settings_mode")
    add_settings_sub_interface(window, "codec_interface", "settings_codec")
    add_settings_sub_interface(window, "cover_interface", "settings_cover")
    add_settings_sub_interface(window, "path_interface", "settings_path")
    add_settings_sub_interface(window, "template_interface", "settings_template")
    add_settings_sub_interface(window, "quality_interface", "settings_quality")
    add_settings_sub_interface(window, "log_interface", "settings_log")

    layout.addWidget(window.settings_pivot)
    layout.addWidget(window.settings_stacked_widget)
    window.settings_pivot.setCurrentItem("mode_interface")


def add_settings_sub_interface(window, object_name, text_key):
    widget = QWidget()
    widget.setObjectName(object_name)

    if object_name == "mode_interface":
        window.create_mode_settings_page(widget)
    elif object_name == "codec_interface":
        window.create_codec_settings_page(widget)
    elif object_name == "cover_interface":
        window.create_cover_settings_page(widget)
    elif object_name == "path_interface":
        window.create_path_settings_page(widget)
    elif object_name == "template_interface":
        window.create_template_settings_page(widget)
    elif object_name == "quality_interface":
        window.create_quality_settings_page(widget)
    elif object_name == "log_interface":
        window.create_log_settings_page(widget)

    window.settings_stacked_widget.addWidget(widget)
    window.settings_pivot.addItem(
        routeKey=object_name,
        text=window.tr_text(text_key),
        onClick=lambda: window.settings_stacked_widget.setCurrentWidget(widget),
    )


def build_download_ui(window):
    layout = QVBoxLayout(window.download_interface)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    window.url_title = SubtitleLabel(window.tr_text("download_urls"))
    layout.addWidget(window.url_title)

    window.url_input = TextEdit()
    window.url_input.setPlaceholderText(window.tr_text("placeholder_urls"))
    window.url_input.setMaximumHeight(100)
    layout.addWidget(window.url_input)

    line1 = QFrame()
    line1.setFrameShape(QFrame.Shape.HLine)
    line1.setFrameShadow(QFrame.Shadow.Sunken)
    layout.addWidget(line1)

    window.path_title = SubtitleLabel(window.tr_text("download_paths"))
    layout.addWidget(window.path_title)

    path_layout = QGridLayout()
    path_layout.setSpacing(10)

    window.cookie_label_widget = QLabel(window.tr_text("label_cookie"))
    path_layout.addWidget(window.cookie_label_widget, 0, 0)
    window.cookie_path = LineEdit()
    window.cookie_path.setPlaceholderText(window.tr_text("placeholder_cookie"))
    path_layout.addWidget(window.cookie_path, 0, 1)
    window.cookie_button = PushButton(window.tr_text("btn_browse"))
    window.cookie_button.clicked.connect(window.select_cookie_file)
    path_layout.addWidget(window.cookie_button, 0, 2)

    window.output_label_widget = QLabel(window.tr_text("label_output"))
    path_layout.addWidget(window.output_label_widget, 1, 0)
    window.output_path = LineEdit()
    window.output_path.setPlaceholderText(window.tr_text("placeholder_output"))
    path_layout.addWidget(window.output_path, 1, 1)
    window.output_button = PushButton(window.tr_text("btn_browse"))
    window.output_button.clicked.connect(window.select_output_directory)
    path_layout.addWidget(window.output_button, 1, 2)

    layout.addLayout(path_layout)

    line2 = QFrame()
    line2.setFrameShape(QFrame.Shape.HLine)
    line2.setFrameShadow(QFrame.Shadow.Sunken)
    layout.addWidget(line2)

    window.options_title = SubtitleLabel(window.tr_text("download_options"))
    layout.addWidget(window.options_title)

    options_layout = QVBoxLayout()
    options_layout.setSpacing(10)

    checkboxes_layout = QGridLayout()
    checkboxes_layout.setSpacing(10)

    window.overwrite = CheckBox(window.tr_text("opt_overwrite"))
    window.disable_music_video_skip = CheckBox(window.tr_text("opt_disable_mv_skip"))
    window.save_playlist = CheckBox(window.tr_text("opt_save_playlist"))
    window.synced_lyrics_only = CheckBox(window.tr_text("opt_synced_only"))
    window.no_synced_lyrics = CheckBox(window.tr_text("opt_no_synced"))
    window.read_urls_as_txt = CheckBox(window.tr_text("opt_read_urls_txt"))
    window.no_exceptions = CheckBox(window.tr_text("opt_no_exceptions"))

    checkboxes_layout.addWidget(window.overwrite, 0, 0)
    checkboxes_layout.addWidget(window.disable_music_video_skip, 0, 1)
    checkboxes_layout.addWidget(window.save_playlist, 1, 0)
    checkboxes_layout.addWidget(window.synced_lyrics_only, 1, 1)
    checkboxes_layout.addWidget(window.no_synced_lyrics, 2, 0)
    checkboxes_layout.addWidget(window.read_urls_as_txt, 2, 1)
    checkboxes_layout.addWidget(window.no_exceptions, 3, 0)

    options_layout.addLayout(checkboxes_layout)

    format_layout = QHBoxLayout()
    format_layout.setSpacing(10)
    window.audio_convert_label = QLabel(window.tr_text("label_audio_convert"))
    format_layout.addWidget(window.audio_convert_label)

    window.audio_format = ComboBox()
    window.audio_format.addItems(["保持原格式", "mp3", "flac", "wav", "aac", "m4a", "ogg", "wma"])
    format_layout.addWidget(window.audio_format)

    window.video_convert_label = QLabel(window.tr_text("label_video_convert"))
    format_layout.addWidget(window.video_convert_label)

    window.video_format = ComboBox()
    window.video_format.addItems(["保持原格式", "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm"])
    format_layout.addWidget(window.video_format)

    options_layout.addLayout(format_layout)
    layout.addLayout(options_layout)

    line3 = QFrame()
    line3.setFrameShape(QFrame.Shape.HLine)
    line3.setFrameShadow(QFrame.Shadow.Sunken)
    layout.addWidget(line3)

    window.download_btn = PrimaryPushButton(window.tr_text("btn_start"))
    window.download_btn.clicked.connect(window.start_download)
    layout.addWidget(window.download_btn)

    window.progress_bar = ProgressBar()
    window.progress_bar.setTextVisible(True)
    window.progress_bar.setFixedHeight(20)
    layout.addWidget(window.progress_bar)

    layout.addStretch(1)
