from enum import Enum, auto

# Byte masks (quarters).
q4 = 255
q3 = q4 << 8
q2 = q3 << 8
q1 = q2 << 8
# Double byte masks (halves).
h1 = q1 | q2
h2 = q3 | q4

class Gender(Enum):
	Male = auto()
	Female = auto()
	Genderless = auto()

	def __str__(self) -> str:
		return self.name

class Gender_threshold(Enum):
	Allmale = 0
	Mostmale = 31
	Moremale = 63
	Equal = 127
	Morefemale = 191
	Mostfemale = 225
	Allfemale = 254
	Genderless = 255

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ!?"
NATURES = (
	"Hardy", "Lonely", "Brave", "Adamant", "Naughty",
	"Bold", "Docile", "Relaxed", "Impish", "Lax",
	"Timid", "Hasty", "Serious", "Jolly", "Naive",
	"Modest", "Mild", "Quiet", "Bashful", "Rash",
	"Calm", "Gentle", "Sassy", "Careful", "Quirky"
)
SHINY_CHANCE = 655


def nature(personality:int) -> str:
	return NATURES[personality % 25]


def is_shiny(personality:int, trainer_id:int) -> bool:
	"""Xor the upper and lower halves of both personality and trainer id."""

	p1 = (personality & h1) >> 16
	p2 = (personality & h2)
	t1 = (trainer_id & h1) >> 16
	t2 = (trainer_id & h2)

	return p1 ^ p2 ^ t1 ^ t2 < SHINY_CHANCE


def gender(personality:int, species_threshold:Gender_threshold) -> Gender:
	"""Depends only on the last byte."""

	# Special values
	match species_threshold:
		case 255:
			return Gender.Genderless
		case 254:
			return Gender.Female
		case 0:
			return Gender.Male

	p = personality & q4
	return Gender.Male if p >= species_threshold.value else Gender.Female


def unown_letter(personality:int) -> str:
	"""Concatenates the last two bits from each byte."""

	u4 = personality & 3
	u3 = personality & 3 << 8
	u2 = personality & 3 << 16
	u1 = personality & 3 << 24

	u = u1 >> 18 | u2 >> 12 | u3 >> 6 | u4
	return LETTERS[u % 28]


def wurmple_evolution(personality:int) -> str:
	"""Depends only on the upper half."""

	p = (personality & h1) >> 16
	return "Silcoon" if p%10 <= 4 else "Cascoon"


# Just return numbers for testing.

def numbernature(personality:int) -> int:
	return personality % 25

def numbergender(personality:int, species_threshold:Gender_threshold) -> bool:
	p = personality & q4
	return p >= species_threshold.value

def number_unown_letter(personality:int) -> int:
	u4 = personality & 3
	u3 = personality & 3 << 8
	u2 = personality & 3 << 16
	u1 = personality & 3 << 24

	u = u1 >> 18 | u2 >> 12 | u3 >> 6 | u4
	return u % 28

def number_wurmple_evolution(personality:int) -> bool:
	p = (personality & h1) >> 16
	return p%10 <= 4
