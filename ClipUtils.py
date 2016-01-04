# Written by Trevor Harris aka BeigeAlert.
# Feel free to modify at your leisure, just make sure you
# give credit where it's due.
# Cheers! -Beige
# Last modified November 22, 2014

#from ctypes import *
#from binascii import hexlify
from . import SparkClasses
from . import sparkclip
import sys

def GetClipboardAsString():
	"""Returns a byte string of all the data contained on the clipboard, as long as it's Spark data"""
	return sparkclip.get_clipboard_data()

def SetClipboardFromString(data):
	"""Sets the data in the clipboard to the data supplied in the byte string, and sets the clipboard format to the proper spark data format"""
	sparkclip.set_clipboard_data(data)
	return True

'''def GetClipboardAsString():
    """Returns a byte string of all the data contained on the clipboard, as long as it's Spark data"""
    kernel32 = windll.kernel32
    user32 = windll.user32
    
    user32.OpenClipboard(0)
    
    CF_SPARK = user32.RegisterClipboardFormatW("application/spark editor")
    CF_SPARK2 = user32.RegisterClipboardFormatA("application/spark editor")
    
    if user32.IsClipboardFormatAvailable(CF_SPARK):
        data = user32.GetClipboardData(CF_SPARK)
        size = kernel32.GlobalSize(data)
        if size == 0:
            data = user32.GetClipboardData(CF_SPARK2)
            size = kernel32.GlobalSize(data)
        if size == 0:
            raise SparkClasses.SparkError("Error retrieving clipboard data, got 0 bytes!")
        data_locked = kernel32.GlobalLock(data)
        binData = string_at(data_locked,size)
        kernel32.GlobalUnlock(data)
        user32.CloseClipboard()
        return binData
    else:
        user32.CloseClipboard()
        raise SparkClasses.SparkError("No Spark data found on clipboard!")
        return None'''

'''def SetClipboardFromString(data):
    """Sets the data in the clipboard to the data supplied in the byte string, and sets the clipboard format to the proper spark data format"""
    kernel32 = windll.kernel32
    user32 = windll.user32
    memcpy = cdll.msvcrt.memcpy
    
    user32.OpenClipboard(None)
    user32.EmptyClipboard()
    
    CF_SPARK = user32.RegisterClipboardFormatW("application/spark editor")
    GPTR = 0x0040 #Flags to use when allocating global memory.
    
    hexlify(b'helloworld!') #ESSENTIAL CODE, DON'T KNOW WHY!!!  (Seriously...)
    
    length = len(data)
    memory_handle = kernel32.GlobalAlloc(GPTR, length)
    
    hexlify(b'helloworld!') #ESSENTIAL CODE, DON'T KNOW WHY!!!  (Seriously...)
    
    data_point = kernel32.GlobalLock(memory_handle)
    
    hexlify(b'helloworld!') #ESSENTIAL CODE, DON'T KNOW WHY!!!  (Seriously...)
    
    for i in range(0,length):
        value = int.from_bytes((data[i:i+1]), byteorder='little')
        memset(data_point+i,value,1)
        
    kernel32.GlobalUnlock(memory_handle)
    
    hexlify(b'helloworld!') #ESSENTIAL CODE, DON'T KNOW WHY!!!  (Seriously...)
    
    user32.SetClipboardData(CF_SPARK, memory_handle)
    
    hexlify(b'helloworld!') #ESSENTIAL CODE, DON'T KNOW WHY!!!  (Seriously...)
    
    user32.CloseClipboard()
    return True'''

