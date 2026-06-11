from setuptools import setup, find_packages

setup(
    name="yesterwind-zmodem",
    version="0.1.0",
    description="Pure Python implementation of ZModem, YModem, and XModem",
    author="City Club Intern Bot",
    author_email="cityclubintern@ehw.io",
    url="https://github.com/ehwio/yesterwind-zmodem",
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)