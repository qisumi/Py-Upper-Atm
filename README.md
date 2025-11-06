# DQZNMX-interface

这是一个包含多种大气模型接口的项目，包括HWM14、HWM93、MSIS00和MSIS2等。

## Git LFS 使用指南

### 初始化 Git LFS

项目中的数据文件（如.dat、.bin、.parm等）使用Git LFS进行管理。使用前请确保已安装Git LFS并进行初始化：

1. 首先安装Git LFS客户端：
   - Windows: 可以通过Git安装程序安装，或从[官方网站](https://git-lfs.github.com/)下载
   - macOS: `brew install git-lfs`
   - Linux: `apt-get install git-lfs` 或 `yum install git-lfs`

2. 在项目目录中初始化Git LFS：
   ```bash
   cd c:\Users\ZiQiQ\Desktop\DQZNMX-interface
   git lfs install
   git lfs track "*.dat" "*.bin" "*.parm"
   ```

3. 确保`.gitattributes`文件被添加到版本控制中：
   ```bash
   git add .gitattributes
   git commit -m "Add Git LFS configuration"
   ```

### 后续使用

初始化后，正常使用Git命令即可，Git LFS会自动处理大型文件：

```bash
# 添加文件
git add *.dat *.bin *.parm

# 提交和推送
git commit -m "Add data files"
git push origin main
```

### 克隆项目

当克隆此项目时，Git LFS会自动下载大型文件：

```bash
git clone <repository-url>
cd <repository-name>
```

如果需要手动拉取LFS文件，可以运行：
```bash
git lfs pull
```
