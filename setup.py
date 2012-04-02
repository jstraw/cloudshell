from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


version = '0.1.0'

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    'python-novaclient >= 2.0.0',
    'python-cloudlb >= 0.3',
    'python-cloudfiles >= 1.7.9.0',
    'python-clouddns'
]


setup(name='cloudshell',
    version=version,
    description="Rackspace Cloud API Shell",
    long_description=README + '\n\n' + NEWS,
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      'Development Status :: 2 - Pre-Alpha',
      'Environment :: Console',
      'License :: OSI Approved :: GNU General Public License (GPL)',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Topic :: System :: Systems Administration'
    ],
    keywords='Rackspace Cloud Shell',
    author='Jason Straw',
    author_email='jason.straw@rackspace.com',
    url='',
    license='GPL v3',
    packages=find_packages('src'),
    package_dir = {'': 'src'},include_package_data=True,
    dependency_links = [
        'https://github.com/rackspace/python-clouddns/zipball/master#egg=python-clouddns-0.0.0'
    ],
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        'console_scripts':
            ['cloudshell=cloudshell:main']
    },
    data_files=[('/etc/profile.d', ['tools/cloudservers-aliases.sh'])]
)
