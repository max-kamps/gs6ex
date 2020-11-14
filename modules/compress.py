import pickle
import pickletools
import lzma


char_ranges = {
    15: (
        'ҠӀ', 'ԀԠ', 'ڀۀ', 'ݠޠ', '߀ߠ', 'ကဠ', 'ႠჀ', 'ᄀᅠ', 'ᆀᆠ', 'ᇠቀ',
        'በኀ', 'ዠጀ', 'ጠፀ', 'ᎠᏠ', 'ᐠᙠ', 'ᚠᛠ', 'កហ', 'ᠠᡠ', 'ᣀᣠ', 'ᦀᦠ',
        '᧠ᨀ', 'ᨠᩀ', 'ᯀᯠ', 'ᰀᰠ', 'ᴀᴠ', '⇠∀', '⋀⋠', '⍀⏠', '␀␠', '─❠',
        '➀⟀', '⠀⦀', '⦠⧀', '⨠⩠', '⪀⫀', '⫠⭠', 'ⰀⰠ', 'ⲀⳠ', 'ⴀⴠ', 'ⵀⵠ',
        '⺠⻠', '㇀㇠', '㐀䶠', '䷀鿀', 'ꀀꒀ', '꒠꓀', 'ꔀꘀ', 'ꙀꙠ', 'ꚠꛠ', '꜀Ꝡ',
        'ꞀꞠ', 'ꡀꡠ',
    ),
    7: ('ƀƠ', 'ɀʠ'),
}

encode_lut = {}
decode_lut = {}

for num_of_bits, ranges in char_ranges.items():
    charset = []

    for start, stop in ranges:
        for point in range(ord(start), ord(stop)):
            charset.append(chr(point))

    encode_lut[num_of_bits] = charset
    
    for z, char in enumerate(charset):
        decode_lut[char] = (num_of_bits, z)


def base32768_encode_bytes(data):
    digits = []

    bit_buffer = 0
    num_bits = 0

    for byte in data:
        bit_buffer = (bit_buffer << 8) | byte
        num_bits += 8
        
        while num_bits >= 15:
            num_bits -= 15
            digits.append(encode_lut[15][bit_buffer >> num_bits])
            bit_buffer &= ((1 << num_bits) - 1)

    if num_bits > 0:
        bits_to_pad_to = 7 if num_bits <= 7 else 15
        missing_bits = bits_to_pad_to - num_bits
        digits.append(encode_lut[bits_to_pad_to][(bit_buffer << missing_bits) | ((1 << missing_bits) - 1)])

    return ''.join(digits)

def base32768_decode_bytes(data):
    output = bytearray()

    bit_buffer = 0
    num_bits = 0

    for char in data:
        digit_bits, digit = decode_lut[char]
        
        bit_buffer = (bit_buffer << digit_bits) | digit
        num_bits += digit_bits

        while num_bits >= 8:
            num_bits -= 8
            output.append(bit_buffer >> num_bits)
            bit_buffer &= ((1 << num_bits) - 1)

    # Check the padding is all that's left
    if bit_buffer != ((1 << num_bits) - 1):
        raise ValueError(f'Invalid base32768 string (invalid padding)')

    return output

lzma_filter_chain = [{'id': lzma.FILTER_LZMA2, 'preset': 9}]

def base32768_encode(obj):
    pickled = pickletools.optimize(pickle.dumps(obj, protocol=5))
    compressed = lzma.compress(pickled, format=lzma.FORMAT_RAW, filters=lzma_filter_chain)
    return base32768_encode_bytes(compressed)

def base32768_decode(data):
    decoded = base32768_decode_bytes(data)
    decompressed = lzma.decompress(decoded, format=lzma.FORMAT_RAW, filters=lzma_filter_chain)
    return pickle.loads(decompressed)
