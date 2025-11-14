#!/bin/bash
# HWM93 编译脚本
# 编译 HWM93 Fortran 源代码为 Linux 共享库

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始编译 HWM93...${NC}"

# 检查源文件是否存在
if [ ! -f "hwm93.f" ]; then
    echo -e "${RED}错误: 找不到 hwm93.f 文件${NC}"
    exit 1
fi

if [ ! -f "hwm93_cshim.F90" ]; then
    echo -e "${RED}错误: 找不到 hwm93_cshim.F90 文件${NC}"
    exit 1
fi

# 编译源文件为目标文件
echo -e "${YELLOW}正在编译 hwm93.f...${NC}"
if ! gfortran -O3 -c hwm93.f; then
    echo -e "${RED}编译 hwm93.f 失败${NC}"
    exit 1
fi

echo -e "${YELLOW}正在编译 hwm93_cshim.F90...${NC}"
if ! gfortran -O3 -c hwm93_cshim.F90; then
    echo -e "${RED}编译 hwm93_cshim.F90 失败${NC}"
    exit 1
fi

# 链接为共享库
echo -e "${YELLOW}正在链接生成 libhwm93.so...${NC}"
if ! gfortran -shared -o libhwm93.so hwm93.o hwm93_cshim.o -static-libgcc -static-libgfortran -static-libquadmath; then
    echo -e "${RED}链接生成 libhwm93.so 失败${NC}"
    exit 1
fi

# 清理临时文件
echo -e "${YELLOW}正在清理临时文件...${NC}"
rm -f *.mod *.o

echo -e "${GREEN}HWM93 编译完成!${NC}"