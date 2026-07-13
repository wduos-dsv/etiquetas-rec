# Etiquetas REC

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
PyInstaller --onefile --noconsole --icon=my_logo.ico script.py
```