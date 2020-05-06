import numpy as np

# define normalized 2D gaussian
def gaus2d(x=0, y=0, mx=0, my=0, sx=1, sy=1):
    return 1. / (2. * np.pi * sx * sy) * np.exp(-((x - mx)**2. / (2. * sx**2.) + (y - my)**2. / (2. * sy**2.)))

x = np.linspace(-5, 5, 128)
y = np.linspace(-5, 5, 128)
x, y = np.meshgrid(x, y) # get 2D variables instead of 1D
z = gaus2d(x, y)

# normalize to 0, 255
z /= np.max(z)

z *= 255

z = z.astype(np.uint8)
out = np.full((128, 128, 4), 255, dtype=np.uint8)
out[:, :, 3] = z # only alpha channel should be fading


import matplotlib.pyplot as plt
from PIL import Image
fig, ax = plt.subplots()
ax.imshow(out)
ax.set_facecolor("lightslategray")
fig.show()

im = Image.fromarray(out)
im.save('particle.png')
