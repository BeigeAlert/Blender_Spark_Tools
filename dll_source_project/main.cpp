
#include <python.h>
#include <Windows.h>
#include <iostream>
#include <string>

#define RCF RegisterClipboardFormatW

const wchar_t *CLIPBOARD_FORMAT = L"application/spark editor";

static PyObject* get_clipboard_data(PyObject *self, PyObject *args)
{
    OpenClipboard(NULL);
    unsigned int CF_SPARK = RCF(CLIPBOARD_FORMAT);

    if (!IsClipboardFormatAvailable(CF_SPARK))
    {
        CloseClipboard();
        PyErr_SetString(PyExc_IOError, "No Spark data found on clipboard!");
        return NULL;
    }

    HANDLE data = GetClipboardData(CF_SPARK);
    SIZE_T size = GlobalSize(data);

    if (size <= 0)
    {
        CloseClipboard();
        PyErr_SetString(PyExc_IOError, "Error reading Spark data! (size <= 0)");
        return NULL;
    }

    LPVOID dataLocked = GlobalLock(data);
    std::string binData(static_cast<char*>(dataLocked), size);
    GlobalUnlock(data);
    CloseClipboard();

    PyObject* pythonBytesData = PyBytes_FromStringAndSize(binData.c_str(), binData.size());
    return pythonBytesData;
}

static PyObject* set_clipboard_data(PyObject *self, PyObject *args)
{
    OpenClipboard(0);
    if (!EmptyClipboard())
    {
        PyErr_SetString(PyExc_IOError, "Error clearing old clipboard data!");
        CloseClipboard();
        return NULL;
    }

    unsigned int CF_SPARK = RCF(CLIPBOARD_FORMAT);

    PyObject* passedBytes;
    if (!PyArg_UnpackTuple(args, "clip", 1, 1, &passedBytes))
    {
        CloseClipboard();
        PyErr_SetString(PyExc_IOError, "Error reading passed data!");
        return NULL;
    }

    Py_ssize_t length;
    char* binData;
    PyBytes_AsStringAndSize(passedBytes, &binData, &length);

    HGLOBAL memoryHandle = GlobalAlloc(GPTR, length);
    LPVOID dataPointer = GlobalLock(memoryHandle);

    errno_t e = memcpy_s(dataPointer, length, binData, length);

    GlobalUnlock(memoryHandle);
    SetClipboardData(CF_SPARK, memoryHandle);
    CloseClipboard();

    return Py_None;
}

static PyMethodDef ClipMethods[] = {
    { "get_clipboard_data", get_clipboard_data, METH_VARARGS, "retrieve the spark clipboard data as a bytes object." },
    { "set_clipboard_data", set_clipboard_data, METH_VARARGS, "set the spark clipboard data to the provided bytes object." },
    { NULL, NULL, 0, NULL } // Sentinel
};

static struct PyModuleDef clipmodule = {
    PyModuleDef_HEAD_INIT,
    "sparkclip", //name
    NULL, //docs
    -1,
    ClipMethods
};

PyMODINIT_FUNC PyInit_sparkclip(void)
{
    return PyModule_Create(&clipmodule);
}
