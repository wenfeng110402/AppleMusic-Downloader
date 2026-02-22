from amdl.i18n import I18N


def save_window_settings(window):
    settings = window.settings
    settings.setValue("cookie_path", window.cookie_path.text())
    settings.setValue("output_path", window.output_path.text())
    settings.setValue("overwrite", window.overwrite.isChecked())
    settings.setValue("disable_music_video_skip", window.disable_music_video_skip.isChecked())
    settings.setValue("save_playlist", window.save_playlist.isChecked())
    settings.setValue("synced_lyrics_only", window.synced_lyrics_only.isChecked())
    settings.setValue("no_synced_lyrics", window.no_synced_lyrics.isChecked())
    settings.setValue("read_urls_as_txt", window.read_urls_as_txt.isChecked())
    settings.setValue("no_exceptions", window.no_exceptions.isChecked())
    settings.setValue("codec_song", window.codec_song.currentText())
    settings.setValue("codec_music_video", window.codec_music_video.currentText())
    settings.setValue("quality_post", window.quality_post.currentText())
    settings.setValue("download_mode", window.download_mode.currentText())
    settings.setValue("remux_mode", window.remux_mode.currentText())
    settings.setValue("cover_format", window.cover_format.currentText())
    settings.setValue("cover_size", window.cover_size.value())
    settings.setValue("truncate", window.truncate.value())
    settings.setValue("temp_path", window.temp_path.text())
    settings.setValue("wvd_path", window.wvd_path.text())
    settings.setValue("template_folder_album", window.template_folder_album.text())
    settings.setValue("template_folder_compilation", window.template_folder_compilation.text())
    settings.setValue("template_file_single_disc", window.template_file_single_disc.text())
    settings.setValue("template_file_multi_disc", window.template_file_multi_disc.text())
    settings.setValue("audio_format", window.audio_format.currentText())
    settings.setValue("video_format", window.video_format.currentText())
    settings.setValue("ui_language", window.current_language)


def load_window_settings(window):
    settings = window.settings
    window.cookie_path.setText(settings.value("cookie_path", ""))
    window.output_path.setText(settings.value("output_path", ""))
    window.overwrite.setChecked(settings.value("overwrite", False, type=bool))
    window.disable_music_video_skip.setChecked(settings.value("disable_music_video_skip", False, type=bool))
    window.save_playlist.setChecked(settings.value("save_playlist", False, type=bool))
    window.synced_lyrics_only.setChecked(settings.value("synced_lyrics_only", False, type=bool))
    window.no_synced_lyrics.setChecked(settings.value("no_synced_lyrics", False, type=bool))
    window.read_urls_as_txt.setChecked(settings.value("read_urls_as_txt", False, type=bool))
    window.no_exceptions.setChecked(settings.value("no_exceptions", False, type=bool))
    window.codec_song.setCurrentText(settings.value("codec_song", "aac-legacy"))
    window.codec_music_video.setCurrentText(settings.value("codec_music_video", "h264"))
    window.quality_post.setCurrentText(settings.value("quality_post", "best"))
    window.download_mode.setCurrentText(settings.value("download_mode", "ytdlp"))
    window.remux_mode.setCurrentText(settings.value("remux_mode", "ffmpeg"))
    window.cover_format.setCurrentText(settings.value("cover_format", "jpg"))
    window.cover_size.setValue(settings.value("cover_size", 1200, type=int))
    window.truncate.setValue(settings.value("truncate", 0, type=int))
    window.temp_path.setText(settings.value("temp_path", "./temp"))
    window.wvd_path.setText(settings.value("wvd_path", ""))
    window.template_folder_album.setText(settings.value("template_folder_album", "{album_artist}/{album}"))
    window.template_folder_compilation.setText(settings.value("template_folder_compilation", "Compilations/{album}"))
    window.template_file_single_disc.setText(settings.value("template_file_single_disc", "{track:02d} {title}"))
    window.template_file_multi_disc.setText(settings.value("template_file_multi_disc", "{disc}-{track:02d} {title}"))
    window.audio_format.setCurrentText(settings.value("audio_format", "保持原格式"))
    window.video_format.setCurrentText(settings.value("video_format", "保持原格式"))

    window.current_language = settings.value("ui_language", window.current_language)
    if window.current_language not in I18N:
        window.current_language = "zh_CN"

    if hasattr(window, "language_combo"):
        window.language_combo.blockSignals(True)
        window.language_combo.setCurrentIndex(1 if window.current_language == "en_US" else 0)
        window.language_combo.blockSignals(False)
