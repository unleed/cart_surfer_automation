# Cart Surfer Bot

Automation for the Cart Surfer game (Club Penguin), compatible with servers like **NewCP** and **CP Journey**.

This bot automatically detects the game on screen, starts the match, performs tricks to earn points, and avoids obstacles (turns).

## Requirements

- **uv** (python dependency manager)
- Windows (Tested on Windows 10/11)

## Installation

1.  **Clone or download** this repository.
2.  Open the terminal in the project folder.
3.  Install **uv** using the command:

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

4.  Install python using the command:

```bash
uv python install
```

5.  Install the dependencies using the command:

```bash
uv sync
```

## How to Use

The bot must be run via the command line (CMD or PowerShell).

### Basic Command

```bash
uv run main.py -g newcp
```
or
```bash
uv run main.py -g journey
```

The `-g` (or `--game`) argument is **required** and defines which version of the game you are playing (`newcp` or `journey`). This adjusts the colors and images used for detection.

### Additional Options

-   `-debug`: Activates debug mode, showing detailed logs in the terminal about what the bot is detecting.
    ```bash
    uv run main.py -g newcp -debug
    ```
-   `-vis`: Activates a real-time visualization window, showing what the bot "sees" and the detection zones.
    ```bash
    uv run main.py -g newcp -vis
    ```

## In-Game Controls

-   **`CTRL + ALT + S`**: **Start / Stop** the bot.
    -   When started, it will try to find the game and begin.
    -   Press again to pause at any time.
-   **`CTRL + E`**: **Emergency Stop**. Terminates the script immediately.

## Folder Structure

The bot expects reference images to be organized as follows:

```
cart_surfer_automation/
├── images/
│   ├── newcp/
│   │   ├── cart_surfer.png
│   │   ├── yes.png
│   │   ├── play.png
│   │   ├── close.png
│   │   └── shack.png
│   └── journey/
│       ├── (equivalent images)
├── main.py
├── game_player.py
├── game_starter.py
└── ...
```

## How It Works

1.  When started (`CTRL+ALT+S`), the bot looks for the `cart_surfer.png` image on the screen.
2.  It clicks "Yes" and then "Play".
3.  During the game:
    -   Performs tricks (Loop and 360) to score points.
    -   Detects turns by track colors (left/right zones) and turns automatically.
    -   Automatically restarts the game upon detecting the end of the match (`close.png` / `shack.png`).

## Troubleshooting

-   **Bot doesn't click:** Verify if the images in the `images/` folder match exactly what appears on your screen. Game resolution or theme may vary. Take new screenshots if necessary and replace the files.
-   **ROI Error:** If the bot cannot find the game region, ensure the game is visible on screen and not minimized.
-   **Permissions:** The bot controls mouse and keyboard. You may need to run the terminal as Administrator.