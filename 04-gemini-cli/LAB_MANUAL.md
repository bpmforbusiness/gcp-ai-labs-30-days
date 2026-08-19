# Hands-on Lab: Gemini CLI

## 1. Objective of this Lab
In this hands-on lab, you will install and authenticate the Gemini CLI, and try out some basic use cases.

---

## 2. Before You Begin
If you do not already have a project that you can use, you will need to create a new project in the GCP console.

In this lab, we will use GCP Cloud Shell to perform the steps below: 
1. Open the Cloud Shell and set the project. 
2. Open the GCP Cloud Shell Editor by pressing the Cloud Shell Editor Button. 
3. If you see the "Authorize Shell" popup, click to authorize the Cloud Shell Editor.

Check if the project is already authenticated:
```bash
gcloud auth list
```

Confirm your current project:
```bash
gcloud config list project
```

If you can't remember your project ID, list all your project IDs:
```bash
gcloud projects list
```

If your project is not set, use the following command to set it:
```bash
gcloud config set project <YOUR_PROJECT_ID>
```

Enable the necessary services to run this lab:
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

---

## 3. Installation and Authentication

### Installation
Gemini CLI comes preinstalled in GCP Cloud Shell Editor. If you want to use that, you can get started right away.

To install Gemini CLI in your local environment, you need **Node.js 20+**. Execute the following command:
```bash
npm install -g @google/gemini-cli
```

To upgrade to the latest version:
```bash
npm update -g @google/gemini-cli
```

Run Gemini by executing the following command in your terminal:
```bash
gemini
```

### Authentication
If you are using GCP Cloud Shell Editor, you should already be authenticated if you authorized the shell. If you are running locally and haven't authenticated yet, type `/auth` in the Gemini CLI to bring up the authentication menu. *(Note: First, exit Gemini CLI with the `/quit` command if needed).*

**Method 1: Authenticate with Google**
1. Run `/auth` and select **Login with Google**.
2. Complete the login in your browser.
3. Specify your Google Cloud project (can also be done in a `.env` file):
```bash
export GOOGLE_CLOUD_PROJECT=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Method 2: Authenticate with API Key**
Generate an API Key from `aistudio.google.com` and set it in the console:
```bash
export GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Method 3: Authenticate with Vertex AI**
1. Authenticate into Google Cloud:
```bash
gcloud auth application-default login
```
2. Execute the following commands in your terminal:
```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT=<Your GCP Project Name>
export GOOGLE_CLOUD_LOCATION=us-central1
```

---

## 4. Try Gemini CLI

First, create and enter a project folder to run Gemini securely within its boundaries:
```bash
mkdir ~/my_cli_project
cd ~/my_cli_project
```

Enter the Gemini CLI:
```bash
gemini
```

### Basic Prompts
Try a simple prompt (this automatically uses the GoogleSearch Tool!):
> What is the weather today in Tokyo
> 今日の東京の天気について教えてください

### Using Tools
Confirm the installed tools:
```text
/tools
```

Get news from a local news site (e.g., mainichi.jp) using the WebFetch tool:
> Get me the news summary from https://mainichi.jp/
> このサイトからニュースのサマリーを教えてください https://mainichi.jp/

Run a multi-step task:
> Get me the news from https://mainichi.jp/ and filter in only the sports news and summarize that for me.
> https://mainichi.jp/ からニュースを取得し、スポーツニュースのみを抽出して、その要約を作成してください。

### System Commands
To run system commands, press `!` to enter command mode, type your command, and press `!` again to revert to normal mode.
```bash
!
ls
pwd
!
```

### Generate a Tic-Tac-Toe Game
Pass the following prompt to Gemini to generate a fully functioning game:

**English Prompt:**
> Please develop a Tic-Tac-Toe game that meets the following requirements. The solution should be split into separate HTML, CSS, and JavaScript files, with the JavaScript file handling the majority of the game logic independently.
> 1. General Requirements: One human vs. one computer. Show "GAME OVER" and the winner ("X wins!", "O wins!", or "Draw!"). Include a "Reset" button.
> 2. HTML (index.html): 9 clickable cells, game status display, reset button, and linked CSS/JS.
> 3. CSS (style.css): Clear borders, readable X and O fonts, standout game over message, and responsive design.
> 4. JavaScript (script.js):
> - Handle game state (array for board, current player, game end flag).
> - Initialization (clear board, set X, clear results).
> - Player interaction (click empty cell, update board, check win, switch turns).
> - Computer AI (randomly select empty cell for O, check win, switch back).
> - Win/Draw determination (check rows, columns, diagonals).
> - Game end handling (prevent clicks, display result).
> - Reset functionality.

**Japanese Prompt:**
> 以下の要件を満たす三目並べ（Tic-Tac-Toe）ゲームを開発してください。HTML、CSS、JavaScriptの各ファイルに分割し、JavaScriptはゲームロジックの大部分を単独で処理するようにしてください。
> 1. 全体要件: プレイヤーは人間1人、コンピューター1人。終了時は「GAME OVER」と勝者（「Xの勝利！」「Oの勝利！」「引き分け！」）を表示。リセットボタンを設ける。
> 2. HTML (index.html): 9つのマス目、状態表示、リセットボタン、CSS/JSのリンク。
> 3. CSS (style.css): 見やすいマス目の枠線、X/Oのフォントサイズと色、レスポンシブ対応。
> 4. JavaScript (script.js):
> - 状態管理（ボード配列、現在のプレイヤー、終了フラグ）。
> - 初期化（マス目を空に、Xに設定、表示クリア）。
> - プレイヤー操作（空マスのみ配置、勝敗判定、交代）。
> - コンピューターの思考ロジック（ランダム配置、勝敗判定、交代）。
> - 勝敗判定（3つの行・列・対角線でチェック、引き分け判定）。
> - ゲーム終了時の処理（クリック無効化、結果表示）。
> - リセット機能。

### Test Your Generated Code
Open a new terminal in Cloud Shell (Terminal > New) and run a Python server to test your game:
```bash
gcloud config set project <YOUR_PROJECT_ID>
cd ~/my_cli_project
python3 -m http.server 8080
```
Open `http://localhost:8080` in your browser (CTRL+click in Cloud Shell).

---

## 5. Run Gemini CLI Extensions

Gemini CLI provides useful extensions to connect to various services (see [geminicli.com/extensions](https://geminicli.com/extensions/)). Let's install the **Nanobanana** extension for image generation.

Install the extension:
```bash
gemini extensions install https://github.com/gemini-cli-extensions/nanobanana
```

Restart the Gemini CLI. Before running it, set your Gemini API key:
```bash
export NANOBANANA_GEMINI_API_KEY=<YOUR_API_KEY>
```

### Available Nanobanana Commands:
* `/generate` - Single/multiple image generation
* `/edit` - Image editing
* `/restore` - Image restoration
* `/icon` - Generate app icons and UI elements
* `/pattern` - Generate seamless patterns
* `/story` - Generate sequential visual stories
* `/diagram` - Generate technical diagrams
* `/nanobanana` - Natural language interface

### Example Generation Prompts (English)
```text
# Single image
/generate "a watercolor painting of a fox in a snowy forest"

# Multiple variations with preview
/generate "sunset over mountains" --count=3 --preview

# Style variations
/generate "mountain landscape" --styles="watercolor,oil-painting" --count=4

# Specific variations with auto-preview
/generate "coffee shop interior" --variations="lighting,mood" --preview
```

### Example Generation Prompts (Japanese)
```text
# Single image
/generate "雪の森のキツネの水彩画"

# Multiple variations with preview
/generate "山にかかる夕焼け" --count=3 --preview

# Style variations
/generate "山岳風景" --styles="watercolor,oil-painting" --count=4

# Specific variations with auto-preview
/generate "コーヒーショップのインテリア" --variations="lighting,mood" --preview
```

### Editing Images
*(Make sure to change the file name to your local file)*
```text
/edit my_photo.png "change the color of fox to blue"
```

---

## 6. Challenge!
Think of the prompts you could use to make these applications using the Gemini CLI:
* Your favorite game
* A photo gallery application
* A Manga generator app
