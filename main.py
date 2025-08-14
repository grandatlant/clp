#!/usr/bin/env -S python3
# -*- coding = utf-8 -*-
"""combatlogparse main module.
"""

import sys

import logging
log = logging.getLogger(__name__)

from dotenv import load_dotenv
from pydantic import BaseModel

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt



##  MAIN ENTRY POINT
def main(args=None):
    print(args)
    
    return 0

if __name__ == '__main__':
    assert sys.prefix != sys.base_prefix, 'Running outside venv!'
    sys.exit(main(sys.argv))
