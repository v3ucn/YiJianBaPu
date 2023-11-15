# 一键扒谱

本项目fork自https://github.com/openvpi/SOME


## 安装依赖

   ```bash
   pip install -r requirements.txt
   ```

### 下载模型

```
链接：https://pan.baidu.com/s/1lVQcKP7ijTELslJNgoDqkQ?pwd=odsm 
```

2stems模型放到项目的pretrained_models目录下

ckpt模型放入项目的ckpt目录下

如果没有ckpt和pretrained_models目录，请手动建立。

如下所示：

```
├───ckpt
│       config.yaml
│       model_ckpt_steps_104000_simplified.ckpt
├───pretrained_models
│   └───2stems
│           ._checkpoint
│           checkpoint
│           model.data-00000-of-00001
│           model.index
│           model.meta
```
### 人声和背景音分离

如果没有output目录，请手动建立，test.mp3为需要扒谱的音乐文件

```
spleeter separate -p spleeter:2stems -o ./output ./test.mp3   
```

### 人声降噪

```
python test_noisereduce.py
```

### 扒谱（人声转换为midi）

```
python infer.py --model ./ckpt/model_ckpt_steps_104000_simplified.ckpt --wav ./output/vocals.wav  
```

midi存储于项目的output目录下

