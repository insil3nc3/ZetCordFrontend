import numpy as np
from av import AudioFrame
from fractions import Fraction
import logging

logging.basicConfig(level=logging.DEBUG)
data = np.zeros((1, 960), dtype=np.int16)
frame = AudioFrame.from_ndarray(data, format='s16', layout='mono')
frame.sample_rate = 48000
frame.time_base = Fraction(1, 48000)
logging.debug(f"Frame: format={frame.format}, layout={frame.layout}, samples={frame.samples}")