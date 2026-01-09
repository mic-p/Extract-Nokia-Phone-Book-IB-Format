#!/usr/bin/env python3
"""
Nokia old-style phonebook (.ib) binary reader.

This script parses a Nokia phonebook binary file (e.g. phonebook.ib),
extracting contact names and phone numbers.

The binary format is partially reverse-engineered and contains:
- fixed-size blocks (200 bytes)
- records starting with 8 consecutive 0xFF bytes
- BCD-like encoded phone numbers with swapped nibbles
"""

import sys
import string

# Allowed characters for contact names
CHR_OK = string.digits + string.ascii_letters + " "

# Some italian mobile phone prefix. Modify them from your need
prefixes = (
    "320", "327", "324", "328", "329",
    "331", "333", "334", "335", "336", "337", "338", "339",
    "340", "342", "343", "344", "345", "346", "347", "348", "349",
    "351", "350",
    "366", "371", "370", "375",
    "380", "388", "389", "390", "391", "392", "393",

)

class NokiaPhonebook325:
    """
    Nokia 3xx series phonebook reader.

    The implementation intentionally preserves some legacy quirks
    of the original format and parsing logic, in order to ensure
    identical output compared to the original script.
    """

    BLOCK_SIZE = 200

    def __init__(self, filename):
        """
        Open the binary phonebook file and read the first block.
        """
        self.fh = open(filename, "rb")
        self.block = self.fh.read(self.BLOCK_SIZE)
        self.bytes_read = len(self.block)

    # ------------------------------------------------------------------

    @staticmethod
    def _hex_block(block):
        """
        Return a concatenated hexadecimal string representation
        of the given byte block.
        """
        return "".join(hex(b) for b in block)

    # ------------------------------------------------------------------

    def _read_name(self):
        """
        Extract the contact name.

        Name field:
        - offset: 68
        - length: 80 bytes

        Non-alphanumeric characters are ignored.
        """
        start = 68
        end = start + 80
        raw = self.block[start:end]

        name = ""
        for b in raw:
            c = chr(b)
            if c in CHR_OK:
                name += c

        return name.strip()

    # ------------------------------------------------------------------

    def _read_number(self):
        """
        Extract the phone number from the current block.

        Number field:
        - offset: 24
        - length: 30 bytes

        The number is encoded in a semi-BCD format with swapped nibbles.
        Padding and invalid bytes are handled exactly like the
        original legacy implementation.
        """
        start = 24
        end = start + 30
        raw = self.block[start:end]

        num = ""

        for b in raw:
            # Equivalent to: v = hex(ord(chr(b)))[2:]
            v = hex(b)[2:]

            # Add leading zero ONLY if this is not the first digit group
            if num and len(v) == 1:
                v = "0" + v

            # Skip invalid byte representations
            if len(v) != 2:
                continue

            # Swap nibbles (BCD decoding)
            num += v[1] + v[0]

        return num.strip()

    # ------------------------------------------------------------------

    @staticmethod
    def _clean_number(prefix, num):
        """
        Extract and clean a phone number starting from a given prefix.
        """
        idx = num.find(prefix)
        num = num[idx:idx + 10]
        return "".join(c for c in num if c.isdigit())

    # ------------------------------------------------------------------

    def _normalize_number(self, num):
        """
        Normalize the phone number using known prefixes.

        The logic preserves the original behavior:
        1. Check prefix at the beginning
        2. Check prefix after an offset of 30 characters
        3. Check prefix anywhere in the string
        """

        # 1) Prefix at the beginning
        for p in prefixes:
            if num.startswith(p):
                return self._clean_number(p, num)

        # 2) Prefix after offset 30 (legacy quirk)
        num2 = num[30:]
        for p in prefixes:
            if num2.startswith(p):
                return self._clean_number(p, num2)

        # 3) Prefix anywhere in the string
        for p in prefixes:
            if p in num:
                return self._clean_number(p, num)

        return num

    # ------------------------------------------------------------------

    def _advance(self, nbytes):
        """
        Advance the internal buffer by n bytes, reading from file.
        """
        self.block = self.block[nbytes:] + self.fh.read(nbytes)
        self.bytes_read += nbytes

    # ------------------------------------------------------------------

    def run(self):
        """
        Main parsing loop.
        """
        while self.block:
            if len(self.block) < self.BLOCK_SIZE:
                self.block += self.fh.read(self.BLOCK_SIZE - len(self.block))

            if not self.block:
                break

            # Look for record start marker: 8 consecutive 0xFF bytes
            if self.block[0] != 0xFF:
                self._advance(1)
                continue

            if self._hex_block(self.block[:8]) != "0xff" * 8:
                self._advance(1)
                continue

            name = self._read_name()
            number = self._normalize_number(self._read_number())

            print(f"{name};{number}")

            # Skip over the current record
            self._advance(30)

        self.fh.close()


# ----------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: read_pb.py phonebook.ib")
        sys.exit(1)

    NokiaPhonebook325(sys.argv[1]).run()
