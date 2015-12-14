from setuptools import setup

from binview import __version__

setup(
    author='Justus Perlwitz',
    author_email='hello@justus.pw',
    description='Binary File Visualizer',
    entry_points={
        'console_scripts': [
            'binview = binview.binview:main',
        ],
    },
    install_requires=[],
    license='MIT',
    name='binview',
    packages=['binview'],
    url='https://github.com/justuswilhelm/binview',
    version=__version__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
