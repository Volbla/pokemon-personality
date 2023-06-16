from implementation import *
from random import randrange
from time import perf_counter as now

def newid(): return randrange(2**32)
trainer_id = newid()


def main():
	global trainer_id

	then = now()
	for n in range(10_000_000):
		if now() > then + 2:
			print(n)
			then = now()

		if n % 100_000 == 0:
			trainer_id = newid()

		try:
			test_function()
		except AssertionError as e:
			print(n)
			raise e


def test_function():
	g_thresh = Gender_threshold.Equal

	# Any personality
	personality = newid()

	# Only shiny
	# while personality := newid():
	# 	if is_shiny(personality, trainer_id): break

	old_nature = personality % 25
	wanted_nature = (old_nature + randrange(24)) % 25


	new_personality = change_nature(wanted_nature, personality)

	assert(nature(new_personality) == nature(wanted_nature))
	assert(gender(personality, g_thresh) == gender(new_personality, g_thresh))
	assert(is_shiny(personality, trainer_id) == is_shiny(new_personality, trainer_id))

	# Print text for curiosity.
	# print_all_qualities(personality)
	# print(nature(wanted))
	# print_all_qualities(new_personality)
	# print()
	# sleep(2.5)


def change_nature(wanted_nature:int, personality:int) -> int:
	"""Changing the nature of a pokemon while preserving both shininess and gender.
	This relies on Emerald Rogue's 655 ( ~1/100 ) shiny chance.

	Shininess depends on a 16 bit value. Since 655 is larger than one byte
	the value of the lower byte only matters when the higher byte is 00000010.
	This means we have a lot of freedom to change the lower byte without
	changing shininess.

	The shiny value depends on the xor of the upper and lower halves of the
	personality. The lower byte of the shiny value is thus the xor of the
	personality's second and fourth bytes. Gender depends only on the
	fourth byte. The nature is equal to the full personality mod 25.

	By changing only the second byte in the personality we can change
	the nature without even touching the gender. By keeping track of
	edge cases we can also guarantee preserved shininess.

	Does not preserve: Unown's letter, Wurmple's evolution, Spinda's spots.
	"""

	# Bit shifting modular values will shuffle around their order.
	# Making a map from the desired overall value to the corresponding bit shifted value.
	forward = [(n << 16) % 25 for n in range(25)]
	backward = [forward.index(n) for n in range(25)]

	# The six lowest bits of the second highest byte in the personality.
	# If these overflow the shiny value might change significantly.
	dangerous_bits = personality & (63 << 16)	# 00000000 00111111 00000000 00000000
	overflow_threshold = (64 - 25) << 16
	might_overflow = dangerous_bits > overflow_threshold

	# Despite the first precaution the shiny value could still exceed 655.
	# This is prevented by making sure the byte's highest bit is zero in the shiny value.
	# If this bit is zero AND the 6 lowest bits don't increase by too much,
	# a shiny personality will never become non-shiny.
	problem_bit = 1 << 7						# 00000000 10000000
	the_problem = shiny_value(personality, trainer_id) & problem_bit

	new_personality = personality ^ (the_problem << 16)

	# Difference needed for the new nature.
	# Adding 25 to not underflow the unsigned int.
	needed = (25 + wanted_nature - (new_personality % 25)) % 25

	# The bit-shifted counterpart.
	new_personality += backward[needed] << 16

	if might_overflow:
		new_personality -= 25 << 16

	# Messing with the second lowest byte in case we turned a non-shiny shiny.
	# I'm not convinced this is 100% reliable, but it hasn't broken in any of my tests.
	if is_shiny(new_personality, trainer_id) and not is_shiny(personality, trainer_id):
		new_personality += 25 << 10

	return new_personality


# Vectorized testing in numpy.
import numpy as np

def test_all_shinies():
	starts = all_shiny_personalities().astype(np.uint32)

	for nature in range(25):
		results = change_nature_vectorized(nature, starts)
		assert(np.all(results % 25 == nature))
		print(np.count_nonzero(is_shiny(results, trainer_id)) / (655*65536))


def change_nature_vectorized(wanted, personality):
	# Not updated. May turn non-shinies shiny.

	forward = np.array([(n << 16) % 25 for n in range(25)], dtype = np.uint32)
	backward = np.argsort(forward).astype(np.uint32)

	dangerous_bits = personality & (63 << 16)
	overflow_threshold = (64 - 25) << 16
	might_overflow = (dangerous_bits > overflow_threshold)

	problem_bit = 1 << 7
	the_problem = shiny_value(personality, trainer_id) & problem_bit != 0

	new_personailty = personality.copy()
	new_personailty[the_problem] ^= problem_bit << 16

	needed = (25 + wanted - (new_personailty % 25))
	new_personailty += backward[needed % 25] << 16
	new_personailty[might_overflow] -= 25 << 16

	# For testing. Printing out a personality that lost its shininess.
	shiny_mask = is_shiny(new_personailty, trainer_id)
	if not np.all(shiny_mask):
		for p in (personality, new_personailty):
			example = p[~shiny_mask][0]
			prant(example)
			prant(shiny_value(example, trainer_id), bits=16)

	return new_personailty


def count_specifics():
	shinies = all_shiny_personalities()
	very_specific = np.all([
		shinies % 25 == randrange(25),	# Specific ability
		shinies & q4 < 31,				# Rare female
		number_unown_letter(shinies) == randrange(28),	# type: ignore Specific Unown
		number_wurmple_evolution(shinies)	# type: ignore
	], axis=0)
	print(np.count_nonzero(very_specific))


def all_shiny_personalities():
	shiny_options = np.arange(655, dtype=np.uint32)

	t1 = (trainer_id & h1) >> 16
	t2 = (trainer_id & h2)
	trainer16 = t1 ^ t2
	person16 = shiny_options ^ trainer16

	lower_options = np.arange(2**16, dtype=np.uint32)
	upper_options = lower_options[None,:] ^ person16[:,None]

	return upper_options << 16 | lower_options


# Some utility.

def binary(value:int, bits:int=32) -> str:
	"""Pretty string of the binary form of an integer."""

	bin_string = f"{value:032b}"[32-bits:]
	byte_list = [bin_string[i:i+8] for i in range(0, bits, 8)]
	return " ".join(byte_list)


def prant(*objects, bits:int=32):
	"""Print multiple things on separate lines,
	using pretty binary for ints."""

	for o in objects:
		if isinstance(o, int):
			print(binary(o, bits))
		else:
			print(o)


def print_all_qualities(personality):
	from functools import partial

	threshold = Gender_threshold.Equal
	is_shiny2 = partial(is_shiny, trainer_id=trainer_id)
	gender2 = partial(gender, species_threshold = threshold)

	for function in (nature, is_shiny2, gender2, unown_letter, wurmple_evolution):
		print(str(function(personality)).ljust(8), end=" ")
	print()


if __name__ == "__main__":
	print()
	main()
