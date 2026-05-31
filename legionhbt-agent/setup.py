from setuptools import setup, find_packages

setup(
    name="legionhbt-agent",
    version="1.0.0",
    description="LEGIONHBT Autonomous Pentesting Agent - AI-powered vulnerability discovery and exploitation",
    author="death legion",
    author_email="demo@legionhbt.ai",
    packages=find_packages(),
    install_requires=[
        "flask==3.0.3",
        "flask-socketio==5.3.6",
        "openai==1.30.0",
        "anthropic==0.28.0",
        "requests==2.31.0",
        "python-nmap==0.7.1",
        "sqlalchemy==2.0.30",
        "pydantic==2.7.1",
        "python-dotenv==1.0.1",
        "aiohttp==3.9.5",
        "psutil==5.9.8",
        "paramiko==3.4.0",
        "pexpect==4.9.0",
        "eventlet==0.36.1",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "legionhbt-agent=agent.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Security :: Penetration Testing",
    ],
    license="MIT",
)