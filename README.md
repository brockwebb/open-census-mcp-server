# Open Census MCP Server
[![Unofficial Project](https://img.shields.io/badge/Census-Unofficial-blue)](#disclaimer)

## Disclaimer <a name="disclaimer"></a>
This is an **independent, open-source experiment**.
It is **not** affiliated with, endorsed by, or sponsored by the U.S. Census Bureau or the Department of Commerce.

Data retrieved through this project remains subject to the terms of the original data providers (e.g., Census API Terms of Service).

## What Is This?

An AI-powered statistical consultant for U.S. Census data. Ask questions in plain English, get accurate demographic data with proper statistical context, methodology guidance, and fitness-for-use caveats.

**The insight:** Census data has a pragmatics problem, not a search problem. Knowing WHICH data to use and HOW to interpret it matters more than finding it. This system encodes statistical consulting expertise into the AI interaction layer.

## Status

🔬 **Active Research & Rebuild** — v3 architecture in progress.
See [docs/lessons_learned/](docs/lessons_learned/) for the v1/v2 journey.

## Vision

Census data influences billions in policy decisions, but accessing it effectively requires specialized knowledge. This project aims to make America's most valuable public dataset as easy to use as asking a question — with the statistical rigor of a professional consultant.

**The opportunity:** Every city council member, journalist, nonprofit director, and curious citizen should be able to fact-check claims and understand their communities with the same ease an eighth-grader uses a search engine. The data is public. The expertise to use it properly shouldn't be gatekept by technical complexity.

## Architecture (v3)

Pure Python MCP server with pragmatic rules engine. No R dependency.

- **Pragmatic Rules Layer:** Fitness-for-use constraints (MOE thresholds, coverage bias, temporal validity, source selection)
- **Census API Integration:** Direct Python calls to Census Bureau APIs
- **Knowledge Base:** Methodology documentation for RAG-enhanced guidance

Details: [docs/architecture/](docs/architecture/) (coming soon)

## Project Structure

```
docs/                  # Systems engineering documentation
  requirements/        # ConOps, SRS
  architecture/        # System architecture
  decisions/           # ADRs, trade studies
  design/              # Detailed design
  verification/        # V&V, evaluation results
  lessons_learned/     # Project narrative & lessons
knowledge-base/        # Source docs & pragmatic rules
  source-docs/         # Census methodology PDFs (gitignored)
  rules/               # Extracted pragmatic rules
  methodology/         # Processed methodology content
src/                   # MCP server source code
tests/                 # Evaluation harness & unit tests
scripts/               # Build & utility scripts
```

## Acknowledgments

- **U.S. Census Bureau** — for collecting and maintaining vital public data
- **Kyle Walker** — [Analyzing US Census Data](https://walker-data.com/census-r/) textbook as knowledge base source
- **Anthropic** — Model Context Protocol enabling AI tool integration

## Contributing

Contributions welcome, especially:
- Domain expertise from Census data veterans
- Statistical methodology review
- Evaluation test cases (real-world query scenarios)

## License

MIT License - see [LICENSE](LICENSE) file for details.
