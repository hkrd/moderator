from setuptools import setup, find_packages

setup(
    name="moderator",
    version="0.1.0",
    packages=find_packages(include=["src", "src.*"]),
    py_modules=["main"],  
    entry_points={
        "console_scripts": [
            "moderator=main:cli",
        ],
    },
    install_requires=["click", "fastapi", "requests", "uvicorn", "openai"],
    python_requires=">=3.11",
    description="A content moderation tool with a FastAPI server and CLI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    include_package_data=True,
)
