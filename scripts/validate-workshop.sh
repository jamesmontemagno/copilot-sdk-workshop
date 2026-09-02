#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

target="${1:-all}"
temporary_directory="$(mktemp -d)"

cleanup() {
    rm -rf "$temporary_directory"
}

trap cleanup EXIT

validate_content() {
    python3 scripts/validate_workshop.py
    node docs/tests/markdown-language-preprocessor.test.js
}

validate_dotnet() {
    projects=()
    while IFS= read -r project; do
        projects+=("$project")
    done < <(find start-accessibility/dotnet finished/dotnet -name '*.csproj' -print | sort)
    projects+=("src/BlazorApp/BlazorApp.csproj")
    for project in "${projects[@]}"; do
        echo "Restoring and building $project"
        dotnet restore "$project" --nologo --verbosity quiet
        dotnet build "$project" --no-restore --nologo --verbosity quiet
        if [[ "$project" == *.Tests.csproj ]]; then
            dotnet test "$project" --no-build --nologo --verbosity quiet
        fi
    done
}

validate_nodejs() {
    for project in start-accessibility/nodejs finished/nodejs/*; do
        echo "Installing and type-checking $project"
        (
            cd "$project"
            npm ci --ignore-scripts --no-audit --fund=false
            npm run build
            npm test --if-present
        )
    done
}

validate_python() {
    python_venv="$temporary_directory/python-venv"
    python3 -m venv "$python_venv"

    for project in start-accessibility/python finished/python/*; do
        echo "Installing and smoke-checking $project"
        (
            cd "$project"
            "$python_venv/bin/python" -m pip install --disable-pip-version-check --no-input --requirement requirements.txt
            "$python_venv/bin/python" -m py_compile *.py
            "$python_venv/bin/python" -c "import importlib, pathlib; [importlib.import_module(path.stem) for path in pathlib.Path('.').glob('*.py')]; from copilot import CopilotClient"
            if [[ -d tests ]]; then
                "$python_venv/bin/python" -m unittest discover -s tests
            fi
        )
    done
}

validate_go() {
    go_build_directory="$temporary_directory/go-build"
    mkdir -p "$go_build_directory"

    for project in start-accessibility/go finished/go/*; do
        echo "Resolving and testing $project"
        (cd "$project" && go mod download && go mod verify && go build -mod=readonly -o "$go_build_directory/" ./... && go test -mod=readonly ./...)
    done
}

validate_rust() {
    export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$repo_root/.cargo-target}"
    for project in start-accessibility/rust finished/rust/*; do
        echo "Checking and testing $project"
        (cd "$project" && cargo check --locked && cargo test --locked)
    done
}

validate_java() {
    for project in start-accessibility/java finished/java/*; do
        echo "Resolving and testing $project"
        (cd "$project" && mvn --batch-mode --no-transfer-progress dependency:go-offline test)
        (cd "$project" && mvn --batch-mode --no-transfer-progress --offline test)
    done
}

case "$target" in
    content)
        validate_content
        ;;
    dotnet|nodejs|python|go|rust|java)
        "validate_${target}"
        ;;
    all)
        validate_content
        validate_dotnet
        validate_nodejs
        validate_python
        validate_go
        validate_rust
        validate_java
        ;;
    *)
        echo "Unknown validation target: $target" >&2
        echo "Expected one of: all, content, dotnet, nodejs, python, go, rust, java" >&2
        exit 2
        ;;
esac
