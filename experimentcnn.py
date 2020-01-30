import tensorflow as tf
import imageio 
import matplotlib.pyplot as plt
import numpy as np
import PIL
from PIL import Image
import dnnlib as dnnlib
import dnnlib.tflib as tflib
import config as config
import pickle
import os  
import time 
# some handy functions to use along widgets
from IPython.display import display, Markdown, clear_output
# widget packages
import ipywidgets as widgets
from IPython.core.display import Image as Imdisplay

from keras_vggface import VGGFace
from keras.preprocessing import image
from keras_vggface import utils
import keras


# use imageio.imwrite

# Initialize TensorFlow
tflib.init_tf()


# load VGG based face classifier        
face_classifier = VGGFace(model='resnet50')


# Load pre-trained network.

url = 'http://cocosci.princeton.edu/jpeterson/temp_file_hosting/263e666dc20e26dcbfa514733c1d1f81_karras2019stylegan-ffhq-1024x1024.pkl' # karras2019stylegan-ffhq-1024x1024.pkl
# https://drive.google.com/uc?id=1MEGjdvVpUsu1jB4zrXZN7Y4kBBOzizDQ
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
	images = Gs.run(latents, None, truncation_psi=0.7, randomize_noise=True, output_transform=fmt)

	# Save image.
	os.makedirs(config.result_dir, exist_ok=True)
	png_filename = os.path.join(config.result_dir, 'random.png')
	PIL.Image.fromarray(images[0], 'RGB').save(png_filename)
	
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

white_image = z_sample(Gs, random_vector())
white_image.fill(255)

def gen_grid_exp(cur_z, exp_iter, experimentNum, original, cur_reconstructed_image, noise_level = 1):
	noise = 0.99
	seed = np.random.randint(4000)
	np.random.seed(seed)
	noisyVecs = []
	noises = []
	noisyImages = []
	imagesToDisplay = []			
	# new_im = Image.new('RGB', (1152,128))
	white_image_fixed = np.array(Image.fromarray(white_image).resize(size = (256,256), resample = False))
	index = 0
	print("Generating grid of noisy images ...")
	print("      1               2              3              4             5              6                         Reconstructed    Original")
	for i in range(0,768,128):
		np.random.seed(np.random.randint(4362634))
		noise_val = (random_vector() * noise_level) #most noise added
		zs = cur_z + noise_val
		zs = np.clip(zs, -5, 5)
		p_image = z_sample(Gs, zs)
		imagesToDisplay.append(np.array(Image.fromarray(p_image).resize(size = (256,256), resample = False)))
		noises.append(noise_val)
		noisyVecs.append(zs)
		noisyImages.append(p_image)		

	#add blank image between proposals and original
	imagesToDisplay.append(white_image_fixed)
	noisyImages.append(white_image)

	#add current reconstructed image to grid 
	imagesToDisplay.append(np.array(Image.fromarray(cur_reconstructed_image).resize(size = (256,256), resample = False)))	
	noisyImages.append(cur_reconstructed_image)

	#add original image to grid
	imagesToDisplay.append(np.array(Image.fromarray(original).resize(size = (256,256), resample = False)))
	noisyImages.append(original)

	image_grid = np.hstack(imagesToDisplay)
		
	# new_im.save("./exp" + str(experimentNum) + "/grid_" +str(exp_iter)+".png")
	# display(Imdisplay(filename = "./exp" + str(experimentNum) + "/grid_" +str(exp_iter)+".png", width=1000, unconfined=True))
	plt.figure(figsize=(20,40))
	plt.grid(False)
	plt.axis("off")
	plt.imshow(image_grid)
	# plt.imshow(new_im)
	plt.draw()
	plt.pause(0.00001)
	return noisyVecs, noisyImages, noises

def gen_images_to_rank(image_matrices, original, indexToRemove, iteration):
	white_image_fixed = np.array(Image.fromarray(white_image).resize(size = (256,256), resample = False))
	imagesToDisplay = []

	del image_matrices[indexToRemove - 1]
	for i in range(0,len(image_matrices) * 128,128):
		imagesToDisplay.append(np.array(Image.fromarray(image_matrices[int(i/128)]).resize(size = (256,256), resample = False)))

	image_grid = np.hstack(imagesToDisplay)

	plt.figure(figsize=(20,40))
	plt.grid(False)
	plt.axis("off")
	plt.imshow(image_grid)
	# plt.imshow(new_im)
	plt.draw()
	plt.pause(0.00001)



def present_noise_choices(cur_z, exp_iter, experimentNum, original, cur_reconstructed_image, noise_level = 1):
	noise = 0.99
	np.random.seed(np.random.randint(4362634))
	noisyVecs = []
	noises = []
	imagesToDisplay = []
	noisyImages = []
	# new_im = Image.new('RGB', (1792,128))
	white_image_fixed = np.array(Image.fromarray(white_image).resize(size = (256,256), resample = False))
	index = 0
	print("   Low Noise                               Medium Noise                         High Noise                            Recon.    Original")
	for i in range(0,384,128):
		noise_val = (random_vector() * 0.85) #least noise added
		zs = cur_z + noise_val
		zs = np.clip(zs, -5, 5)
		p_image = z_sample(Gs, zs)
		imagesToDisplay.append(np.array(Image.fromarray(p_image).resize(size = (256,256), resample = False)))
		noises.append(noise_val)
		noisyVecs.append(zs)
		noisyImages.append(p_image)

	imagesToDisplay.append(white_image_fixed)

	for i in range(512,896,128):
		noise_val = (random_vector() * 3.2) #most noise added
		zs = cur_z + noise_val
		zs = np.clip(zs, -5, 5)
		p_image = z_sample(Gs, zs)
		imagesToDisplay.append(np.array(Image.fromarray(p_image).resize(size = (256,256), resample = False)))
		noises.append(noise_val)
		noisyVecs.append(zs)
		noisyImages.append(p_image)

	imagesToDisplay.append(white_image_fixed)

	for i in range(1024,1408,128):
		noise_val = (random_vector() * 7) #most noise added
		zs = cur_z + noise_val
		zs = np.clip(zs, -5, 5)
		p_image = z_sample(Gs, zs)
		imagesToDisplay.append(np.array(Image.fromarray(p_image).resize(size = (256,256), resample = False )))
		noises.append(noise_val)
		noisyVecs.append(zs)
		noisyImages.append(p_image)


	#add blank image between proposals and original
	imagesToDisplay.append(white_image_fixed)
	noisyImages.append(white_image)

	#add current reconstructed image to grid 	
	imagesToDisplay.append(np.array(Image.fromarray(cur_reconstructed_image).resize(size = (256,256), resample = False)))
	noisyImages.append(cur_reconstructed_image)

	#add original image to grid
	imagesToDisplay.append(np.array(Image.fromarray(original).resize(size = (256,256), resample = False)))
	noisyImages.append(original)

	image_grid = np.hstack(imagesToDisplay)

	# new_im.save("noise_choices.png")
	# display(Imdisplay(filename = "noise_choices.png", width=1500, unconfined=True))
	plt.figure(figsize=(20,40))
	plt.grid(False)
	plt.axis('off')
	plt.imshow(image_grid)
	plt.draw()
	plt.pause(0.00001)
	return noisyVecs, noisyImages, noises


def gen_grid_vis(original_image, first_image, ordered_images, num_trials, experimentNum):
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
		
	new_im.save("./exp" + str(experimentNum) + "/data-" + str(experimentNum)+".png")

def pixel_error(image1, image2):
	difference = image1 - image2
	error = np.linalg.norm(difference)
	return error

def delete_helper(delete_array, index):
	cur_sum = 0
	for i, x in enumerate(delete_array):
		cur_sum += x
		if cur_sum == index:
			return i 

def classify(path, classifier, class_num=None):
	# feed render into classifier and get class probability outputs
	x = image.load_img(path, 
                       target_size=(224, 224))
	x = image.img_to_array(x)
	x = np.expand_dims(x, axis=0)
	x = utils.preprocess_input(x, version=2)

	class_probs = classifier.predict(x)[0]
	if class_num is None: 
		return class_probs
	else:
		return class_probs[class_num]


def run(experimentNum, num_trials = 20, learning_rate = 15, noise = 0.99, alpha = 0.99):

	os.mkdir("exp" + str(experimentNum))

	#Generate and save original image that you will 
	seed = 3244
	np.random.seed(34234)

	original_z = random_vector()

	print("Generating Image to Reconstruct ... ")

	# generate image to reconstruct during experiment
	o_image = z_sample(Gs, original_z) #need to keep this fixed according to a class in vggface 

	#Keep track of experimental data
	z_vectors = [] # z vector after each iteration
	error_vals = [] # pixel error w.r.t original image after each iteration
	total_grid = []

	cur_z = random_vector()
	
	# generate initial random image to begin experiment 
	r_image = z_sample(Gs, cur_z) 
	first_image = r_image

	clear_output()

	for exp_iter in range(1,num_trials + 1):
		print("ITERATION #", exp_iter)
		# print("Generating noise level options ... ") 
		# present_noise_choices(cur_z, exp_iter,experimentNum, o_image, r_image)
		# print("Input integer between 1 (least noise) - 3 (most noise) for desired noise level")
		
		# raw_noise_level = input()

		# clear_output()

		noisyVecs, noisyImages, noises = gen_grid_exp(cur_z, exp_iter,experimentNum, o_image, r_image, 1.5)

		copyNoisyImages = list(noisyImages)
		temp_grid =  [0] * 6  

		vggface_scores = [0] * 6

		for i in range(6):
			temp_filename = os.path.join(config.result_dir, 'x_temp.png')
			PIL.Image.fromarray(noisyImages[i], 'RGB').save(temp_filename)
			vggface_scores[i] = classify(temp_filename, face_classifier, class_num=398) #change class number to score proposals against different faces 

		vggface_scores = np.array(vggface_scores)
		vggface_scores_copy = np.copy(vggface_scores)

		#for visualization purposes 
		for i,r in enumerate(vggface_scores):
			best_scoring_image = np.argmax(vggface_scores_copy)
			vggface_scores_copy[best_scoring_image] = -100
			temp_grid[len(temp_grid) - 1 - i] = copyNoisyImages[best_scoring_image]
		total_grid += temp_grid

		vggface_scores = (vggface_scores - vggface_scores.mean())/vggface_scores.std()
		score_weighted_noise = np.zeros(512).reshape(1,512).astype('float32')
		for i,r in enumerate(vggface_scores):
			score_weighted_noise += r * (noises[i])

		# update step 
		learning_rate = (alpha**(exp_iter/2))
		cur_z = cur_z + learning_rate * (score_weighted_noise/(6 * noise))

		# create next reconstructed image
		r_image = z_sample(Gs,cur_z)
		total_grid.append(r_image)
		z_vectors.append(cur_z)

	print("Experiment Complete!")    
	gen_grid_vis(o_image, first_image, total_grid, num_trials, experimentNum)

if __name__ == "__main__":
	run(12)