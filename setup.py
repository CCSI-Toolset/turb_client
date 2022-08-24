##########################################################################
# $Id: setup.py 10252 2016-04-27 21:26:30Z ksb $
# Joshua R. Boverhof, LBNL
# See LICENSE.md for copyright notice!
#
#   $Author: ksb $
#   $Date: 2016-04-27 14:26:30 -0700 (Wed, 27 Apr 2016) $
#   $Rev: 10252 $
#
###########################################################################
import os
import subprocess
#from ez_setup import use_setuptools
from setuptools import setup
# use_setuptools()

_url = "https://github.com/CCSI-Toolset/turb_client"
# Update version from latest git tags.
# Create a version file in the root directory
version_py = os.path.join(os.path.dirname(__file__), 'turbine/version.py')
try:
    git_describe = subprocess.check_output(
        ["git", "describe", "--tags", "--dirty"]).rstrip().decode('utf-8')
    version_msg = "# Managed by setup.py via git tags.  **** DO NOT EDIT ****"
    with open(version_py, 'w') as f:
        f.write(version_msg + os.linesep + "__version__='" +
                git_describe.split("-")[0] + "'")
        f.write(os.linesep + "__release__='" + git_describe + "'" + os.linesep)

except Exception as e:
    # If there is an exception, this means that git is not available
    # We will used the existing version.py file
    pass

try:
    with open(version_py) as f:
        code = compile(f.read(), version_py, 'exec')
        exec(code)
except:
    __release__ = None


setup(
    name="TurbineClient",
    version=__release__,
    license="See LICENSE.md",
    packages=['turbine', 'turbine.commands'],
    description="Turbine Science Gateway Client",
    author="Joshua Boverhof",
    author_email="jrboverhof@lbl.gov",
    maintainer="Joshua Boverhof",
    maintainer_email="jrboverhof@lbl.gov",
    url=_url,
    long_description="For additional information, please see " + _url,
    setup_requires=[],
    dependency_links=[],

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Natural Language :: English",
        "Operating System :: POSIX"
    ],

    scripts=["scripts/turbine_job_script",
             "scripts/turbine_application_list",
             "scripts/turbine_simulation_list",
             "scripts/turbine_simulation_update",
             "scripts/turbine_simulation_create",
             "scripts/turbine_simulation_delete",
             "scripts/turbine_simulation_get",
             "scripts/turbine_session_list",
             "scripts/turbine_session_create",
             "scripts/turbine_session_append",
             "scripts/turbine_session_kill",
             "scripts/turbine_session_start",
             "scripts/turbine_session_stop",
             "scripts/turbine_session_status",
             "scripts/turbine_session_stats",
             "scripts/turbine_session_results",
             "scripts/turbine_session_delete",
             "scripts/turbine_session_graphs",
             "scripts/turbine_consumer_log",
             "scripts/turbine_consumer_list"
             ],
    install_requires=[
        "python-dateutil >= 2.5"
    ],
    extras_require={
        "graphs": ["rpy2", ],
    },

    # sdist
    exclude_package_data={'': ['tools']},
)
