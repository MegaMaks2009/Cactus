# Cactus V2
Fast offline voice-controlled app launcher for Windows.

## How to install?
1. Download the project.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Run the program:
   `python main.py`

## How to use?
1. Cactus listens to your microphone and recognizes english voice commands.
2. To open, close, or terminate a program, say `"open"`, `"close"`, or `"terminate"` followed by the program name. For example: `open chrome`.
3. Say "exit" to close Cactus
4. `data/programs.json` contains the names Cactus can recognize and the paths to the programs. The left side is what you say: "chrome", The right side is the path to the program: "C:\\chrome.exe", for example: "program name": "program path".
5. If you want to use a non-standard or more natural command, say `"Cactus"` before your request. For example: `Cactus I would like to see my browser`.
6. Voice commands and program names should be pronounced clearly in English. Before using Cactus, it is recommended to check the correct pronunciation of the words you want to use.
7. The local AI model uses your GPU through Vulkan by default. If you want to run it on the CPU instead, open `main.py` and change: `Engine = "vulkan"` to `Engine = "cpu"`.
