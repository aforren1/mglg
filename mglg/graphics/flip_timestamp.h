#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <dwmapi.h>
typedef struct
{
    int foo;
} _foo;
int get_flip_time(_foo *res)
{
    // See PsychWindowGlue
    DWM_TIMING_INFO dwmtiming;
    HRESULT rc;

    DwmFlush();
    while (1)
    {
        // TODO: use timeBeginPeriod(1) to better resolution
        Sleep(1);
        dwmtiming.cbSize = sizeof(dwmtiming);
        if ((rc = DwmGetCompositionTimingInfo(NULL, &dwmtiming)) != 0)
        {
            return (-1);
        }

        if (dwmtiming.cDXPresentSubmitted == dwmtiming.cDXPresentConfirmed)
        {
            break;
        }
    }
    return 0;
}
#endif