"""
UI builder - AppleMusic Downloader
Clean card-based layout with generous spacing.
"""

from PyQt6.QtWidgets import (
    QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget, QGridLayout,
)

from qfluentwidgets import (
    BodyLabel, CheckBox, ComboBox, FluentIcon, HeaderCardWidget,
    LineEdit, NavigationItemPosition, Pivot, PrimaryPushButton,
    ProgressBar, PushButton, ScrollArea, SpinBox, TextEdit,
)


# ─────────────────── sidebar ───────────────────

def build_main_ui(window):
    window.download_interface = QWidget()
    window.download_interface.setObjectName("downloadInterface")
    window.settings_interface = QWidget()
    window.settings_interface.setObjectName("settingsInterface")

    build_download_ui(window)
    build_settings_ui(window)

    window.addSubInterface(
        window.download_interface, FluentIcon.DOWNLOAD,
        window.tr_text("nav_download"),
    )
    window.addSubInterface(
        window.settings_interface, FluentIcon.SETTING,
        window.tr_text("nav_settings"),
        NavigationItemPosition.BOTTOM,
    )
    # Language switcher in sidebar - switches to Settings > Codec tab
    window.navigationInterface.addItem(
        routeKey="langSwitch",
        icon=FluentIcon.GLOBE,
        text=window.tr_text("settings_language"),
        onClick=lambda: _go_language(window),
        selectable=False,
        position=NavigationItemPosition.BOTTOM,
    )
    window.apply_runtime_translations()


def build_settings_ui(window):
    lay = QVBoxLayout(window.settings_interface)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)

    window.settings_pivot = Pivot(window)
    window.settings_stacked = QStackedWidget()
    _add_tab(window, "codec", "settings_codec")
    _add_tab(window, "output", "settings_path")
    _add_tab(window, "templates", "settings_template")

    lay.addWidget(window.settings_pivot)
    lay.addWidget(window.settings_stacked)
    window.settings_pivot.setCurrentItem("codec")


def _add_tab(window, key, text_key):
    w = QWidget()
    w.setObjectName(key)
    fn = {
        "codec": _build_codec_tab,
        "output": _build_output_tab,
        "templates": _build_templates_tab,
    }.get(key)
    if fn:
        fn(window, w)
    window.settings_stacked.addWidget(w)
    window.settings_pivot.addItem(
        routeKey=key, text=window.tr_text(text_key),
        onClick=lambda _, ww=w: window.settings_stacked.setCurrentWidget(ww),
    )


# ─────────────────── download page ───────────────────

def build_download_ui(window):
    scroll = ScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")

    page = QWidget()
    page.setStyleSheet("background:transparent;")
    root = QVBoxLayout(page)
    root.setContentsMargins(24, 24, 24, 24)
    root.setSpacing(20)

    # URLs
    url_card = _card(window.tr_text("download_urls"))
    window.url_input = TextEdit()
    window.url_input.setPlaceholderText(window.tr_text("placeholder_urls"))
    window.url_input.setMaximumHeight(80)
    window.url_input.setMinimumHeight(60)
    url_card.viewLayout.addWidget(window.url_input)
    root.addWidget(url_card)

    # Paths
    paths_card = _card(window.tr_text("download_paths"))
    pg = QGridLayout()
    pg.setSpacing(8)
    window.cookie_path = LineEdit()
    window.cookie_path.setPlaceholderText(window.tr_text("placeholder_cookie"))
    window.cookie_button = PushButton(window.tr_text("btn_browse"))
    window.cookie_button.clicked.connect(window.select_cookie_file)
    window.output_path = LineEdit()
    window.output_path.setPlaceholderText(window.tr_text("placeholder_output"))
    window.output_button = PushButton(window.tr_text("btn_browse"))
    window.output_button.clicked.connect(window.select_output_directory)
    pg.addWidget(BodyLabel(window.tr_text("label_cookie")), 0, 0)
    pg.addWidget(window.cookie_path, 0, 1)
    pg.addWidget(window.cookie_button, 0, 2)
    pg.addWidget(BodyLabel(window.tr_text("label_output")), 1, 0)
    pg.addWidget(window.output_path, 1, 1)
    pg.addWidget(window.output_button, 1, 2)
    paths_card.viewLayout.addLayout(pg)
    root.addWidget(paths_card)

    # Actions
    act_card = _card("")
    window.progress_bar = ProgressBar()
    window.progress_bar.setTextVisible(True)
    window.progress_bar.setFixedHeight(20)
    act_card.viewLayout.addWidget(window.progress_bar)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(12)
    window.download_btn = PrimaryPushButton(window.tr_text("btn_start"))
    window.download_btn.setFixedHeight(38)
    window.download_btn.clicked.connect(window.start_download)
    window.stop_btn = PushButton(window.tr_text("btn_stop"))
    window.stop_btn.setFixedHeight(38)
    window.stop_btn.clicked.connect(window.stop_download)
    window.stop_btn.setEnabled(False)
    btn_row.addWidget(window.download_btn)
    btn_row.addWidget(window.stop_btn)
    btn_row.addStretch()
    act_card.viewLayout.addLayout(btn_row)
    root.addWidget(act_card)

    # Log
    log_card = _card(window.tr_text("page_log_title"))
    window.status_text = TextEdit()
    window.status_text.setReadOnly(True)
    window.status_text.setMinimumHeight(100)
    window.status_text.setMaximumHeight(180)
    log_card.viewLayout.addWidget(window.status_text)
    clr = PushButton(window.tr_text("btn_clear_log"))
    clr.clicked.connect(window.clear_log)
    log_card.viewLayout.addWidget(clr)
    root.addWidget(log_card)

    root.addStretch()
    scroll.setWidget(page)

    outer = QVBoxLayout(window.download_interface)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.addWidget(scroll)


# ─────────────────── helpers ───────────────────


def _card(title):
    c = HeaderCardWidget()
    if title:
        c.setTitle(title)
    c.viewLayout.setContentsMargins(24, 8, 24, 20)
    return c


def _go_language(window):
    window.switchTo(window.settings_interface)
    window.settings_pivot.setCurrentItem("codec")


# ─────────────────── codec tab ───────────────────


def _build_codec_tab(window, parent):
    lay = QVBoxLayout(parent)
    lay.setContentsMargins(24, 24, 24, 24)
    lay.setSpacing(24)

    # Language
    lang_card = _card("Language / language")
    lang_row = QHBoxLayout()
    lang_row.setSpacing(8)
    window.language_combo = ComboBox()
    window.language_combo.addItem("Chinese")
    window.language_combo.addItem("English")
    window.language_combo.setMinimumWidth(200)
    window.language_combo.currentIndexChanged.connect(window.on_language_changed)
    lang_row.addWidget(window.language_combo)
    lang_row.addStretch()
    lang_card.viewLayout.addLayout(lang_row)
    lay.addWidget(lang_card)

    # Codec — side by side
    codec_card = _card(window.tr_text("settings_codec"))
    codec_row = QHBoxLayout()
    codec_row.setSpacing(16)

    def _codec_group(label, combo):
        vb = QVBoxLayout()
        vb.setSpacing(4)
        vb.addWidget(BodyLabel(label))
        combo.setFixedHeight(34)
        vb.addWidget(combo)
        return vb

    window.codec_song = ComboBox()
    window.codec_song.addItems(["aac-web", "aac", "alac", "atmos", "ac3", "aac-he", "ask"])
    codec_row.addLayout(_codec_group(window.tr_text("label_codec_song"), window.codec_song))

    window.codec_music_video = ComboBox()
    window.codec_music_video.addItems(["h264", "h265", "ask"])
    codec_row.addLayout(_codec_group(window.tr_text("label_codec_mv"), window.codec_music_video))

    window.quality_post = ComboBox()
    window.quality_post.addItems(["best", "ask"])
    codec_row.addLayout(_codec_group(window.tr_text("label_quality_post"), window.quality_post))

    codec_row.addStretch()
    codec_card.viewLayout.addLayout(codec_row)
    lay.addWidget(codec_card)

    # Download mode — side by side
    mode_card = _card(window.tr_text("settings_mode"))
    mode_row = QHBoxLayout()
    mode_row.setSpacing(16)

    window.download_mode = ComboBox()
    window.download_mode.addItems(["ytdlp", "nm3u8dlre"])
    window.download_mode.setFixedHeight(34)
    window.remux_mode = ComboBox()
    window.remux_mode.addItems(["ffmpeg", "mp4box"])
    window.remux_mode.setFixedHeight(34)

    mode_row.addLayout(_codec_group(window.tr_text("label_download_mode"), window.download_mode))
    mode_row.addLayout(_codec_group(window.tr_text("label_remux_mode"), window.remux_mode))
    mode_row.addStretch()
    mode_card.viewLayout.addLayout(mode_row)
    lay.addWidget(mode_card)

    # Options — vertical spacing increased
    opt_card = _card(window.tr_text("download_options"))
    cbg = QGridLayout()
    cbg.setSpacing(16)
    window.overwrite = CheckBox(window.tr_text("opt_overwrite"))
    window.disable_music_video_skip = CheckBox(window.tr_text("opt_disable_mv_skip"))
    window.save_playlist = CheckBox(window.tr_text("opt_save_playlist"))
    window.synced_lyrics_only = CheckBox(window.tr_text("opt_synced_only"))
    window.no_synced_lyrics = CheckBox(window.tr_text("opt_no_synced"))
    window.read_urls_as_txt = CheckBox(window.tr_text("opt_read_urls_txt"))
    window.no_exceptions = CheckBox(window.tr_text("opt_no_exceptions"))
    cbg.addWidget(window.overwrite, 0, 0)
    cbg.addWidget(window.disable_music_video_skip, 0, 1)
    cbg.addWidget(window.save_playlist, 1, 0)
    cbg.addWidget(window.synced_lyrics_only, 1, 1)
    cbg.addWidget(window.no_synced_lyrics, 2, 0)
    cbg.addWidget(window.read_urls_as_txt, 2, 1)
    cbg.addWidget(window.no_exceptions, 3, 0)
    opt_card.viewLayout.addLayout(cbg)
    lay.addWidget(opt_card)

    lay.addStretch()


# ─────────────────── output tab ───────────────────


def _build_output_tab(window, parent):
    lay = QVBoxLayout(parent)
    lay.setContentsMargins(24, 24, 24, 24)
    lay.setSpacing(24)

    # Cover
    cv = _card(window.tr_text("settings_cover"))
    cg = QGridLayout()
    cg.setSpacing(10)
    window.cover_format = ComboBox()
    window.cover_format.addItems(["jpg", "png"])
    window.cover_format.setMinimumWidth(200)
    window.cover_size = SpinBox()
    window.cover_size.setRange(90, 10000)
    window.cover_size.setValue(1200)
    window.cover_size.setMinimumWidth(140)
    cg.addWidget(BodyLabel(window.tr_text("label_cover_format")), 0, 0)
    cg.addWidget(window.cover_format, 0, 1)
    cg.addWidget(BodyLabel(window.tr_text("label_cover_size")), 1, 0)
    cg.addWidget(window.cover_size, 1, 1)
    cv.viewLayout.addLayout(cg)
    lay.addWidget(cv)

    # Paths
    pc = _card(window.tr_text("settings_path"))
    pg = QGridLayout()
    pg.setSpacing(10)
    window.temp_path = LineEdit()
    window.temp_path.setText("./temp")
    window.temp_path.setMinimumWidth(300)
    window.wvd_path = LineEdit()
    window.wvd_path.setMinimumWidth(300)
    window.truncate = SpinBox()
    window.truncate.setRange(0, 1000)
    window.truncate.setValue(0)
    window.truncate.setMinimumWidth(100)
    pg.addWidget(BodyLabel(window.tr_text("label_temp_path")), 0, 0)
    pg.addWidget(window.temp_path, 0, 1)
    pg.addWidget(BodyLabel(window.tr_text("label_wvd_path")), 1, 0)
    pg.addWidget(window.wvd_path, 1, 1)
    pg.addWidget(BodyLabel(window.tr_text("label_truncate")), 2, 0)
    pg.addWidget(window.truncate, 2, 1)
    pc.viewLayout.addLayout(pg)
    lay.addWidget(pc)

    # Format conversion
    fc = _card(window.tr_text("label_audio_convert"))
    fg = QGridLayout()
    fg.setSpacing(10)
    window.audio_format = ComboBox()
    window.audio_format.addItems(["keep original", "mp3", "flac", "wav", "ogg", "wma"])
    window.audio_format.setMinimumWidth(200)
    window.video_format = ComboBox()
    window.video_format.addItems(["keep original", "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm"])
    window.video_format.setMinimumWidth(200)
    fg.addWidget(BodyLabel(window.tr_text("label_audio_convert")), 0, 0)
    fg.addWidget(window.audio_format, 0, 1)
    fg.addWidget(BodyLabel(window.tr_text("label_video_convert")), 1, 0)
    fg.addWidget(window.video_format, 1, 1)
    fc.viewLayout.addLayout(fg)
    lay.addWidget(fc)

    lay.addStretch()


# ─────────────────── templates tab ───────────────────


def _build_templates_tab(window, parent):
    lay = QVBoxLayout(parent)
    lay.setContentsMargins(24, 24, 24, 24)
    lay.setSpacing(24)

    c = _card(window.tr_text("settings_template"))
    g = QGridLayout()
    g.setSpacing(10)

    def _row(r, key, default):
        g.addWidget(BodyLabel(window.tr_text(key)), r, 0)
        le = LineEdit()
        le.setText(default)
        attr = {
            "label_tpl_album": "template_folder_album",
            "label_tpl_comp": "template_folder_compilation",
            "label_tpl_single": "template_file_single_disc",
            "label_tpl_multi": "template_file_multi_disc",
        }.get(key, key)
        setattr(window, attr, le)
        g.addWidget(le, r, 1)

    _row(0, "label_tpl_album", "{album_artist}/{album}")
    _row(1, "label_tpl_comp", "Compilations/{album}")
    _row(2, "label_tpl_single", "{track:02d} {title}")
    _row(3, "label_tpl_multi", "{disc}-{track:02d} {title}")
    c.viewLayout.addLayout(g)

    pick = QHBoxLayout()
    pick.setSpacing(8)
    lbl = BodyLabel(window.tr_text("label_tpl_available_params"))
    pick.addWidget(lbl)
    cmb = ComboBox()
    cmb.addItems(["{album_artist}", "{album}", "{artist}", "{title}", "{track:02d}", "{disc}"])
    pick.addWidget(cmb)
    window.template_param_combo = cmb
    ibtn = PushButton(window.tr_text("btn_tpl_insert_param"))
    ibtn.clicked.connect(window.insert_selected_template_param)
    pick.addWidget(ibtn)
    pick.addStretch()
    c.viewLayout.addLayout(pick)
    lay.addWidget(c)

    sbtn = PrimaryPushButton(window.tr_text("btn_save_settings"))
    sbtn.clicked.connect(window.save_settings)
    lay.addWidget(sbtn)
    lay.addStretch()

    # Save references for insert_selected_template_param
    window.template_param_label = lbl
    window.template_param_insert_btn = ibtn
