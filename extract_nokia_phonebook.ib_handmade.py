#!/usr/bin/python

import sys
import string

f = open(sys.argv[1],"rb")

chr_ok = string.digits + string.ascii_letters + " "

# Some italian mobile phone prefix. Modify them from your need

pref = ("320", "327", "324", "328", "329",
        "331", "333", "334", "335", "336", "337", "338", "339",
        "340", "342", "343", "344", "345", "346", "347", "348", "349",
        "351","350",
        "366", "371", "370","375",
        "380", "388","389","390", "391","392","393")


class ReadNokiaPB_325:
    def __init__(self):
        self.nblock = 200
        self.block = f.read(1)
        self.bread = 200


    def from_block_to_str(self, block):
        return "".join(hex(x) for x in block)

    def read_name(self):
        name = ""
        blk_name_start = 68
        blk_name_stop = blk_name_start + 80
        block_name = self.block[blk_name_start:blk_name_stop]
        for b in block_name:
            char = chr(b)
            if not char in chr_ok:
                continue
            name += char

        return name.strip()

    def read_num(self):
        num = ""
        blk_start = 24
        blk_stop = blk_start + 30
        block_num = self.block[blk_start:blk_stop]
        #print (repr(block_num))
        num = ""
        for b in block_num:
            char = chr(b)
            v = hex(ord(char))[2:]
            if num and len(v) == 1:
                v = "0" + v
            if len(v) != 2:
                continue
            try:
                num += "".join((v[1],v[0]))
            except:
                #print (repr(v))
                #print(block_num)
                raise
        #if num.startswith("e33"):
        #    print (block_num)

        return num.strip()

    def clean_num(self, pref, num):
        idx = num.find(pref)
        num = num[idx:idx+10]
        return "".join(x for x in num if x in string.digits).strip()

    def check_num(self, num):


        for p in pref:
            if num.startswith(p):
                #print (num, type(num), len(num))
                return self.clean_num(p, num)

        for p in pref:
            num2 = num[30:]
            #print (num, num2, p)
            if num2.startswith(p):
                return self.clean_num(p, num2)


        for p in pref:
            if p in num:
                #print (idx)

                num = self.clean_num(p, num)
                return num
        else:
            return num

    def block_read_n(self, nread):
        self.block = self.block[nread:] + f.read(nread)
        self.bread += nread

    def go(self):
        while self.block:
            #block = f.read(nblock)
            #print (block)
            if len(self.block) != 200:
                self.block = f.read(self.nblock - len(self.block) + 1)
                #print  (self.block)
                #print (len(block))
                #raise

            if not self.block:
                break
            c = hex(self.block[0])
            if c != '0xff':
                self.block_read_n(1)
            else:
                block_ff = self.from_block_to_str(self.block[:8])
                #print (block_ff,"--",'0xff'*8)
                if block_ff != '0xff'*8:
                    continue

                #print (self.bread)
                name = self.read_name()
                #print(name)
                num = self.check_num(self.read_num())

                print ("%s;%s" % (name, num))

                # go over 8 0xff
                self.block_read_n(30)

                #print(repr(block_name))
                #print (bread)
                #raise ValueError("")
            #hex(a[0]) == '0x70'






ReadNokiaPB_325().go()
