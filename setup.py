from setuptools import setup

setup(name='rayvens',
      packages=[
          'rayvens', 'rayvens.core', 'rayvens.core.camel_anywhere',
          'rayvens.core.utils'
      ],
      version='0.1',
      description='Ray eventing',
      license='apache-2.0',
      author='Rayvens authors',
      author_email='tardieu@us.ibm.com;gheorghe-teod.bercea@ibm.com',
      url='https://github.ibm.com/solsa/rayvens')
