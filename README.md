# NGSL 词表生成器

把 [NGSL](https://www.newgeneralservicelist.com/)（新通用词表）做成带**美式音标、词性、中文释义**的清单，一次生成三种格式：

| 文件 | 用途 |
|---|---|
| `output/NGSL_前2000词.md` | 表格，阅读、做笔记用 |
| `output/NGSL_前2000词.csv` | 表格，Excel 打开、导进 Anki |
| `output/NGSL点读.html` | 网页，**点一下单词就用系统语音念** |

## 用法

```bash
python3 build.py            # 默认取前 2000 词
python3 build.py --limit 500
```

首次运行会把三份原始数据下载到 `data/`（约 70MB），之后再跑直接复用。生成的成果在 `output/`。只依赖 Python 3 标准库，不用装任何包。

## 数据来源

| 数据 | 来源 | 授权 |
|---|---|---|
| 词表与频次 | NGSL 1.2，newgeneralservicelist.com | Creative Commons（官网注明允许商用） |
| 中文释义 | [ECDICT](https://github.com/skywind3000/ECDICT) | MIT |
| 美式音标 | [CMU Pronouncing Dictionary](https://github.com/cmusphinx/cmudict) | BSD 类（允许再分发） |

`data/` 里的原始数据不进版本库，由脚本自动下载；`output/` 里的成果会提交，方便直接用。

## 音标说明

CMU 词典用的是 ARPAbet 记法（`AH0 B AE1 N D AH0 N`），`ipa.py` 把它转成国际音标：

- 元音带数字 0/1/2 表示无重音/主重音/次重音，转成 `ə` 与 `ˈ` `ˌ`
- 美音特有的卷舌元音：`ER` 转成 `ɝ`（重读）、`ɚ`（轻读）
- 重音符号放在重读音节的起首辅音之前，而不是紧贴元音

## 想换一份词表？

`build.py` 里 `SOURCES['ngsl']` 换成别的词表地址、再改一下读取列名就能复用同一套流程（比如 NGSL 口语版、TOEIC 词表、你自己的生词表）。
