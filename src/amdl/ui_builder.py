from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QStackedWidget
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
    ScrollArea,
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

    add_settings_sub_interface(window, "templates_interface", "settings_template")

    layout.addWidget(window.settings_pivot)
    layout.addWidget(window.settings_stacked_widget)
    window.settings_pivot.setCurrentItem("templates_interface")


def add_settings_sub_interface(window, object_name, text_key):
    widget = QWidget()
    widget.setObjectName(object_name)

    if object_name == "templates_interface":
        window.create_template_settings_page(widget)

    window.settings_stacked_widget.addWidget(widget)
    window.settings_pivot.addItem(
        routeKey=object_name,
        text=window.tr_text(text_key),
        onClick=lambda w=widget: window.settings_stacked_widget.setCurrentWidget(w),
    )


def build_download_ui(window):
    # Scrollable main area
    scroll = ScrollArea()
    scroll.setWidgetResizable(True)
    scroll_widget = QWidget()
    layout = QVBoxLayout(scroll_widget)
    layout.setContentsMargins(20, 16, 20, 16)
    layout.setSpacing(12)

    # ---- URLs ----
    window.url_title = SubtitleLabel(window.tr_text("download_urls"))
    layout.addWidget(window.url_title)

    window.url_input = TextEdit()
    window.url_input.setPlaceholderText(window.tr_text("placeholder_urls"))
    window.url_input.setMaximumHeight(80)
    window.url_input.setMinimumHeight(60)
    layout.addWidget(window.url_input)

    # ---- Paths ----
    window.path_title = SubtitleLabel(window.tr_text("download_paths"))
    layout.addWidget(window.path_title)

    path_layout = QGridLayout()
    path_layout.setSpacing(8)

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

    # ---- Quick Settings (codec, mode, quality, cover, language) ----
    window.options_title = SubtitleLabel(window.tr_text("download_options"))
    layout.addWidget(window.options_title)

    quick_grid = QGridLayout()
    quick_grid.setSpacing(8)

    # Row 0: Song Codec | MV Codec | Post Quality
    quick_grid.addWidget(QLabel(window.tr_text("label_codec_song")), 0, 0)
    window.codec_song = ComboBox()
    window.codec_song.addItems(["aac", "aac-he", "atmos"])
    window.codec_song.setMinimumWidth(100)
    quick_grid.addWidget(window.codec_song, 0, 1)

    quick_grid.addWidget(QLabel(window.tr_text("label_codec_mv")), 0, 2)
    window.codec_music_video = ComboBox()
    window.codec_music_video.addItems(["h264", "h265", "ask"])
    window.codec_music_video.setMinimumWidth(100)
    quick_grid.addWidget(window.codec_music_video, 0, 3)

    quick_grid.addWidget(QLabel(window.tr_text("label_quality_post")), 0, 4)
    window.quality_post = ComboBox()
    window.quality_post.addItems(["best", "ask"])
    window.quality_post.setMinimumWidth(100)
    quick_grid.addWidget(window.quality_post, 0, 5)

    # Row 1: Download Mode | Remux Mode | Cover Format | Cover Size | Language
    quick_grid.addWidget(QLabel(window.tr_text("label_download_mode")), 1, 0)
    window.download_mode = ComboBox()
    window.download_mode.addItems(["ytdlp", "nm3u8dlre"])
    window.download_mode.setMinimumWidth(100)
    quick_grid.addWidget(window.download_mode, 1, 1)

    quick_grid.addWidget(QLabel(window.tr_text("label_remux_mode")), 1, 2)
    window.remux_mode = ComboBox()
    window.remux_mode.addItems(["ffmpeg", "mp4box"])
    window.remux_mode.setMinimumWidth(100)
    quick_grid.addWidget(window.remux_mode, 1, 3)

    quick_grid.addWidget(QLabel(window.tr_text("label_cover_format")), 1, 4)
    cover_formats = QHBoxLayout()
    cover_formats.setSpacing(4)
    window.cover_format = ComboBox()
    window.cover_format.addItems(["jpg", "png"])
    window.cover_format.setMinimumWidth(70)
    cover_formats.addWidget(window.cover_format)
    window.cover_size = SpinBox()
    window.cover_size.setRange(90, 10000)
    window.cover_size.setValue(1200)
    window.cover_size.setMinimumWidth(70)
    window.cover_size.setPrefix("#")
    cover_formats.addWidget(window.cover_size)
    quick_grid.addLayout(cover_formats, 1, 5)

    layout.addLayout(quick_grid)

    # ---- Language (compact) ----
    lang_line = QHBoxLayout()
    lang_line.addWidget(QLabel(window.tr_text("label_language")))
    window.language_combo = ComboBox()
    window.language_combo.addItem(window.tr_text("lang_zh"))
    window.language_combo.addItem(window.tr_text("lang_en"))
    window.language_combo.setMaximumWidth(150)
    window.language_combo.currentIndexChanged.connect(window.on_language_changed)
    lang_line.addWidget(window.language_combo)
    lang_line.addStretch()
    layout.addLayout(lang_line)

    # ---- Checkboxes ----
    checkboxes_layout = QGridLayout()
    checkboxes_layout.setSpacing(6)

    window.overwrite = CheckBox(window.tr_text("opt_overwrite"))
    window.disable_music_video_skip = CheckBox(window.tr_text("opt_disable_mv_skip"))
    window.save_playlist = CheckBox(window.tr_text("opt_save_playlist"))
    window.synced_lyrics_only = CheckBox(window.tr_text("opt_synced_only"))
    window.no_synced_lyrics = CheckBox(window.tr_text("opt_no_synced"))
    window.read_urls_as_txt = CheckBox(window.tr_text("opt_read_urls_txt"))
    window.no_exceptions = CheckBox(window.tr_text("opt_no_exceptions"))

    checkboxes_layout.addWidget(window.overwrite, 0, 0)
    checkboxes_layout.addWidget(window.disable_music_video_skip, 0, 1)
    checkboxes_layout.addWidget(window.save_playlist, 0, 2)
    checkboxes_layout.addWidget(window.synced_lyrics_only, 1, 0)
    checkboxes_layout.addWidget(window.no_synced_lyrics, 1, 1)
    checkboxes_layout.addWidget(window.read_urls_as_txt, 1, 2)
    checkboxes_layout.addWidget(window.no_exceptions, 2, 0)

    layout.addLayout(checkboxes_layout)

    # ---- Advanced paths (compact, inline) ----
    adv_layout = QHBoxLayout()
    adv_layout.setSpacing(10)
    adv_layout.addWidget(QLabel(window.tr_text("label_temp_path")))
    window.temp_path = LineEdit()
    window.temp_path.setText("./temp")
    window.temp_path.setMinimumWidth(120)
    adv_layout.addWidget(window.temp_path)
    adv_layout.addWidget(QLabel(window.tr_text("label_wvd_path")))
    window.wvd_path = LineEdit()
    window.wvd_path.setMinimumWidth(120)
    adv_layout.addWidget(window.wvd_path)
    adv_layout.addWidget(QLabel(window.tr_text("label_truncate")))
    window.truncate = SpinBox()
    window.truncate.setRange(0, 1000)
    window.truncate.setValue(0)
    window.truncate.setMinimumWidth(70)
    adv_layout.addWidget(window.truncate)
    adv_layout.addStretch()
    layout.addLayout(adv_layout)

    # ---- Format conversion ----
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
    layout.addLayout(format_layout)

    # ---- Buttons ----
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)

    window.download_btn = PrimaryPushButton(window.tr_text("btn_start"))
    window.download_btn.clicked.connect(window.start_download)
    btn_layout.addWidget(window.download_btn)

    window.stop_btn = PushButton(window.tr_text("btn_stop"))
    window.stop_btn.clicked.connect(window.stop_download)
    window.stop_btn.setEnabled(False)
    btn_layout.addWidget(window.stop_btn)
    btn_layout.addStretch()

    layout.addLayout(btn_layout)

    # ---- Progress ----
    window.progress_bar = ProgressBar()
    window.progress_bar.setTextVisible(True)
    window.progress_bar.setFixedHeight(20)
    layout.addWidget(window.progress_bar)

    # ---- Log area (inline, at bottom of download page) ----
    window.status_text = TextEdit()
    window.status_text.setReadOnly(True)
    window.status_text.setMinimumHeight(80)
    window.status_text.setMaximumHeight(160)
    window.status_text.setPlaceholderText("下载日志将显示在此处...")
    layout.addWidget(window.status_text)

    clear_btn = PushButton(window.tr_text("btn_clear_log"))
    clear_btn.clicked.connect(window.clear_log)
    layout.addWidget(clear_btn, alignment=0)

    scroll.setWidget(scroll_widget)
    # Replace the download_interface layout with the scroll area
    outer = QVBoxLayout(window.download_interface)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.addWidget(scroll)
