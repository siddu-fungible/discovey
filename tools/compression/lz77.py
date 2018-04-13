import logging
import sys
###################################################################################
# Coding
import pylzma


def encode(stream):
    """Encode the input stream using a hard-coded window size"""
    window = ""  # Buffer of last MAX_WINDOW_SIZE symbols
    s = ""  # Suffix of stream to be coded
    n = 0  # Index into stream
    code_data = []

    while n < len(stream):
        logging.info("----- n = " + str(n) + " | window = " + window + " | s = " + s)
        x = stream[n]

        logging.info("READ: x = " + x)

        if (window + s).find(s + x) < 0:
            # Suffix extended by x could not described by previously seen symbols.
            if s == "":
                # No previously seen substring so code x and add it to window
                # code_symbol(x)
                code_data.append(x)
                window = grow(window, x)
            else:
                # Find number of symbols back that s starts
                i = lookback(window, s)
                code_data.append(code_pointer(i, s))
                window = grow(window, s)

                # Reset suffix and push back last symbol
                s = ""
                n -= 1
        else:
            # Append the last symbol to the search suffix
            s += x

        # Increment the stream index
        n += 1

    # Stream finished, flush buffer
    logging.info("READ: <END>")
    if s != "":
        i = lookback(window, s)
        code_data.append(code_pointer(i, s))
    return code_data


def code_symbol(x):
    """Write a single symbol out"""
    print "(0," + x + ")"


def code_pointer(i, s):
    """Write a pointer out"""
    return len(s), i


MAX_WINDOW_SIZE = 32<<10


def lookback(window, s):
    """Find the lookback index for the suffix s in the given window"""
    return len(window) - (window + s).find(s)


def grow(window, x):
    """Update a window by adding x and keeping only MAX_WINDOW most recent symbols"""
    window += x
    if len(window) > MAX_WINDOW_SIZE:
        window = window[-MAX_WINDOW_SIZE:]  # Keep MAX_WINDOW last symbols

    return window


if __name__ == "__main__":
    # Uncomment line below to show encoding state
    # logging.basicConfig(level=logging.INFO)
    input_string = "abcdefghijklmnoabcdefghijklmnoabcdefghijklmno"
    print input_string
    print encode(input_string)
