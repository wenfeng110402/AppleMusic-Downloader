# Changelog

## [2.5.0] — 2026-09-25

### Added
- Support for syllable-level word-by-word synced lyrics and localized translations via Apple Music Sing endpoint (`syllable-lyrics`)
- Desktop UI options for synced lyrics format selection (LRC, SRT, TTML)
- Desktop UI toggle for "Synced lyrics only" download mode
- Desktop UI custom path and filename templates for albums and tracks
- Integrated lightweight in-app Toast notification system replacing native modal alerts
- Automatic deduplication for batch URL inputs

### Fixed
- Fixed CLI routing regression where passing options (e.g. `-c cookies.txt`) caused Click to crash with `NoSuchOption: -c`
- Resolved security vulnerabilities in frontend dependencies

### Changed
- Refactored CLI `--help` with clear parameter summaries and added `--gamdl-help` flag
- Streamlined audio codec options to verified playable formats (AAC, AAC-HE, Dolby Atmos), removing unsupported ALAC

## [2.0.0] — 2026-07-08

### Added
- Web-based GUI (Next.js + FastAPI)
- Download queue with real-time WebSocket progress
- Settings persistence via API
- Dependency check UI (FFmpeg, N_m3u8DL-RE, MP4Box)
- Dark/Light theme toggle
- Chinese/English i18n

### Changed
- Migrated from Flet GUI to pywebview desktop mode
- Restructured backend with FastAPI
- Separated frontend and backend for flexible deployment

### Fixed
- Cross-origin request handling in development
- Various type annotation issues
- Format conversion parameter passing

## [1.0.0] — 2026-06-xx

### Added
- Initial release with CLI and Flet GUI
- Apple Music download via gamdl
- Audio format conversion (FFmpeg)
- Basic task management
