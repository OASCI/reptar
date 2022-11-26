# MIT License
# 
# Copyright (c) 2022, Alex M. Maldonado
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import pytest

def pytest_sessionstart(session):  # pytest_configure(config)
    """Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    # Check that the reptar-data repo is cloned.
    reptar_data_path = './examples/reptar-data'
    reptar_data_exists = os.path.exists(reptar_data_path)
    if not reptar_data_exists:
        pytest.exit(
            4, 
            f'\nreptar-data repository not found at {reptar_data_path}'
            '\nPlease clone https://github.com/aalexmmaldonado/reptar-data'
            '\nin the reptar/examples/ directory'
        )

    # Creates a tmp directory for writing files.
    test_tmp_path = './tests/tmp'
    os.makedirs(test_tmp_path, exist_ok=True)

    # Initializes ray if available.
    try:
        import ray
    except (ModuleNotFoundError, ImportError):
        pass
    else:
        if not ray.is_initialized():
            ray.init()

def pytest_sessionfinish(session, exitstatus):
    # Shutdown ray if possible.
    try:
        import ray
    except (ModuleNotFoundError, ImportError):
        pass
    else:
        ray.shutdown()
    