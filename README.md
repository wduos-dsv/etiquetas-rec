# Etiquetas EXP

## Build
Step 1: Install PyInstaller

```bash
pip install pyinstaller
```

Step 2: Build the .exe File

```bash
PyInstaller --onefile --noconsole script.py
```

### Adding an Icon
```bash
PyInstaller --onefile --windowed script.py
```