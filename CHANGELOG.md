# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-XX - Initial Release (P2)

### Added

#### Installation & Setup
- **New `neshama init --config` command**: Interactive configuration wizard with 3-step setup
  - Select from 21 LLM providers
  - Enter API key
  - Choose from 8 themes
  - Configuration saved to `~/.neshama/config.yaml`
- **New `neshama version` command**: Display version information
- **Improved `neshama` CLI**: Added banner, better help text, and quick start guide
- **Enhanced `neshama init`**: Legacy mode preserved for creating personality SKILL.md files

#### Soul Panel Welcome Flow
- **New Welcome modal**: 3-step onboarding for first-time users
  - Step 1: Configure LLM Provider (7 popular providers displayed)
  - Step 2: Choose Personality Template (5 presets)
  - Step 3: Start using (Dashboard or Chat options)
- **Theme preview**: Visual theme selector in welcome flow
- **Skip option**: Users can skip configuration and set up later
- **LocalStorage persistence**: Welcome completion state saved

#### Documentation
- **New `README.md`**: Comprehensive project documentation with:
  - Project overview and vision
  - Architecture diagram
  - Quick start guide
  - Feature showcase
  - Available themes
  - Supported LLM providers
  - Testing information
- **New `docs/getting-started.md`**: Detailed tutorial covering:
  - Installation options
  - Configuration wizard usage
  - Soul Panel features
  - CLI commands reference
  - Configuration file guide
  - Custom personality creation
  - API usage examples
  - Troubleshooting tips

#### Packaging
- **New `LICENSE` file**: Apache 2.0 license (matching Coze Studio)
- **New `CHANGELOG.md`**: Version history tracking
- **Updated `pyproject.toml`**: Enhanced metadata and classifiers

### Changed

#### CLI Improvements
- Banner now shows logo and tagline
- Better error messages for missing dependencies
- Improved help text with examples
- Default command shows version and quick start hints

#### Web Interface
- Added welcome modal overlay styling
- Added CSS variables for welcome page components
- Updated i18n with welcome flow translations (English + Chinese)
- Added `navigateTo()` function for programmatic page navigation

### Fixed

- CLI `--version` flag now properly shows version
- `neshama dashboard` dependency check improved
- Welcome modal properly hides after completion

---

## [0.1.0] - 2025-XX-XX - Development (P1)

### Added

#### Core Systems
- **Soul System**: OCEAN personality model with 5 factors
- **Personality Module**: Trait configuration, desire priorities, behavioral patterns
- **Engine**: Main NeshamaEngine for chat interactions

#### Emotion Engine
- **Base Emotions**: 15 emotion types (Joy, Trust, Fear, Surprise, Sadness, Disgust, Anger, Anticipation, etc.)
- **Composite Emotions**: 15 preset emotion recipes with synthesis logic
- **Emotion Decay**: Time-based intensity reduction
- **Conflict Resolution**: Priority-based emotion conflict handling
- **Triggered Behaviors**: Emotional state affects response style

#### Entity Graph
- **8 Entity Types**: Person, Organization, Location, Concept, Event, Object, Media, Topic
- **15 Relation Types**: KNOWS, WORKS_FOR, LOCATED_IN, PART_OF, SIMILAR_TO, etc.
- **BFS Path Query**: Shortest path between entities
- **Entity Extraction**: Automatic entity recognition from text

#### Memory System
- **Progressive Summarization**: L0 (raw) → L1 (summarized) → L2 (distilled)
- **Layered Architecture**: Short-term and long-term memory
- **Auto-trigger**: Automatic summarization based on entry count

#### Model Adapter Layer
- **21 LLM Providers**: OpenAI, Anthropic, Google, Chinese providers, etc.
- **55+ Models**: Pricing information for cost tracking
- **Unified API**: Consistent interface across all providers
- **Provider Registry**: Easy provider switching

#### Soul Panel Desktop Client
- **12 Pages**: Dashboard, Soul Config, Chat, Emotion, Entity Graph, Memory, etc.
- **8 Themes**: Ocean, Spring, Midnight, Cyberpunk, Sunset, Forest, Slate, Purple
- **i18n**: English and Chinese language support
- **FastAPI Backend**: REST API for frontend communication
- **pywebview**: Native desktop window

#### Testing
- **190 Test Cases**: Comprehensive test coverage
- **Core Tests**: Engine, personality, OCEAN model
- **Emotion Tests**: Composite emotions, decay, conflict
- **Entity Tests**: Graph operations, path finding

---

## [Unreleased] - Future Plans

### Planned Features
- [ ] More personality presets
- [ ] Emotion visualization charts
- [ ] Custom entity type creation
- [ ] Memory export/import
- [ ] Plugin system for tools
- [ ] Multi-agent support
- [ ] Cloud sync for configuration
- [ ] Mobile companion app

### Known Limitations
- Some Chinese LLM providers require additional configuration
- Memory auto-summarization triggers may need tuning
- Entity extraction accuracy varies by provider

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 1.0.0 | 2026-01-XX | Current (P2 - New User Experience) |
| 0.1.0 | 2025-XX-XX | Development (P1 - Core Features) |
