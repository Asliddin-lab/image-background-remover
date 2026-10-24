import os
from setuptools import setup, find_packages

setup(
    name="image-background-remover",
    version="1.0.0",
    description="High-performance Image Background Remover powered by AI (U2Net/IS-Net), Chroma/Colorkey & FFmpeg",
    long_description=open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Asliddin",
    url="https://github.com/Asliddin-lab/image-background-remover",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "bg_remover": ["templates/*", "static/*"],
    },
    python_requires=">=3.9",
    install_requires=[
        "Pillow>=9.5.0",
        "rembg>=2.0.50",
        "onnxruntime>=1.15.0",
        "numpy>=1.21.0",
        "Flask>=2.3.0",
        "tqdm>=4.65.0",
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "bg-remover=bg_remover.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
