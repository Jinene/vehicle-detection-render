from setuptools import setup, find_packages

setup(
    name="vehicle-detection",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "opencv-python-headless>=4.8.1.78",
        "ultralytics>=8.0.186", 
        "numpy>=1.24.3",
        "flask>=2.3.3",
        "pillow>=10.0.0",
        "gunicorn>=21.2.0"
    ],
    python_requires=">=3.9",
)
