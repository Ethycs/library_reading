# Library Reading

A Python project for library reading management, configured with [pixi](https://pixi.sh) for dependency and environment management.

## Prerequisites

- [pixi](https://pixi.sh) - A fast, cross-platform package manager
- Python 3.11 or higher (managed by pixi)

### Installing pixi

On Windows (PowerShell):
```powershell
iwr -useb https://pixi.sh/install.ps1 | iex
```

For other platforms, visit [pixi.sh](https://pixi.sh).

## Getting Started

### 1. Install Dependencies

Clone the repository and install all dependencies:

```powershell
pixi install
```

This will:
- Create a virtual environment in `.pixi/`
- Install all dependencies defined in `pyproject.toml`
- Install the `library_reading` package in editable mode

### 2. Run Commands in the pixi Environment

To run any command within the pixi environment:

```powershell
pixi run <command>
```

Or start a shell with the environment activated:

```powershell
pixi shell
```

### 3. Running Python Scripts

Execute Python scripts using the pixi environment:

```powershell
pixi run python your_script.py
```

## Project Structure

```
library_reading/
├── src/
│   └── library_reading/
│       └── __init__.py
├── pyproject.toml          # Project metadata and pixi configuration
├── pixi.lock               # Lock file for reproducible environments
└── README.md
```

## Configuration

The project is configured in `pyproject.toml` with the following pixi settings:

- **Channels**: `conda-forge`
- **Platforms**: `win-64` (Windows 64-bit)
- **Dependencies**: 
  - pandas (>=2.3.3, <3)
- **Python Version**: >=3.11

## Adding Dependencies

### Adding Conda Dependencies

To add a new conda package:

```powershell
pixi add <package-name>
```

Example:
```powershell
pixi add numpy
```

### Adding PyPI Dependencies

To add a PyPI package:

```powershell
pixi add --pypi <package-name>
```

Example:
```powershell
pixi add --pypi requests
```

## Custom Tasks

You can define custom tasks in `pyproject.toml` under `[tool.pixi.tasks]`. Run them with:

```powershell
pixi run <task-name>
```

Example task configuration:
```toml
[tool.pixi.tasks]
test = "pytest tests/"
lint = "ruff check src/"
format = "ruff format src/"
```

## Updating Dependencies

To update all dependencies to their latest compatible versions:

```powershell
pixi update
```

## Cleaning Up

To remove the pixi environment and start fresh:

```powershell
Remove-Item -Recurse -Force .pixi
pixi install
```

## Troubleshooting

### Environment Issues

If you encounter environment issues, try:

1. Clean and reinstall:
   ```powershell
   Remove-Item -Recurse -Force .pixi
   pixi install
   ```

2. Check pixi version:
   ```powershell
   pixi --version
   ```

### Lock File Conflicts

If `pixi.lock` has conflicts after a merge, regenerate it:

```powershell
pixi install --locked=false
```

## More Information

- [pixi Documentation](https://pixi.sh/latest/)
- [pixi GitHub Repository](https://github.com/prefix-dev/pixi)

## License

[Specify your license here]

## Contributing

[Add contribution guidelines here]
