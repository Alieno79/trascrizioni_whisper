import os
import subprocess
import sys
import argparse
import time
import json
import requests
from pydub import AudioSegment

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OGG_DIR = os.path.join(BASE_DIR, r"INPUTS\OGG")
MP3_DIR = os.path.join(BASE_DIR, r"INPUTS\MP3")
TXT_DIR = os.path.join(BASE_DIR, r"OUTPUTS\TXT")
SRT_DIR = os.path.join(BASE_DIR, r"OUTPUTS\SRT")
VTT_DIR = os.path.join(BASE_DIR, r"OUTPUTS\VTT")
JSON_DIR = os.path.join(BASE_DIR, r"OUTPUTS\JSON")

WHISPER_SERVER_PATH = r".\CORE\Whisper\whisper-server.exe"
WHISPER_MODEL_PATH = r".\CORE\Models\ggml-large-v3.bin"
WHISPER_MODEL_DEST_LANGUAGE = "it"
WHISPER_SERVER_PORT = 8080
WHISPER_SERVER_PARAMS = ["-m", WHISPER_MODEL_PATH, "-l", WHISPER_MODEL_DEST_LANGUAGE,"-bo", "5", "-bs", "5", "-fa"]
NR_THREADS = 6

EXPORT_TXT = True
EXPORT_SRT = True
EXPORT_VTT = False
EXPORT_JSON = False

SRT_PRIMARY_FORMAT = True


def parse_srt_to_json(srt_text):
    entries = []
    blocks = srt_text.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            index = lines[0]
            timing = lines[1]
            text = "\n".join(lines[2:])
            start, end = timing.split(" --> ")
            entries.append({
                "index": index,
                "start": start,
                "end": end,
                "text": text
            })
    return {"entries": entries}


def srt_to_vtt(srt_text):
    return srt_text.replace(",", ".")


def srt_to_txt(srt_text):
    lines = []
    blocks = srt_text.strip().split("\n\n")
    for block in blocks:
        parts = block.strip().split("\n", 2)
        if len(parts) >= 3:
            text = parts[2]
            text = text.replace("\n", " ")
            text = text.replace(". ", ".\n")
            text = text.replace(", ", ",\n")
            text_lines = text.split("\n")
            lines.extend([t.strip() for t in text_lines])
    return "\n".join(lines)


whisper_proc = None


def crea_cartelle():
    os.makedirs(MP3_DIR, exist_ok=True)
    os.makedirs(TXT_DIR, exist_ok=True)
    os.makedirs(SRT_DIR, exist_ok=True)
    os.makedirs(VTT_DIR, exist_ok=True)
    os.makedirs(JSON_DIR, exist_ok=True)


def avvia_whisper_server(use_gpu=True, debug=False):
    global whisper_proc
    params = WHISPER_SERVER_PARAMS.copy()
    if not use_gpu:
        if "-fa" in params:
            params.remove("-fa")
        params.extend(["-t", str(NR_THREADS), "--no-gpu"])
    if debug:
        params.append("-debug")
    print(f"Avvio whisper-server sulla porta {WHISPER_SERVER_PORT}...")
    print(f"Parametri: {' '.join(params)}")
    if debug:
        whisper_proc = subprocess.Popen(
            [WHISPER_SERVER_PATH] + params
        )
    else:
        whisper_proc = subprocess.Popen(
            [WHISPER_SERVER_PATH] + params,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    time.sleep(3)


def chiudi_whisper_server():
    global whisper_proc
    if whisper_proc:
        print("Chiusura whisper-server...")
        whisper_proc.terminate()
        try:
            whisper_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            whisper_proc.kill()
        print("whisper-server chiuso")


def converti_ogg_mp3(ogg_path, mp3_path):
    audio = AudioSegment.from_file(ogg_path, format="ogg")
    audio.export(mp3_path, format="mp3", bitrate="192k")


def trascrivi(mp3_path, output_txt_path):
    nome_file = os.path.basename(output_txt_path)
    base_name = os.path.splitext(nome_file)[0]
    url = f"http://localhost:{WHISPER_SERVER_PORT}/inference"

    if SRT_PRIMARY_FORMAT:
        with open(mp3_path, "rb") as f:
            files = {"file": (os.path.basename(mp3_path), f, "audio/mpeg")}
            data = {"response_format": "srt"}
            try:
                response = requests.post(url, files=files, data=data, timeout=300)
            except requests.exceptions.Timeout:
                raise Exception("Timeout request al server (5 min)")

        if response.status_code != 200:
            raise Exception(f"Errore server: {response.status_code} - {response.text}")

        srt_text = response.text

        formatiCreati = []

        if EXPORT_SRT:
            output_path = os.path.join(SRT_DIR, f"{base_name}.srt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(srt_text)
            formatiCreati.append("SRT")

        if EXPORT_VTT:
            vtt_text = srt_to_vtt(srt_text)
            output_path = os.path.join(VTT_DIR, f"{base_name}.vtt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(vtt_text)
            formatiCreati.append("VTT")

        if EXPORT_TXT:
            txt_text = srt_to_txt(srt_text)
            output_path = os.path.join(TXT_DIR, nome_file)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(txt_text)
            formatiCreati.append("TXT")

        if EXPORT_JSON:
            json_data = parse_srt_to_json(srt_text)
            json_path = os.path.join(JSON_DIR, f"{base_name}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            formatiCreati.append("JSON")

        print(f"Trascrizione terminata per {base_name}: {', '.join(formatiCreati)}")
    else:
        formati = []
        if EXPORT_TXT:
            formati.append("txt")
        if EXPORT_SRT:
            formati.append("srt")
        if EXPORT_VTT:
            formati.append("vtt")

        results = {}
        for fmt in formati:
            with open(mp3_path, "rb") as f:
                files = {"file": (os.path.basename(mp3_path), f, "audio/mpeg")}
                data = {"response_format": fmt}
                response = requests.post(url, files=files, data=data)

            if response.status_code == 200:
                results[fmt] = response.text
            else:
                raise Exception(f"Errore server: {response.status_code} - {response.text}")

        if EXPORT_JSON and "txt" in results:
            json_path = os.path.join(JSON_DIR, f"{base_name}.json")
            try:
                result = response.json()
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                with open(json_path, "w", encoding="utf-8") as f:
                    f.write(results["txt"])

        if EXPORT_TXT and "txt" in results:
            output_path = os.path.join(TXT_DIR, nome_file)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(results["txt"])

        if EXPORT_SRT and "srt" in results:
            output_path = os.path.join(SRT_DIR, f"{base_name}.srt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(results["srt"])

        if EXPORT_VTT and "vtt" in results:
            output_path = os.path.join(VTT_DIR, f"{base_name}.vtt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(results["vtt"])


def solo_conversione():
    crea_cartelle()

    if not os.path.exists(OGG_DIR):
        print(f"Cartella {OGG_DIR} non trovata")
        sys.exit(1)

    file_ogg = [f for f in os.listdir(OGG_DIR) if f.lower().endswith(".ogg")]

    if not file_ogg:
        print("Nessun file OGG trovato")
        sys.exit(1)

    print(f"Trovati {len(file_ogg)} file OGG")

    for filename in file_ogg:
        nome_base = os.path.splitext(filename)[0]
        ogg_path = os.path.join(OGG_DIR, filename)
        mp3_path = os.path.join(MP3_DIR, f"{nome_base}.mp3")

        print(f"Conversione: {filename} -> {nome_base}.mp3")
        converti_ogg_mp3(ogg_path, mp3_path)

    print("Fatto!")
    print(f"File salvati in: {MP3_DIR}")


def solo_trascrizione(use_gpu=True, debug=False):
    crea_cartelle()

    if not os.path.exists(MP3_DIR):
        print(f"Cartella {MP3_DIR} non trovata")
        sys.exit(1)

    file_mp3 = [f for f in os.listdir(MP3_DIR) if f.lower().endswith(".mp3")]

    if not file_mp3:
        print("Nessun file MP3 trovato")
        sys.exit(1)

    print(f"Trovati {len(file_mp3)} file MP3")

    try:
        avvia_whisper_server(use_gpu, debug)

        for filename in file_mp3:
            nome_base = os.path.splitext(filename)[0]
            mp3_path = os.path.join(MP3_DIR, filename)
            txt_path = os.path.join(TXT_DIR, f"{nome_base}.txt")

            try:
                trascrivi(mp3_path, txt_path)
            except Exception as e:
                print(f"Errore trascrizione {filename}: {e}")
    finally:
        chiudi_whisper_server()

    print("Fatto!")
    print(f"File salvati in: {TXT_DIR}")


def conversione_e_trascrizione(use_gpu=True, debug=False):
    global whisper_proc
    crea_cartelle()

    if not os.path.exists(OGG_DIR):
        print(f"Cartella {OGG_DIR} non trovata")
        sys.exit(1)

    file_ogg = [f for f in os.listdir(OGG_DIR) if f.lower().endswith(".ogg")]

    if not file_ogg:
        print("Nessun file OGG trovato")
        sys.exit(1)

    print(f"Trovati {len(file_ogg)} file OGG")

    print("Conversione OGG -> MP3...")
    mp3_files = []
    for filename in file_ogg:
        nome_base = os.path.splitext(filename)[0]
        ogg_path = os.path.join(OGG_DIR, filename)
        mp3_path = os.path.join(MP3_DIR, f"{nome_base}.mp3")
        txt_path = os.path.join(TXT_DIR, f"{nome_base}.txt")
        converti_ogg_mp3(ogg_path, mp3_path)
        mp3_files.append((mp3_path, txt_path))

    print(f"Conversione completata: {len(mp3_files)} file")

    try:
        avvia_whisper_server(use_gpu, debug)

        for mp3_path, txt_path in mp3_files:
            nome = os.path.basename(mp3_path)
            try:
                trascrivi(mp3_path, txt_path)
            except Exception as e:
                print(f"Errore trascrizione {nome}: {e}")
                continue
    finally:
        chiudi_whisper_server()

    print("Fatto!")


def solo_server(use_gpu=True, debug=False):
    params = WHISPER_SERVER_PARAMS.copy()
    if not use_gpu:
        if "-fa" in params:
            params.remove("-fa")
        params.extend(["-t", str(NR_THREADS), "--no-gpu"])
    if debug:
        params.append("-debug")
    print(f"Avvio whisper-server sulla porta {WHISPER_SERVER_PORT}...")
    print(f"Parametri: {' '.join(params)}")
    print("Server avviato. Premi CTRL+C per terminare.")
    whisper_proc = subprocess.Popen(
        [WHISPER_SERVER_PATH] + params
    )
    try:
        whisper_proc.wait()
    except KeyboardInterrupt:
        print("\nChiusura server...")
        whisper_proc.terminate()
        whisper_proc.wait()


def main():
    parser = argparse.ArgumentParser(description="Converti OGG in MP3 e trascrivi con whisper")
    parser.add_argument("-C", "--converti", action="store_true", help="Solo conversione OGG->MP3")
    parser.add_argument("-MP3", "--mp3", action="store_true", help="Solo trascrizione da MP3")
    parser.add_argument("-S", "--server", action="store_true", help="Avvia solo il server (CTRL+C per terminare)")
    parser.add_argument("-CPU", "--cpu", dest="use_cpu", action="store_true", help="Usa CPU invece di GPU")
    parser.add_argument("-DBG", "--debug", dest="debug", action="store_true", help="Modalita debug")

    args = parser.parse_args()
    use_gpu = not args.use_cpu
    debug = args.debug

    if args.server:
        solo_server(use_gpu, debug)
    elif args.converti:
        solo_conversione()
    elif args.mp3:
        solo_trascrizione(use_gpu, debug)
    else:
        conversione_e_trascrizione(use_gpu, debug)


if __name__ == "__main__":
    main()