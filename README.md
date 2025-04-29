# Crystal Growth RHEED Image Analysis System

## Installation

```shell
# Terminal
pip install -r requirements.txt

# Unix
chmod +x install.sh
./install.sh
```

## How to run

```shell
python run-gui.py

# When applying in the factory, run the following script to capture live screenshots of computer
python run-script.py
```

## Project Structure

```shell
crystal
├── README-ZH.md
├── README.md
├── crystal
│   ├── __init__.py
│   ├── core.py
│   ├── image_processing.py
│   ├── image_window.py
│   ├── plot_window.py
│   ├── scripts
│   │   └── sync_images.py
│   └── utils.py
├── requirements.txt
├── run-script.py
└── run-gui.py
```

## User Guide

See user guide in user_guide.html or you can view it in the app.
