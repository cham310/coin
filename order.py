from upbit import Upbitpy
from model import Screening
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import telepot
import pickle
import os



scr = Screening()

while True:
    now = datetime.now()
    if now.minute % 30 == 0:
        scr.send_msg()