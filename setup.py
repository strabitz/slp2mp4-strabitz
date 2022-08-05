import setuptools

setuptools.setup(
    name='slp2mp4',
    version='2.0.0',
    install_requires=[
        'py-slippi>=1.6.2',
        'psutil>=5.9.1',
    ],
    package_dir={"": "slp2mp4"},
    entry_points={
        'console_scripts': [
            'slp2mp4 = slp2mp4:main'
        ],
    },
)
