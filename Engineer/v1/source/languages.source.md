Language profiles. Load only the profile for the language in play, in the edition matching your model class (`<slug>.haiku.md`, `<slug>.sonnet.md`, `<slug>.opus.md`, `<slug>.fable.md` under `ENGINEERING_PERSONA_LANGUAGES/`). Each profile answers what the language is for in this repository, how it makes illegal states unrepresentable, how it handles errors, what tooling is mandatory, and the one hazard that most often bites people who are fluent in it. The Haiku edition is a checklist: concrete, imperative, no discussion. The Sonnet edition is the full working profile. The Opus and Fable editions add a Judgment note: when to depart from the default, and the deeper mechanism behind the hazard. Opus and Fable currently render identical content; each gets its own file so a harness can load by its own class name.

Assembly rule for the build script, per language section below:
- `<slug>.haiku.md` = For + Checklist + Hazard
- `<slug>.sonnet.md` = For + Illegal states + Errors + Tooling + Hazard
- `<slug>.opus.md` = `<slug>.fable.md` = For + Illegal states + Structure (if present) + Errors + Tooling + Hazard + Judgment

---

## SLUG: ai-prompting
## TITLE: AI prompting

**For.** Anything only a model can do: judgement over unstructured text, synthesis, generation, classification where no deterministic rule exists. Not for anything a parser, a regex or a lookup answers.

**Checklist.**
- Use a model only when a parser, regex or lookup cannot answer the question.
- Force output through a schema or tool call; never parse free text.
- Order the prompt: identity and standards, then tools, then reference material, then the task, then the most recent state.
- One job per prompt; split anything that does two things.
- Pin the model identifier in config, never in the prompt body.
- Run the regression suite (fixed inputs, evaluated outputs, cost, latency) before shipping any prompt change.

**Illegal states.** Schema-forced output (a tool call or a structured-output mode) rather than free text that is parsed afterwards. Enumerated answers where the answer space is finite. A single prompt has a single job; a prompt that does two things is two prompts.

**Structure.** Ordered by change frequency for cache stability: identity and standards, then tool definitions, then reference material, then the task, then the most recent state. Instructions are positive (what to do) rather than negative (what to avoid) where the two are equivalent. Examples only where an evaluation shows they help, because each example is a recurring token cost. Prompts for smaller classes are shorter, more concrete and more imperative; prompts for larger classes state the goal and the constraints and leave the method open.

**Errors.** A model's error is a wrong output, and it is caught by validation at the boundary, never by trusting the text. Every model output is untrusted input.

**Tooling.** Prompts live in files with a hash recorded in the run manifest. Every prompt has a regression suite of fixed inputs with evaluated outputs, cost and latency lines, run on every prompt change and every model version change. Model identifiers are pinned in config and never appear in the prompt body. Proprietary syntax stays inside the provider adapter.

**Hazard.** Behaviour drifts silently on model updates. A prompt that passed last quarter is a hypothesis this quarter. Re-run the evaluation on any model or version change, and treat a version bump as a code change.

**Judgment.** Treat every model version bump as a code change: re-run the evaluation before trusting the prompt again, because a passing prompt is a hypothesis, not a fact, and behaviour drifts silently across versions. When designing the regression suite itself, choose the fixed inputs to cover the adversarial cases from the five gates, not only the happy path, because a suite that never fails has never been checked.

---

## SLUG: arm-x86-asm
## TITLE: ARM and x86-64 assembly

**For.** Only where a measurement shows the compiler cannot get there: SIMD inner loops, boot and reset paths, interrupt handlers, constant-time cryptographic primitives, hand-tuned memory routines. Intrinsics are tried first and the assembly must beat them in the profile.

**Checklist.**
- Try intrinsics first; write assembly only when a profile shows the compiler cannot get there.
- Document calling convention, clobbered registers, and stack alignment at the top of every routine.
- Write a C or Rust reference implementation and property-test the assembly against it.
- Cross-assemble and test in CI for every target ISA.
- Check constant-time routines with a timing test, not by inspection.

**Illegal states.** A documented contract at the top of every routine: calling convention (System V, Windows x64, AAPCS64), input and output registers, clobbered registers, stack alignment on entry and at each call, and preserved flags. A C or Rust reference implementation exists for every routine and property tests compare the two across the input space.

**Errors.** Assembly does not have them; it has undefined behaviour and faults. Every routine states its preconditions and the reference implementation's tests enforce them. Static assertions on structure offsets and sizes at assembly time.

**Tooling.** One syntax per repository (Intel or AT&T), chosen once and enforced. Cross-assembly and test in CI for every target ISA. Disassembly of the compiled reference is read before the hand-written version is started, because the compiler's version is often the state of the art. Constant-time routines are checked with a timing test, not by inspection.

**Hazard.** ABI differences that compile clean and corrupt silently: the 128-byte red zone below the stack pointer on System V that does not exist on Windows x64; 16-byte stack alignment at call sites; ARM's weak memory ordering, which requires explicit barriers where x86 needs none; and endianness assumptions in anything that touches the wire.

**Judgment.** The ABI is the most common silent killer here: the System V red zone, Windows x64's shadow space, ARM's weak memory ordering. Before hand-tuning, read the compiler's own disassembly of the reference implementation, because it is frequently already the state of the art, and the improvement you are chasing may not exist.

---

## SLUG: wasm
## TITLE: WebAssembly

**For.** Portable compute in the browser or under WASI where a native binary cannot go. Compiled from Rust or C++; never hand-written unless a byte budget demands it.

**Checklist.**
- Compile from Rust or C++; hand-write only under a byte budget.
- Write the boundary contract: who owns linear memory, who frees what.
- List every import and export in a manifest checked in CI.
- Run `wasm-opt` in the build and assert a size budget in CI.
- Test in at least two engines (a browser engine and a standalone runtime).

**Illegal states.** An explicit boundary contract: who owns linear memory, how strings and structures cross it, and which side frees what. Imports and exports are listed in a manifest checked in CI. Types crossing the boundary are the primitive types the platform supports, with everything else marshalled explicitly.

**Errors.** A trap is unrecoverable from inside the module. Anything that can fail returns a status code across the boundary and the host decides. Out-of-bounds access is a trap, and a trap is a defect.

**Tooling.** `wasm-opt` in the build. A size budget in bytes asserted in CI. Tests run in at least two engines (a browser engine and a standalone runtime such as `wasmtime`) because engine behaviour differs at the edges. Streaming instantiation in the browser.

**Hazard.** The 32-bit address space, the absence of threads without shared-memory flags and cross-origin isolation, and the temptation to assume that floating-point results are bit-identical across engines beyond what IEEE 754 guarantees.

**Judgment.** Do not assume floating-point bit-identity across engines beyond what IEEE 754 guarantees, and do not assume threads are available without shared-memory flags and cross-origin isolation; both assumptions pass locally and fail in exactly the environment you did not test.

---

## SLUG: c-cpp
## TITLE: C and C++

**For.** Systems code, embedded targets, performance-critical paths, and interoperation with existing native libraries. C17 and C++20 as the floors.

**Checklist.**
- C17 or C++20 floor. RAII for every resource; no raw `new` or `delete`.
- `enum class`, `std::optional`, `std::variant` over unions and sentinel values.
- `-Wall -Wextra -Werror -Wconversion -Wshadow`, zero warnings.
- Run ASan, UBSan and TSan in CI on every change.
- Fuzz every parser with libFuzzer.

**Illegal states.** `enum class`, strong typedefs, `std::variant` with `std::visit`, `std::optional`, and constructors that refuse invalid arguments. RAII for every resource; no owning raw pointers; no raw `new` or `delete`. In C, opaque struct pointers and validated constructor functions.

**Errors.** `std::expected` or an equivalent result type at library boundaries. Exceptions either disabled or confined to a documented layer. Every error path tested. No reliance on undefined behaviour, ever, including signed overflow, strict-aliasing violations and uninitialised reads.

**Tooling.** `-Wall -Wextra -Werror -Wconversion -Wshadow` as the floor. AddressSanitizer, UndefinedBehaviorSanitizer and ThreadSanitizer in CI. `clang-tidy` and `clang-format` enforced. Fuzzing of every parser with libFuzzer. A pinned compiler version and CMake presets so the build is reproducible.

**Hazard.** The code that works on your machine because the undefined behaviour happened to do what you wanted. Static initialisation order across translation units. The One Definition Rule violated by a header that changed.

**Judgment.** Undefined behaviour that "happens to work" on your machine is not a passing test, it is an untriggered one. Treat any reliance on unspecified behaviour (signed overflow, aliasing, initialisation order across translation units) as a defect regardless of whether the current compiler tolerates it.

---

## SLUG: rust
## TITLE: Rust

**For.** Anything that needs native performance and memory safety at once: services, CLIs, WASM modules, embedded targets, FFI wrappers.

**Checklist.**
- `Result<T, E>` everywhere; no `unwrap` or `expect` outside tests.
- `#![forbid(unsafe_code)]` by default; unsafe isolated to one module with a `// SAFETY:` comment per block.
- Run `clippy` at pedantic, `miri` over unsafe code, `cargo-audit` and `cargo-deny` in CI.
- Newtypes for units and identifiers; exhaustive `match` on enums.

**Illegal states.** Newtypes for every unit and identifier. Enums with payloads and exhaustive `match`. Builder patterns that cannot produce a half-built value. `#![forbid(unsafe_code)]` at the crate root by default; where unsafe is needed, it lives in one module, each block carries a `// SAFETY:` comment stating the invariant, and Miri runs over it in CI.

**Errors.** `Result<T, E>` everywhere. `thiserror` in libraries, `anyhow` in binaries. No `unwrap` or `expect` outside tests and provably infallible cases, and the provably infallible case says why in a comment.

**Tooling.** `rust-toolchain.toml` pins the version. `clippy` at pedantic with each allow documented. `rustfmt`. `proptest` and `cargo-fuzz` for unbounded inputs. `cargo-deny` for licence and advisory checks. `cargo-audit` in CI.

**Hazard.** Blocking inside an async task. Async runtime lock-in that makes a library unusable elsewhere. `Send` and `Sync` assumptions at an FFI boundary that the other side does not honour.

**Judgment.** An async runtime choice made for convenience becomes a lock-in that limits who can consume the library. Where a crate is a leaf dependency for others, keep the async runtime out of its public API, or accept that you have chosen the runtime for everyone downstream.

---

## SLUG: go
## TITLE: Go

**For.** Network services, CLIs, tooling, anything where a static binary, fast builds and a simple concurrency model matter more than peak performance.

**Checklist.**
- Check every error return; wrap with `%w`.
- Define interfaces at the consumer, not the producer.
- `context.Context` first parameter on anything doing I/O; honour cancellation.
- Run `go vet`, `staticcheck`, and `go test -race` in CI.
- Give every goroutine an owner responsible for its termination.

**Illegal states.** Small interfaces defined by the consumer. Closed sets sealed with an unexported method. Constructors that validate and return an error. No zero-value-is-valid assumptions on types that need setup.

**Errors.** Errors are values, checked at every call, wrapped with `%w` so the chain is inspectable with `errors.Is` and `errors.As`. A `context.Context` is the first parameter of anything that does I/O or may be cancelled, and cancellation is honoured.

**Tooling.** `gofmt`, `go vet`, `staticcheck`, `golangci-lint`. Table-driven tests. `go test -race` in CI. The built-in fuzzer for parsers. No `init()` side effects. Every goroutine has an owner responsible for its termination.

**Hazard.** A nil pointer wrapped in a non-nil interface. An ignored error return. Unbounded goroutine creation under load. Package-level mutable state.

**Judgment.** A nil pointer stored in a non-nil interface value is the classic trap that a type-level fix in another language would prevent outright; treat every function returning an interface as a place to check `== nil` explicitly, not assume the zero value is safe.

---

## SLUG: python
## TITLE: Python

**For.** Data work, evaluation harnesses, machine-learning pipelines, glue, scripts that will grow. Python 3.12 as the floor.

**Checklist.**
- `pyproject.toml` and a lockfile; no bare `except`.
- Frozen dataclasses, `Enum`, `Literal`; Pydantic or equivalent at every ingress boundary.
- `mypy --strict` or `pyright` strict, `ruff`, in CI.
- `logging`, never `print`, outside throwaway scripts.
- `pathlib` for paths; no mutable default arguments.

**Illegal states.** Frozen dataclasses. `Enum`, `Literal` and `NewType`. Pydantic or equivalent at every ingress boundary and nowhere in the interior. Exhaustiveness checked with `assert_never`.

**Errors.** A custom exception hierarchy rooted in one base per package. Exceptions carry context and are chained with `from`. No bare `except`. No exceptions for control flow.

**Tooling.** `pyproject.toml` only. A lockfile (`uv` or equivalent). `ruff` for format and lint. `mypy --strict` or `pyright` in strict mode. `pytest` with `hypothesis` for property tests. `logging`, never `print`, in anything that is not a throwaway. `pathlib` for paths. `asyncio.TaskGroup` for structured concurrency.

**Hazard.** CPU-bound work behind the GIL. Mutable default arguments. Import-time side effects. Implicit coercion between `int`, `float` and `bool`.

**Judgment.** CPU-bound work behind the GIL will not parallelise no matter how the code is restructured; if a profile shows CPU-bound contention, the fix is a process pool, a native extension, or a different language, not a cleverer asyncio pattern.

---

## SLUG: node-ts-js
## TITLE: Node.js, TypeScript and JavaScript

**For.** The CLI, the agent runtime, the web build, anything that must run in both browser and server.

**Checklist.**
- TypeScript strict, `noUncheckedIndexedAccess`, ESM only; `no-explicit-any` as an error.
- `zod` or equivalent at every ingress boundary.
- No default exports; no floating promises.
- Thread `AbortSignal` through anything that awaits.
- Run `eslint` with an import-boundaries rule and `vitest` in CI.

**Illegal states.** TypeScript 5.x, strict, `NodeNext`, `noUncheckedIndexedAccess`, ESM only, Node 22 LTS. `no-explicit-any` is an error; the only permitted boundary is the vendor SDK edge, narrowed within one file. Discriminated unions and exhaustive `switch`. `zod` or equivalent at every ingress. No default exports, so renames are greppable. Plain JavaScript only where TypeScript cannot run (an inline page script), and then typed with JSDoc and checked with `checkJs`.

**Errors.** Result types at agent-facing boundaries, exceptions internally. No floating promises. `AbortSignal` threaded through anything that awaits.

**Tooling.** `eslint` with an import-boundaries rule. `vitest`. Dependencies pinned and audited; each new dependency justified. Interfaces in `src/types/`, which imports nothing.

**Hazard.** Blocking the event loop with synchronous work. Unhandled promise rejections. Dependency sprawl.

**Judgment.** An unhandled promise rejection or a synchronous block on the event loop degrades every concurrent request, not just the one that triggered it; when latency is inconsistent under load, check the event loop before the network.

---

## SLUG: html-css
## TITLE: HTML and CSS

**For.** Every page a person reads. HTML is the content and structure; CSS is the presentation; JavaScript is an enhancement.

**Checklist.**
- Semantic elements; every form control labelled; every image has alt text or is marked decorative.
- Insert dynamic content with `textContent` or an escaping template, never `innerHTML` concatenation.
- Set a Content Security Policy; no inline scripts outside the build bundle.
- Run a validator and a WCAG 2.2 AA checker in CI.
- Honour `prefers-reduced-motion` and `prefers-color-scheme`.

**Illegal states.** Semantic elements over generic ones. Every form control has a label. Every image has alternative text or is explicitly decorative. `lang` and viewport are set. Content is readable and navigable with JavaScript disabled.

**Errors.** Dynamic content is inserted with `textContent` or a templating layer that escapes; never by string concatenation into `innerHTML`. A Content Security Policy is set and inline scripts and styles are absent except for a single build-generated bundle.

**Tooling.** A validator and an accessibility checker (WCAG 2.2 AA) in CI. A performance budget for largest contentful paint and layout shift. `prefers-reduced-motion` and `prefers-color-scheme` honoured.

**Hazard.** DOM-based cross-site scripting from one unescaped interpolation, and layout that assumes a viewport width.

**Judgment.** A single unescaped interpolation into the DOM is a cross-site-scripting hole regardless of how trusted the data source looked at design time; treat every value that reaches the DOM as user input, including values that originated from your own database.

---

## SLUG: java
## TITLE: Java

**For.** JVM services and libraries, Android where Kotlin is not in use, and interoperation with existing enterprise systems. The current LTS as the floor.

**Checklist.**
- `record` types and sealed interfaces with exhaustive `switch`.
- `Optional` as a return type only, never a field or parameter.
- No `catch (Exception e)` without a re-throw.
- Run Error Prone and SpotBugs in CI.
- Use virtual threads for I/O-bound concurrency.

**Illegal states.** `record` types, sealed interfaces, pattern matching in `switch` with exhaustiveness. Immutable collections by default. `Optional` only as a return type, never as a field or parameter.

**Errors.** Checked exceptions for recoverable conditions the caller must decide on; unchecked for programming errors. Context added at every re-throw. No `catch (Exception e)` without a re-throw.

**Tooling.** Gradle with the Kotlin DSL or Maven, reproducible builds, a pinned toolchain. Error Prone and SpotBugs in CI. JUnit 5, AssertJ, jqwik for properties. Virtual threads for I/O-bound concurrency.

**Hazard.** `null` where the type system said nothing. `equals` and `hashCode` contracts broken by a partial override. Reflection quietly bypassing a sealed hierarchy.

**Judgment.** A partial override of `equals` without `hashCode` (or the reverse) breaks silently in a `HashMap` and shows up as a rare, unreproducible lookup failure; audit both together whenever either changes, and prefer records, which give you both for free.

---

## SLUG: kotlin
## TITLE: Kotlin

**For.** Android, JVM services where expressiveness and null safety pay, and multiplatform shared logic.

**Checklist.**
- Sealed classes with exhaustive `when`; nullability in the type, not a comment.
- `Result` or `Either` at boundaries; exceptions internally.
- Never `GlobalScope`; give every coroutine a scoped, lifetime-owned launcher.
- Run `ktlint` and `detekt` in CI.
- Avoid `!!` as a habit; handle the null case explicitly.

**Illegal states.** Sealed classes and interfaces with exhaustive `when`. Data classes for values, value classes for units and identifiers. Nullability in the type, never in a comment.

**Errors.** `Result` or an `Either` type at boundaries; exceptions internally. Coroutines use structured concurrency: a scope with a lifetime owner, never `GlobalScope`, and `SupervisorJob` chosen deliberately when child failure must be isolated.

**Tooling.** `ktlint` and `detekt`. Explicit API mode for any published library. Kotest or JUnit 5. The same toolchain pinning as Java.

**Hazard.** Platform types arriving from Java interop with nullability unknown. `!!` as a habit. An exception inside a coroutine cancelling siblings the author did not expect.

**Judgment.** A platform type arriving from Java interop carries no compile-time nullability information; treat every Java interop boundary as a validation boundary, and do not let the compiler's silence be mistaken for a guarantee.

---

## SLUG: flutter-dart
## TITLE: Flutter and Dart

**For.** Cross-platform applications with one codebase where native fidelity is not the deciding constraint. Stable channel, version pinned.

**Checklist.**
- Sound null safety; sealed classes with exhaustive `switch`.
- One state-management approach per app, documented, not mixed.
- Keep business logic out of widgets; unit-test it without a widget tree.
- Run widget tests for behaviour and golden tests for appearance.
- Validate every platform-channel message on arrival.

**Illegal states.** Sound null safety. Sealed classes with exhaustive `switch`. Immutable state objects. One state-management approach per application, chosen and documented in the architecture notes, not mixed.

**Errors.** Failures are values in the state, rendered by the widget tree. Exceptions cross no widget boundary. Platform channels are typed at both ends and every message is validated on arrival.

**Tooling.** `flutter analyze` with strict lints. Business logic lives outside widgets and is unit-tested without a widget tree. Widget tests for behaviour, golden tests for appearance, integration tests on a device matrix. Accessibility semantics on every interactive element.

**Hazard.** Rebuild storms from state held too high in the tree. A `BuildContext` used after an `await`. Platform-specific behaviour that was only ever tested on one platform.

**Judgment.** State held higher in the widget tree than it needs to be causes rebuild storms that look like a performance bug but are an architecture bug; when a screen feels slow, check where the state lives before profiling the render.

---

## SLUG: powershell
## TITLE: PowerShell

**For.** Windows automation, deployment and operations tooling. PowerShell 7 (Core) unless the target mandates Windows PowerShell 5.1, and the mandate is written down.

**Checklist.**
- `Set-StrictMode -Version Latest` and `$ErrorActionPreference = 'Stop'` at the top of every script.
- `[CmdletBinding()]`, typed and validated parameters.
- Functions emit objects, never formatted strings.
- `SupportsShouldProcess` on every state-changing function, so `-WhatIf` works.
- Run PSScriptAnalyzer and Pester in CI.

**Illegal states.** `Set-StrictMode -Version Latest` and `$ErrorActionPreference = 'Stop'` at the top of every script. Advanced functions with `[CmdletBinding()]`, typed parameters, `[ValidateSet()]` and `[ValidateNotNullOrEmpty()]`. Functions emit objects, never formatted strings.

**Errors.** Terminating errors with `throw` or `Write-Error -ErrorAction Stop`. `try` and `catch` with the exception type named. `SupportsShouldProcess` on any function that changes state, so `-WhatIf` works.

**Tooling.** PSScriptAnalyzer in CI. Pester tests. Approved verbs only. No aliases in scripts. No `Invoke-Expression`. Output file encoding stated explicitly (`-Encoding utf8`).

**Hazard.** Non-terminating errors that continue silently unless `$ErrorActionPreference` is set. `$null` on the right of a comparison, which does not do what the reader expects with arrays. Execution policy differences between machines.

**Judgment.** A non-terminating error continues the script silently unless `$ErrorActionPreference` is set explicitly for that scope; do not assume a script-level setting propagates into every function or module the same way.

---

## SLUG: bash
## TITLE: Bash

**For.** Glue, build steps, CI, small operational tasks on Unix-like systems. Anything past a hundred lines or with non-trivial logic is rewritten in Python or Go.

**Checklist.**
- `set -euo pipefail` and a quoted `IFS` at the top of every script.
- Quote every expansion; use `[[ ]]`, arrays, and `local` inside functions.
- `trap` for cleanup on `EXIT` and signals; `mktemp` for temp paths.
- Run `shellcheck` and `shfmt` in CI.
- Rewrite in Python or Go past roughly a hundred lines.

**Illegal states.** `#!/usr/bin/env bash`, `set -euo pipefail`, and `IFS=$'\n\t'` at the top. Every expansion quoted. `[[ ]]` rather than `[ ]`. Arrays for lists. Every variable inside a function declared `local`.

**Errors.** `trap` for cleanup on `EXIT` and on signals. `mktemp` for every temporary path. An explicit exit code and a message to stderr on every failure path.

**Tooling.** `shellcheck` and `shfmt` in CI. `bats` for tests. `printf` rather than `echo` for anything that is data. No parsing of `ls` output. POSIX `sh` only when Bash is unavailable, and the script says so in its header.

**Hazard.** `set -e` does not fire inside a command substitution, a pipeline without `pipefail`, or a command used as a condition. Word splitting on an unquoted expansion. A `cd` that failed while the script kept going.

**Judgment.** `set -e` does not fire inside a command substitution, a pipeline without `pipefail`, or when the command is used as a condition; audit those three cases by hand, because the safety net you think you have does not cover them.
