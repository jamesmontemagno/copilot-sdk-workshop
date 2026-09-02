#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

target="${1:-all}"
temporary_directory="$(mktemp -d)"
python_command=()

cleanup() {
    rm -rf "$temporary_directory"
}

trap cleanup EXIT

configure_python() {
    if python3 -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >/dev/null 2>&1; then
        python_command=(python3)
    elif python -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >/dev/null 2>&1; then
        python_command=(python)
    elif py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >/dev/null 2>&1; then
        python_command=(py -3)
    else
        echo "Python 3.11 or newer is required." >&2
        return 1
    fi
}

run_system_python() {
    if [[ ${#python_command[@]} -eq 0 ]]; then
        configure_python
    fi
    "${python_command[@]}" "$@"
}

validate_content() {
    run_system_python scripts/validate_workshop.py
    node docs/tests/markdown-language-preprocessor.test.js
}

validate_dotnet() {
    projects=()
    while IFS= read -r project; do
        projects+=("$project")
    done < <(find start-accessibility/dotnet start-museum/dotnet finished/dotnet -name '*.csproj' -print | sort)
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
    for project in start-accessibility/nodejs start-museum/nodejs finished/nodejs/*; do
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
    run_system_python -m venv "$python_venv"
    if [[ -x "$python_venv/bin/python" ]]; then
        venv_python="$python_venv/bin/python"
    else
        venv_python="$python_venv/Scripts/python.exe"
    fi

    for project in start-accessibility/python start-museum/python finished/python/*; do
        echo "Installing and smoke-checking $project"
        (
            cd "$project"
            "$venv_python" -m pip install --disable-pip-version-check --no-input --requirement requirements.txt
            "$venv_python" -m py_compile *.py
            "$venv_python" -c "import importlib, pathlib; [importlib.import_module(path.stem) for path in pathlib.Path('.').glob('*.py')]; from copilot import CopilotClient"
            if [[ -d tests ]]; then
                "$venv_python" -m unittest discover -s tests
            fi
        )
    done
}

validate_go() {
    go_build_directory="$temporary_directory/go-build"
    mkdir -p "$go_build_directory"

    for project in start-accessibility/go start-museum/go finished/go/*; do
        echo "Resolving and building $project"
        (cd "$project" && go mod download && go mod verify && go build -mod=readonly -o "$go_build_directory/" ./...)
        if [[ "$project" != "start-museum/go" && "$project" != "finished/go/museum-exhibit-studio" ]]; then
            (cd "$project" && go test -mod=readonly ./...)
        fi
    done
}

validate_rust() {
    export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$repo_root/.cargo-target}"
    for project in start-accessibility/rust start-museum/rust finished/rust/*; do
        echo "Checking $project"
        (cd "$project" && cargo check --locked)
        if [[ "$project" != "start-museum/rust" && "$project" != "finished/rust/museum-exhibit-studio" ]]; then
            (cd "$project" && cargo test --locked)
        fi
    done
}

validate_java() {
    for project in start-accessibility/java start-museum/java finished/java/*; do
        echo "Resolving and compiling $project"
        (cd "$project" && mvn --batch-mode --no-transfer-progress dependency:go-offline compile)
        if [[ "$project" == "start-museum/java" || "$project" == "finished/java/museum-exhibit-studio" ]]; then
            (cd "$project" && mvn --batch-mode --no-transfer-progress --offline compile)
        else
            (cd "$project" && mvn --batch-mode --no-transfer-progress --offline test)
        fi
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
