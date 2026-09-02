# Engineering Persona: file guide

This repository ships the engineering persona as a set of small, ready-to-load files instead of one large document. Pick two things per project: **one core file** for the agent's model class, and **one language file per language in play**. Load both. Nothing else in this tree is meant to be loaded by an agent directly.

```
ENGINEERING_PERSONA.haiku.md   \
ENGINEERING_PERSONA.sonnet.md   \
ENGINEERING_PERSONA.opus.md      >  pick exactly one, matching the agent's model class
ENGINEERING_PERSONA.fable.md   /

ENGINEERING_PERSONA_LANGUAGES/
  ai-prompting.haiku.md   ai-prompting.sonnet.md   ai-prompting.opus.md   ai-prompting.fable.md
  arm-x86-asm.haiku.md    arm-x86-asm.sonnet.md    arm-x86-asm.opus.md    arm-x86-asm.fable.md
  wasm.haiku.md           wasm.sonnet.md           wasm.opus.md           wasm.fable.md
  c-cpp.haiku.md          c-cpp.sonnet.md          c-cpp.opus.md          c-cpp.fable.md
  rust.haiku.md           rust.sonnet.md           rust.opus.md           rust.fable.md
  go.haiku.md             go.sonnet.md             go.opus.md             go.fable.md
  python.haiku.md         python.sonnet.md         python.opus.md         python.fable.md
  node-ts-js.haiku.md     node-ts-js.sonnet.md     node-ts-js.opus.md     node-ts-js.fable.md
  html-css.haiku.md       html-css.sonnet.md       html-css.opus.md       html-css.fable.md
  java.haiku.md           java.sonnet.md           java.opus.md           java.fable.md
  kotlin.haiku.md         kotlin.sonnet.md         kotlin.opus.md         kotlin.fable.md
  flutter-dart.haiku.md   flutter-dart.sonnet.md   flutter-dart.opus.md   flutter-dart.fable.md
  powershell.haiku.md     powershell.sonnet.md     powershell.opus.md     powershell.fable.md
  bash.haiku.md           bash.sonnet.md           bash.opus.md           bash.fable.md
                                    ^
                    pick the file matching the language AND
                    the same class as the core file above,
                    one per language in play on the project
```

Opus and Fable are separate files at both levels. Their body content is currently identical: nothing in this persona is marked fable-exclusive yet (see "How this is built" below for why they are still shipped as separate files rather than one shared file).

## How to pick, per project

1. **Look up the agent's model class** (set in your harness or agent config, e.g. `agent.model_class` in `CLAUDE.md` or `AGENTS.md`). Map any other provider's model to the nearest of Haiku, Sonnet, Opus, or Fable by capability, not by name.
2. **Load the matching core file:**
   - Haiku class -> `ENGINEERING_PERSONA.haiku.md`
   - Sonnet class -> `ENGINEERING_PERSONA.sonnet.md`
   - Opus class -> `ENGINEERING_PERSONA.opus.md`
   - Fable class -> `ENGINEERING_PERSONA.fable.md`
3. **Load one language file per language the project actually uses**, in the same class as step 2. A project mixing Python and Bash, run by a Sonnet-class agent, loads `ENGINEERING_PERSONA.sonnet.md` plus `ENGINEERING_PERSONA_LANGUAGES/python.sonnet.md` plus `ENGINEERING_PERSONA_LANGUAGES/bash.sonnet.md`, and nothing else.
4. **Point your agent entry file at both.** For example, the first line of `CLAUDE.md` or `AGENTS.md`:
   ```
   Load ENGINEERING_PERSONA.sonnet.md and ENGINEERING_PERSONA_LANGUAGES/python.sonnet.md before writing any code.
   ```
5. **Mixed-class projects** (a Haiku-class agent applying diffs that a Sonnet-class agent designed) each load their own class's files. The standard is identical across classes; only depth and escalation posture differ (core file, section 3).

## Example selections

| Project | Agent class | Files to load |
|---|---|---|
| A Sonnet-class agent building a Rust CLI | Sonnet | `ENGINEERING_PERSONA.sonnet.md`, `ENGINEERING_PERSONA_LANGUAGES/rust.sonnet.md` |
| A Haiku-class agent applying reviewed diffs to a Node/TypeScript service | Haiku | `ENGINEERING_PERSONA.haiku.md`, `ENGINEERING_PERSONA_LANGUAGES/node-ts-js.haiku.md` |
| An Opus-class agent architecting a Python and Bash data pipeline | Opus | `ENGINEERING_PERSONA.opus.md`, `ENGINEERING_PERSONA_LANGUAGES/python.opus.md`, `ENGINEERING_PERSONA_LANGUAGES/bash.opus.md` |
| A Fable-class agent designing a WASM module with a Rust host and hand-tuned ARM inner loop | Fable | `ENGINEERING_PERSONA.fable.md`, `ENGINEERING_PERSONA_LANGUAGES/wasm.fable.md`, `ENGINEERING_PERSONA_LANGUAGES/rust.fable.md`, `ENGINEERING_PERSONA_LANGUAGES/arm-x86-asm.fable.md` |

## Measured sizes

See `dist/BUILD_REPORT.txt` (or the copy at the repository root) for the exact word and estimated-token count of every generated file, refreshed on every build. As generated:

| Core file | Words | ~Tokens |
|---|---|---|
| `ENGINEERING_PERSONA.haiku.md` | ~5,900 | ~7,670 |
| `ENGINEERING_PERSONA.sonnet.md` | ~8,200 | ~10,670 |
| `ENGINEERING_PERSONA.opus.md` | ~8,600 | ~11,180 |
| `ENGINEERING_PERSONA.fable.md` | ~8,600 | ~11,180 |

Each language file adds roughly 120 to 400 words (~150 to ~510 tokens) depending on class and language. Token counts are a rough estimate (words times 1.3) for planning only; get the real count from your provider's tokeniser or usage report before treating it as a cost figure, per section 7.3 of the persona itself.

## How this is built

Nothing under `ENGINEERING_PERSONA*` is hand-edited. All 60 files (4 core, 56 language) are generated by `build_persona.py` from two annotated source files:

- `source/core.source.md`: Parts A to C of the persona, with every section and subsection heading tagged `` `[all]` ``, `` `[sonnet+]` ``, or `` `[opus+]` `` to mark the minimum class that loads it. `all` ships to every class; `sonnet+` ships to Sonnet, Opus and Fable; `opus+` ships to Opus and Fable. A subsection can override its parent section's tag (see section 8.2 in the source, which is tagged `sonnet+` inside a section otherwise tagged `opus+`, because Sonnet gets that one checklist without the surrounding innovation latitude).
- `source/languages.source.md`: one block per language, each broken into labelled subsections (`**For.**`, `**Checklist.**`, `**Illegal states.**`, `**Errors.**`, `**Tooling.**`, `**Hazard.**`, `**Judgment.**`). The build assembles `haiku` from For + Checklist + Hazard, `sonnet` from For + Illegal states + Errors + Tooling + Hazard, and `opus`/`fable` from the sonnet set plus Judgment.

**Why Opus and Fable are separate files with identical content.** No line in either source file is currently tagged as fable-exclusive, so the two editions render the same body text; only the header and the cross-reference to the paired core file differ. They are still shipped as separate files, not one shared file with two names, for three reasons: a harness looks up a file by the agent's own class name rather than needing to know it shares an edition with another class; the two classes are described with distinct responsibilities in section 3.1 (Fable additionally decides tiering and reviews Opus-class output), so the day genuinely fable-only material is written, it has a home without a rename; and it avoids the file-naming inconsistency of a core document split four ways while the language directory was split three ways, which is what this repository shipped before this file set existed. If you want them to diverge, add a `fable+` tier above `opus+` in `TAG_RANK` and `CLASS_CEILING` in `build_persona.py`, tag the new material `fable+` in the source files, and rerun the build; nothing else changes.

To change anything, edit the relevant source file and rerun:

```bash
python3 build_persona.py
```

This regenerates every file under `dist/` (the four core files, the 56 language files, and `BUILD_REPORT.txt`) from the two source files. It takes no arguments for normal use; `--dist DIR` and `--source-dir DIR` are available if you relocate either. The script has no dependencies beyond the Python 3 standard library.

**To add a language:** append a new block to `languages.source.md` following the existing pattern (`## SLUG: <slug>`, `## TITLE: <name>`, then the labelled subsections), and rerun the build. The slug becomes the filename prefix under `ENGINEERING_PERSONA_LANGUAGES/`.

**To change what a class loads from the core document:** move a section's tag up or down in `core.source.md` and rerun the build. Moving a tag is a decision with real consequences (it changes what every agent of that class sees on every task), so treat it like the reversible-versus-irreversible calls in persona section 4.2: cheap to try, and worth a second look before it ships broadly.

Do not hand-edit anything under `dist/`. The next build overwrites it, and a hand edit made there is a hand edit that silently disappears.
