import tensorflow as tf
# from google.colab import files
from scipy.misc import imsave
import matplotlib.pyplot as plt
import numpy as np
import PIL
from PIL import Image
import dnnlib as dnnlib
import dnnlib.tflib as tflib
import config as config
import pickle
import os  
import sample as sp 
import util as ut


device_name = tf.test.gpu_device_name()
if device_name != '/device:GPU:0':
  raise SystemError('GPU device not found')
print('Found GPU at: {}'.format(device_name))

# Initialize TensorFlow
tflib.init_tf()

# Load pre-trained network.
url = 'https://drive.google.com/uc?id=1MEGjdvVpUsu1jB4zrXZN7Y4kBBOzizDQ' # karras2019stylegan-ffhq-1024x1024.pkl
with dnnlib.util.open_url(url, cache_dir=config.cache_dir) as f:
    _G, _D, Gs = pickle.load(f)
    # _G = Instantaneous snapshot of the generator. Mainly useful for resuming a previous training run.
    # _D = Instantaneous snapshot of the discriminator. Mainly useful for resuming a previous training run.
    # Gs = Long-term average of the generator. Yields higher-quality results than the instantaneous snapshot.

def random_sample(Gs):
    # Pick latent vector.
    rnd = np.random.RandomState(5)
    latents = rnd.randn(1, Gs.input_shape[1])
    print(latents.shape)

    # Generate image.
    fmt = dict(func=tflib.convert_images_to_uint8, nchw_to_nhwc=True)


    with tf.device('/gpu:0'):
        images = Gs.run(latents, None, truncation_psi=0.7, randomize_noise=True, output_transform=fmt)

    # Save image.
    os.makedirs(config.result_dir, exist_ok=True)
    png_filename = os.path.join(config.result_dir, 'random.png')
    PIL.Image.fromarray(images[0], 'RGB').save(png_filename)
    print("Done")
    
def z_sample(Gs, z):
    #z.shape = (1,512)
    
    # Generate image.
    fmt = dict(func=tflib.convert_images_to_uint8, nchw_to_nhwc=True)


    images = Gs.run(z, None, truncation_psi=0.7, randomize_noise=True, output_transform=fmt)

    # Save image.
    os.makedirs(config.result_dir, exist_ok=True)
    png_filename = os.path.join(config.result_dir, 'z_image.png')
    PIL.Image.fromarray(images[0], 'RGB').save(png_filename)
    return images[0]

def random_vector():
    return np.random.normal(0,1,512).reshape(1,512)

def gen_grid_exp(cur_z, exp_iter, noise_level = 1):
    noise = 0.99
    seed = np.random.randint(4000)
    np.random.seed(seed)
    noisyVecs = []
    noises = []
    noisyImages = []
    new_im = Image.new('RGB', (384,64))
    index = 0
    print("Generating grid of noisy images ...")
    for i in range(0,384,64):
        np.random.seed(np.random.randint(4362634))
        noise_val = (random_vector() * noise_level) #most noise added
        zs = cur_z + noise_val
        zs = np.clip(zs, -5, 5)
        p_image = z_sample(zs)
        noises.append(noise_val)
        noisyVecs.append(zs)
        noisyImages.append(p_image)
        im = Image.fromarray(p_image)
        im.thumbnail((64,64))
        new_im.paste(im, (i,0))
        index += 1
        
    new_im.save("./exp" + str(experimentNum) + "/grid_" +str(exp_iter)+".png")
    plt.imshow(new_im)
    plt.draw()
    plt.pause(0.001)
    return noisyVecs, noisyImages, noises


def gen_grid_vis(original_image, first_image, ordered_images, num_trials):
    new_im = Image.new('RGB', (458, num_trials * 64 + 128))
    index = 0
    im = Image.fromarray(first_image)
    im.thumbnail((64,64))
    new_im.paste(im, (394,0))
    im = Image.fromarray(original_image)
    im.thumbnail((64,64))
    new_im.paste(im, (394,num_trials * 64 + 64))
    
    for i in range(64, 64 + num_trials * 64,64):
        for j in range(0,448,64):
            im = Image.fromarray(ordered_images[index])
            im.thumbnail((64,64))
            if j == 384:
                new_im.paste(im, (j + 10,i))
            else:
                new_im.paste(im, (j,i))
            index += 1
        
    new_im.save("./exp" + str(experimentNum) + "/data.png")

def pixel_error(image1, image2):
    difference = image1 - image2
    error = np.linalg.norm(difference)
    return error


def run(experimentNum, num_trials = 20, learning_rate = 15, noise = 0.99, alpha = 0.99):
	# Load pre-trained network.
	url = 'https://drive.google.com/uc?id=1MEGjdvVpUsu1jB4zrXZN7Y4kBBOzizDQ' # karras2019stylegan-ffhq-1024x1024.pkl
	with dnnlib.util.open_url(url, cache_dir=config.cache_dir) as f:
	    _G, _D, Gs = pickle.load(f)

	tflib.init_tf()

	os.mkdir("exp" + str(experimentNum))

	#Generate and save original image that you will 
	seed = 3242
	np.random.seed(19238817)

	original_z = random_vector()

	print("Generating original image ...")

	with tf.device('/GPU:0'):
		o_image = z_sample(Gs, original_z)
	imsave("./" + "exp" + str(experimentNum) + "/original.png", o_image)
	plt.imshow(o_image)
	plt.grid('off')
	plt.axis('off')

	#Keep track of experimental data
	z_vectors = [] # z vector after each iteration
	error_vals = [] # pixel error w.r.t original image after each iteration
	total_grid = []

	cur_z = random_vector()
	with tf.device('/GPU:0'):
		r_image = z_sample(Gs, cur_z)
	first_image = r_image
	imsave("./exp" + str(experimentNum) + "/reconstructed_"  +str(1)+".png", r_image)
	error_vals.append(pixel_error(r_image, o_image))
	plt.imshow(r_image)
	plt.draw()
	plt.pause(0.001)

	for exp_iter in range(1,num_trials + 1):
	  
	    print("Input value between 1-3 for desired noise level")
	    print("1: Least Noise - 3: Most Noise")
	    raw_noise_level = input()
	    if int(raw_noise_level) == 1:
	        noisyVecs, noisyImages, noises = gen_grid_exp(cur_z, exp_iter, 0.5)
	    elif int(raw_noise_level) == 2:
	        noisyVecs, noisyImages, noises = gen_grid_exp(cur_z, exp_iter, 1.3)
	    else:
	        noisyVecs, noisyImages, noises = gen_grid_exp(cur_z, exp_iter, 8)
	    temp_grid =  [0] * 6 
	    
	    # use commas to separate ranking scores 
	    raw_rankings = input() 
	    rankings = np.array([int(x) for x in raw_rankings.split(",")])
	    
	    #for visualization purposes 
	    for i,r in enumerate(rankings):
	        temp_grid[r - 1] = noisyImages[i]
	    total_grid += temp_grid
	    
	    rankings = (rankings - rankings.mean())/rankings.std()
	    noisyVecsSum = np.zeros(512).reshape(1,512)
	    for i,r in enumerate(rankings):
	        noisyVecsSum += r * (noises[i])

	    #update step 
	    learning_rate = (alpha**(exp_iter/2))
	    cur_z = cur_z + learning_rate * (noisyVecsSum/(6 * noise))
	    
	    
	    print("Generating reconstructed image ...")
	    with tf.device('/gpu:0'):
	    	r_image = z_sample(Gs,cur_z)
	    total_grid.append(r_image)
	    z_vectors.append(cur_z)
	    imsave("./exp" + str(experimentNum) + "/reconstructed_"  +str(exp_iter + 1)+".png", r_image)
	    error_vals.append(pixel_error(r_image, o_image))
	    print(error_vals)
	    plt.imshow(r_image)
	    plt.draw()
	    plt.grid('off')
	    plt.axis('off')
	    plt.pause(0.001)
	    
	gen_grid_vis(o_image, first_image, total_grid, num_trials)


if __name__ == "__main__":
	run(12)