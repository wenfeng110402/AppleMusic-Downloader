# Changelog

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
