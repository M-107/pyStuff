let_between = "X"
let_replace = "Q"
let_instead = "XINSX"
let_space = "XSPAX"
let_end = "XENDX"
let_end_alt = "GENDG"

# TODO: Decrypting is weird and sometimes fails, probably needs to be done completely differently


def inputs():
    while True:
        print("\n---PLAYFAIR CYPHER---")
        mode_ed = input(" 1 for encrypting\n 2 for decrypting\n")
        if mode_ed == "0":
            exit()
        elif mode_ed == "1":
            mode_ed = 1
            break
        elif mode_ed == "2":
            mode_ed = -1
            break
        else:
            print(
                "Please input only '1' or '2'.\nYou can also close the scrip by inputting '0'.\n"
            )

    while True:
        input_text = input("\nInput text: ")
        if (x.isalpha() or x.isspace() for x in input_text):
            break
        else:
            print(
                "Please input only letters from the english alphabet with no special symbols."
            )

    while True:
        key = input("Key: ")
        if key.isalpha() == True and (5 < len(key) < 25):
            break
        else:
            print(
                "Please input only 5-25 letters from the english alphabet with no special symbols and no spaces."
            )

    return (mode_ed, input_text, key)


def make_table(key):
    # Sort the key string alphabetically and replace repeating letters
    key_new = "".join(sorted(set(key), key=key.index)).upper()
    # Remove one letter from the alphabet to make it have 25 symbols
    alphabet_def = key_new + "ABCDEFGHIJKLMNOPQRSTUVWXYZ".replace(let_replace, "")
    # Make a new alphabet with the key_new letters first and then alphabet with no repeats
    alphabet = "".join(sorted(set(alphabet_def), key=alphabet_def.index))
    alphabet_list = [x for x in alphabet]
    # Turn the alphabet indo a 5x5 array
    table = [
        alphabet_list[i * 5 : (i + 1) * 5]
        for i in range((len(alphabet_list) + 5 - 1) // 5)
    ]
    return table


def pre_encrypt(input_text):
    # Replace space and the removed letter with alternatives
    text = input_text.replace(" ", let_space).upper()
    text = text.replace(let_replace, let_instead)
    text_list = [x for x in text]
    # Place a filler between neighbouring letters
    for i in range(0, len(text_list) - 1):
        if text_list[i] == text_list[i + 1]:
            text_list.insert(i + 1, let_between)
    # Add a filler at the end if the number of letters is not even
    if len(text_list) % 2 != 0:
        if text_list[-1] != let_end[0]:
            for i in let_end + "FI":
                text_list.append(i)
        else:
            for i in let_end_alt + "SE":
                text_list.append(i)
    output_text = "".join(text_list)
    return output_text


def post_decryp(input_text):
    if input_text[-7:] == "XENDXFI" or input_text[:-7] == "GENDGSE":
        text_no_end = input_text[:-7]
    else:
        text_no_end = input_text

    remove_indices = []
    for i in range(1, len(text_no_end) - 1):
        if text_no_end[i - 1] == text_no_end[i + 1] and text_no_end[i] == let_between:
            remove_indices.append(i)

    text_neighbours = ""
    for i in range(len(text_no_end)):
        if i not in remove_indices:
            text_neighbours = text_neighbours + text_no_end[i]

    text_with_26th = text_neighbours.replace(let_instead, let_replace)
    text_with_spaces = text_with_26th.replace(let_space, " ")
    return text_with_spaces


# Get the position of a letter in a table as X and Y coordinates
def find_letter(let, table):
    for x, i in enumerate(table):
        if let in i:
            y = i.index(let)
            break
    return x, y


def encrypt(text, table, mode):
    text_list = [x for x in text]
    # Make a list of two letter strings from the input text
    split_text = [x + text_list[n + 1] for n, x in enumerate(text_list[:-1])][::2]
    text_out = ""
    # Get the index of the letters in each pair from prepared list of double letters
    for i in split_text:
        x1 = find_letter(i[0], table)[0]
        y1 = find_letter(i[0], table)[1]
        x2 = find_letter(i[1], table)[0]
        y2 = find_letter(i[1], table)[1]
        # If the letters are horizontally or vertically aligned in the table, move them by one
        if x1 == x2:
            n1 = table[x1][(y1 + mode) % 5]
            n2 = table[x2][(y2 + mode) % 5]
        elif y1 == y2:
            n1 = table[(x1 + mode) % 5][y1]
            n2 = table[(x2 + mode) % 5][y2]
        # If they aren't, use letters from the remaining two corners of the rectangle their boundary would make
        else:
            n1 = table[x1][y2]
            n2 = table[x2][y1]
        text_out += n1 + n2
    return text_out


def playfair(mode, text, key):
    table = make_table(key)
    if mode == 1:
        encrypt_prerp = pre_encrypt(text)
        text_out = encrypt(encrypt_prerp, table, mode)
    else:
        decrypt_prep = encrypt(text, table, mode)
        text_out = post_decryp(decrypt_prep)
    return text_out


def main():
    while True:
        mode_encrypt, input_text, key = inputs()
        return_text = playfair(mode_encrypt, input_text, key)
        print(f"\n-------------------------{'-'*len(return_text)}")
        print(f" The resulting text is: {return_text}")
        print(f"-------------------------{'-'*len(return_text)}")


if __name__ == "__main__":
    main()
