from setuptools import setup

setup(
    name='thewife',
    version='0.2.3',
    description='Trading bot that reacts to optimized indicator',
    packages=['thewife'],
    install_requires=[
        'pyyaml', 'ccxt', 'attr', 'tenacity', 'logzero', 'hyperopt', 'pyti',
        'pandas', 'numpy', 'networkx==1.11', 'pyfiglet', 'notifiers'
    ],
    entry_points={'console_scripts': ['wife = thewife.__main__:main']})
