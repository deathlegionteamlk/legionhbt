from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="legionhbt",
    version="1.0.0",
    author="death legion",
    author_email="",
    description="LEGIONHBT - Autonomous AI System with 12-Component Harness Architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deathlegion/legionhbt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "flask>=2.3.0",
        "safetensors>=0.3.0",
        "numpy>=1.24.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "legionhbt=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "legionhbt": ["templates/*.html", "static/*"],
    },
)
