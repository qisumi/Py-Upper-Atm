#!/bin/bash
# HWM14 编译脚本
# 编译 HWM14 Fortran 源代码为 Linux 共享库

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始编译 HWM14...${NC}"

# 检查源文件是否存在
if [ ! -f "hwm14.f90" ]; then
    echo -e "${RED}错误: 找不到 hwm14.f90 文件${NC}"
    exit 1
fi

if [ ! -f "hwm_cshim.F90" ]; then
    echo -e "${RED}错误: 找不到 hwm_cshim.F90 文件${NC}"
    exit 1
fi

# 编译源文件为目标文件
echo -e "${YELLOW}正在编译 hwm14.f90...${NC}"
if ! gfortran -O3 -c hwm14.f90; then
    echo -e "${RED}编译 hwm14.f90 失败${NC}"
    exit 1
fi

echo -e "${YELLOW}正在编译 hwm_cshim.F90...${NC}"
if ! gfortran -O3 -c hwm_cshim.F90; then
    echo -e "${RED}编译 hwm_cshim.F90 失败${NC}"
    exit 1
fi

# 链接为共享库
echo -e "${YELLOW}正在链接生成 libhwm14.so...${NC}"
if ! gfortran -shared -o libhwm14.so hwm14.o hwm_cshim.o -static-libgcc -static-libgfortran -static-libquadmath; then
    echo -e "${RED}链接生成 libhwm14.so 失败${NC}"
    exit 1
fi

# 清理临时文件
echo -e "${YELLOW}正在清理临时文件...${NC}"
rm -f *.mod *.o

echo -e "${GREEN}HWM14 编译完成!${NC}"