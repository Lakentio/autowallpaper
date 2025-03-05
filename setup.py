from setuptools import setup, find_packages

setup(
    name="autowallpaper",
    version="0.1",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'autowallpaper=autowallpaper.__main__:main'
        ],
    },
)
