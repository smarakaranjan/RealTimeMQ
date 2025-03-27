from setuptools import setup, find_packages

setup(
    name="django-mqtt-service",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "django>=3.2",
        "paho-mqtt>=1.6.1"
    ],
    author="Your Name",
    author_email="your_email@example.com",
    description="A Django plugin for real-time MQTT-based messaging and notifications",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/django-mqtt-service",
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
