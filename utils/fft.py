import numpy as np
import matplotlib.pyplot as plt
import numpy.fft as nf

sumstart = 20000
sumend = 23000
varidx = 6
dgn_file = r"D:\AAA_PIC\Parser\MCL_PLYParser\src\data\vir100_25\Simulation_h\result\FieldsDgn.txt";
dst_file = "./FieldsDgn_fft.txt";
fopen=open(dgn_file,'r');
lineidx = 0;
data = []
time = []
for line in fopen:
    if (lineidx!=0):
        tmp1 = line.split();
        time.append(float(tmp1[0]));
        data.append(float(tmp1[varidx]));
    lineidx = lineidx + 1;
fopen.close();

datanum = sumend - sumstart + 1;
dtime = np.zeros(datanum, dtype=np.float64)
ddata = np.zeros(datanum, dtype=np.float64)

for i in range(0, datanum):
    index = sumstart + i;
    dtime[i] = float(time[index]);
    ddata[i] = float(data[index]);

DtAvg = 0.0;
DtNum = 0.0;
for i in range(1, datanum):
    DtAvg = DtAvg + (dtime[i] - dtime[i-1]);
    DtNum = DtNum + 1;
DtAvg = float(DtAvg / DtNum);

plt.figure('FFT', facecolor='lightgray')
plt.subplot(121)
plt.title('Time Domain', fontsize=16)
plt.grid(linestyle=':')
plt.plot(dtime, ddata, label=r'$ddata$')
# 针对方波y做fft
comp_arr = nf.fft(ddata)
y2 = nf.ifft(comp_arr).real
plt.plot(dtime, y2, color='orangered', linewidth=5, alpha=0.5, label=r'$ddata$')
# 绘制频域图形
plt.subplot(122)
#freqs = nf.fftfreq(ddata.size, dtime[1] - dtime[0])
freqs = nf.fftfreq(ddata.size, DtAvg)

pows = np.abs(comp_arr)  # 复数的模
plt.title('Frequency Domain', fontsize=16)
plt.grid(linestyle=':')
plt.plot(freqs[freqs > 0], pows[freqs > 0], color='orangered', label='frequency')

fopenfft=open(dst_file,'w');
datax = freqs[freqs > 0];
datay = pows[freqs > 0];
for idx in range(np.size(datax)):
    fopenfft.write(str(datax[idx])+"       "+str(datay[idx])+"\n");
fopenfft.close();

plt.legend()
plt.savefig('fft.png')
plt.show()
