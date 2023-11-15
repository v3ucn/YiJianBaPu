from scipy.io import wavfile
import noisereduce as nr
# load data
rate, data = wavfile.read("./output/test/vocals.wav")
# perform noise reduction
reduced_noise = nr.reduce_noise(y=data, sr=rate)
wavfile.write("./output/test/vocals.wav", rate, reduced_noise)