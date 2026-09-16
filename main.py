import json
import os
import subprocess
import psutil
import sherpa_onnx
import sounddevice as sd
from rapidfuzz import process, fuzz
import ctypes
import sentencepiece as spm
import urllib.request

def close_program(path):
    exe_name = os.path.basename(path)
    subprocess.run(["taskkill", "/IM", exe_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def terminate_program(path):
    exe_name = os.path.basename(path)
    subprocess.run(["taskkill", "/F", "/IM", exe_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def handle_command(text):
    global last_program

    words = text.split()

    command = None
    command_index = -1

    for i in range(len(words)):
        if fuzz.ratio(words[i], "open") >= 75:
            command = "open"
            command_index = i

        elif fuzz.ratio(words[i], "close") >= 75:
            command = "close"
            command_index = i

        elif fuzz.ratio(words[i], "terminate") >= 75:
            command = "terminate"
            command_index = i

    if command is None:
        return False

    program_name = " ".join(words[command_index + 1:])

    if not program_name:
        return False

    match = process.extractOne(program_name, programs.keys(), scorer=fuzz.ratio, score_cutoff=65)

    if not match:
        return False

    path = programs[match[0]]
    last_program = match[0]

    if command == "open":
        subprocess.Popen([path])

    elif command == "close":
        close_program(path)

    elif command == "terminate":
        terminate_program(path)

    return True


programs = json.load(open("data/programs.json", encoding="utf-8"))
last_program = ""

def build_prompt():
    return open("ttt model/prompt.txt", encoding="utf-8").read().replace("{PROGRAMS}", "\n".join(programs.keys())).replace("{LAST_PROGRAM}", last_program)


def normalize_text(text):
    words = text.split()

    for i in range(len(words)):
        match = process.extractOne(words[i], ["open", "close", "terminate"] + list(programs.keys()), scorer=fuzz.ratio, score_cutoff=75)
        if match:
            words[i] = match[0]

    return " ".join(words)


hotwords = list(programs.keys()) + ["cactus", "open", "close", "terminate", "exit"]
with open("stt model/hotwords.txt", "w", encoding="utf-8") as h:
    h.write("\n".join(hotwords))


recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(tokens="stt model/tokens.txt", encoder="stt model/encoder.onnx", decoder="stt model/decoder.onnx", joiner="stt model/joiner.onnx", bpe_vocab="stt model/bpe.vocab", hotwords_file="stt model/hotwords.txt", hotwords_score=2, num_threads=1, sample_rate=16000, feature_dim=80, enable_endpoint_detection=True, rule1_min_trailing_silence=2, rule2_min_trailing_silence=1, rule3_min_utterance_length=999999, decoding_method="modified_beam_search", max_active_paths=10, modeling_unit="bpe", provider="cpu")

Engine = "vulkan"
server = subprocess.Popen([f"ttt engine/{Engine.lower()}/llama-server.exe", "-m", "ttt model/ai.gguf", "-c", "512", "-n", "100", "-t", "8", *(["-ngl", "all"] if Engine.lower() == "vulkan" else []), "--keep", "-1", "-fa", "on", "--reasoning", "off", "--alias", "ai", "--host", "127.0.0.1", "--port", "2222"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

stream = recognizer.create_stream()
last_text = ""
cactus_mode = False

print("Cactus V2")
with sd.InputStream(channels=1, dtype="float32", samplerate=16000, blocksize=300, latency="low") as mic:

    while True:
        audio, _ = mic.read(300)
        stream.accept_waveform(16000, audio.reshape(-1))

        while recognizer.is_ready(stream):
            recognizer.decode_stream(stream)

        text = normalize_text(recognizer.get_result(stream).lower().strip())

        if text:
            for i in range(len(text.split())):
                if fuzz.ratio(text.split()[i], "cactus") >= 75:
                    cactus_mode = True
                    text = " ".join(text.split()[i + 1:])
                    break

        if cactus_mode:
            if recognizer.is_endpoint(stream):
                print("STT:",text)
                request = urllib.request.Request("http://127.0.0.1:2222/v1/chat/completions", data=json.dumps({"model": "ai", "messages": [{"role": "system", "content": build_prompt()}, {"role": "user", "content": text}], "max_tokens": 30, "temperature": 0}).encode(), headers={"Content-Type": "application/json"})
                data = json.loads(urllib.request.urlopen(request).read())
                answer = data["choices"][0]["message"]["content"].lower().strip()

                print("TTT:", answer)
                handle_command(answer)
                cactus_mode = False
                stream = recognizer.create_stream()
                last_text = ""
            continue

        if not text:
            continue

        if text == last_text:
            continue

        last_text = text
        print("STT:",text)

        words = text.split()

        for word in words:
            if fuzz.ratio(word, "exit") >= 80:
                server.kill()
                server.wait()
                exit()

        if handle_command(text):
            stream = recognizer.create_stream()
            last_text = ""
