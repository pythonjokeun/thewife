from setuptools import setup

setup(
    name='thewife',
    version='0.1.2-MFI',
    description='Trading bot that reacts to optimized RSI indicator',
    packages=['thewife'],
    install_requires=[
        'pyyaml', 'ccxt', 'attr', 'tenacity', 'logzero', 'hyperopt', 'pyti',
        'pandas', 'numpy', 'networkx==1.11', 'pyfiglet', 'notifiers'
    ],
    entry_points={'console_scripts': ['wife = thewife.__main__:main']})
