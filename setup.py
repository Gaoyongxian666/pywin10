# -*- coding: UTF-8 -*-
"""
@Project ：pywin10
@File ：setup.py.py
@Author ：Gao yongxian
@Date ：2021/11/30 13:24
@contact: g1695698547@163.com
"""
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pywin10",
    version="0.0.3",
    author="Gaoyongxian666",
    author_email="g1695698547@163.com",
    description="基于Pywin32,封装了系统托盘,右键菜单,win10通知栏等功能",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Gaoyongxian666/pywin10",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["pywin32"],
    include_package_data=True,
    project_urls={
        'Bug Reports': 'https://github.com/Gaoyongxian666/pywin10',
        'Source': 'https://github.com/Gaoyongxian666/pywin10',
    },
)

