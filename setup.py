from setuptools import setup, find_packages

setup(
    name="RealTimeMQ",
    version="0.1.0",
    packages=find_packages(),  # Auto-detects all packages
    install_requires=[
        "paho-mqtt",
        "Django>=3.2",
    ],
    include_package_data=True,
    description="A pluggable Django app for MQTT-based chat and notifications.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/smarakaranjan/RealTimeMQ",
    author="Your Name",
    author_email="your_email@example.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Django",
        "License :: OSI Approved :: MIT License",
    ],
)
