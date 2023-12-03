

# 晶体生长RHEED图像智能分析系统

## 安装

```shell
pip install -r requirements.txt
```

## 运行

```shell
python run.py
```

## 项目结构

```shell
crystal_proj/
│
├── README.md               
├── run.py
├── data/
├── requirements.txt
│
├── crystal/             
│   ├── __init__.py        
│   ├── image_processing.py
│   ├── image_window.py
│   ├── plot_window.py
│   ├── core.py
│   └── utils.py            
│
└── tests/
    └── spot_detect_new_v1.py


```

