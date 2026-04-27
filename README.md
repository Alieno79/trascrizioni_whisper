# Whisper Trascriber - Guida Installazione (CREATO CON OPENCODE e MINIMAX 2.5 FREE)

## Prerequisiti

- Python 3.x installato
- Windows 10/11 con PowerShell

## CORE (versione attiva)

- SCRIPT RELEASE : WHISPER.CPP - v1.8.4 - 19/03/2026 - VERSIONE CON SUPPORTO CUDA 12.4 (whisper-cublas-12.4.0-bin-x64.zip)
- MODEL HUGGINFACE : GGML-LARGE-V3

## Installazione dipendenze

1. Apri PowerShell nella cartella dello script
2. Esegui il file batch:

```powershell
.\install.bat
```

3. Riavvia il terminale per rendere effettive le modifiche

---

## Download CORE

Scarica whisper.cpp e il modello:

- [RELEASE](https://github.com/ggml-org/whisper.cpp/releases)
- [MODELLI](https://huggingface.co/ggerganov/whisper.cpp/tree/main)

Posiziona i file in:
- `CORE/Whisper/whisper-server.exe`
- `CORE/Models/ggml-large-v3.bin`

---

## Uso dello script

### Opzioni disponibili

| Parametro | Descrizione |
|----------|------------|
| `-C` | Solo conversione OGG -> MP3 |
| `-MP3` | Solo trascrizione da MP3 |
| `-S` | Avvia solo il server |
| `-CPU` | Usa CPU invece di GPU |

### Comandi pronti

#### Solo conversione OGG -> MP3

```powershell
python converti_e_trascrivi.py -C
```

#### Solo trascrizione da MP3 (con GPU)

```powershell
python converti_e_trascrivi.py -MP3
```

#### Solo trascrizione da MP3 (con CPU)

```powershell
python converti_e_trascrivi.py -MP3 -CPU
```

#### Conversione + trascrizione (con GPU)

```powershell
python converti_e_trascrivi.py
```

#### Conversione + trascrizione (con CPU)

```powershell
python converti_e_trascrivi.py -CPU
```

#### Avvia solo il server (con GPU)

```powershell
python converti_e_trascrivi.py -S
```

#### Avvia solo il server (con CPU)

```powershell
python converti_e_trascrivi.py -S -CPU
```

---

## Struttura cartelle

```
Whisper_Trascriber/
├── INPUTS/
│   ├── OGG/        (file audio originali)
│   └── MP3/        (file convertiti)
├── OUTPUTS/
│   ├── TXT/        (testo plain)
│   ├── SRT/        (formato SRT)
│   ├── VTT/        (formato VTT)
│   └── JSON/       (risposta JSON)
├── CORE/
│   ├── Whisper/    (whisper-server.exe)
│   └── Models/    (modelli)
├── converti_e_trascrivi.py
├── install.py
└── install.bat
```

---

## Variabili configurabili

Modifica le variabili all'inizio di `converti_e_trascrivi.py`:

```python
WHISPER_SERVER_PATH = r".\CORE\Whisper\whisper-server.exe"
WHISPER_MODEL_PATH = r".\CORE\Models\ggml-large-v3.bin"
WHISPER_SERVER_PORT = 8080
NR_THREADS = 4

EXPORT_TXT = True
EXPORT_SRT = True
EXPORT_VTT = False
EXPORT_JSON = False
```

- `EXPORT_*`: attiva/disattiva export del formato corrispondente
- `NR_THREADS`: numero thread per elaborazione CPU
