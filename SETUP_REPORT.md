# Setup Report

DEST_DIR:
C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\GL-260

SOURCE_ROOT:
C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application

Copied items (source -> dest):
- C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\GL-260 Data Analysis and Plotter V1.5.0.5.py
  -> C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\GL-260\GL-260 Data Analysis and Plotter V1.5.0.5.py
- C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\solubility_models\ (recursive)
  -> C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\GL-260\solubility_models\
- C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\naoh_co2_pitzer_ph_model.py
  -> C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\GL-260\naoh_co2_pitzer_ph_model.py
- C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\pitzer.dat
  -> C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\GL-260\pitzer.dat
- C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\requirements.txt
  -> C:\Users\mmoheban\Local Documents\Python\Code Template Files\Code Master Files\Codex GL-260 Processing Application\GL-260\requirements.txt

Additional pitzer.dat copies:
- None (no solubility_models dependency found; root copy satisfies runtime search in the app).

Validation commands used (from DEST_DIR):
1) python -m venv .venv
2) .\.venv\Scripts\python -m pip install -r requirements.txt
3) .\.venv\Scripts\python "GL-260 Data Analysis and Plotter V1.5.0.5.py"

Validation result:
- python -m venv .venv: PASS
- pip install -r requirements.txt: FAIL (ConnectionResetError WinError 10054 while downloading matplotlib)
- app run: NOT RUN (dependency install failed)
