import random
import string


def random_upper_code(length):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choices(alphabet, k=length))

