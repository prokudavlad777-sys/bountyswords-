// Звукові ефекти для змінювача голосу (C++ частина)
//
// Збірка (Windows, MinGW):
//     g++ -O2 -shared -static-libgcc -static-libstdc++ -o voice_dsp.dll effects.cpp
// Збірка (Visual Studio, "x64 Native Tools Command Prompt"):
//     cl /LD /O2 effects.cpp /Fe:voice_dsp.dll

#include <cmath>
#include <cstring>

#ifdef _WIN32
#define EXPORT extern "C" __declspec(dllexport)
#else
#define EXPORT extern "C"
#endif

static const float SR = 44100.0f;
static const float PI = 3.14159265358979f;

// ---------- Зсув тону (два голівки читання з плавним змішуванням) ----------
static const int PBUF = 8192;
static const float WIN = 2048.0f;
static float pbuf[PBUF];
static int pw = 0;          // позиція запису
static float ppos = 0.0f;   // затримка першої голівки

static float read_delayed(float delay) {
    float rp = (float)pw - delay;
    while (rp < 0) rp += PBUF;
    int i0 = (int)rp;
    float fr = rp - i0;
    int i1 = (i0 + 1) % PBUF;
    return pbuf[i0 % PBUF] * (1.0f - fr) + pbuf[i1] * fr;
}

static float pitch_shift(float x, float semitones) {
    float ratio = std::pow(2.0f, semitones / 12.0f);
    pbuf[pw] = x;

    float d1 = ppos;
    float d2 = std::fmod(ppos + WIN * 0.5f, WIN);
    float w1 = std::sin(PI * d1 / WIN); w1 *= w1;
    float w2 = std::sin(PI * d2 / WIN); w2 *= w2;
    float out = read_delayed(d1 + 1.0f) * w1 + read_delayed(d2 + 1.0f) * w2;

    ppos += (1.0f - ratio);
    while (ppos >= WIN) ppos -= WIN;
    while (ppos < 0) ppos += WIN;
    pw = (pw + 1) % PBUF;
    return out;
}

// ---------- Луна ----------
static const int EBUF = 22050;      // 0.5 с
static float ebuf[EBUF];
static int ew = 0;
static const int EDELAY = 13230;    // 0.3 с

static float echo(float x) {
    int rp = (ew - EDELAY + EBUF) % EBUF;
    float d = ebuf[rp];
    ebuf[ew] = x + 0.4f * d;
    ew = (ew + 1) % EBUF;
    return x + 0.5f * d;
}

// ---------- Робот ----------
static float rphase = 0.0f;

static float robot(float x) {
    float c = std::sin(rphase);
    rphase += 2.0f * PI * 50.0f / SR;
    if (rphase > 2.0f * PI) rphase -= 2.0f * PI;
    return x * c * 1.6f;
}

// ---------- Експорт ----------
// effect: 0 без ефекту, 1 свій тон, 2 білка, 3 демон, 4 робот, 5 луна
EXPORT void vc_reset() {
    std::memset(pbuf, 0, sizeof(pbuf));
    std::memset(ebuf, 0, sizeof(ebuf));
    pw = 0; ppos = 0; ew = 0; rphase = 0;
}

EXPORT void vc_process(const float* in, float* out, int n, int effect, float semitones) {
    for (int i = 0; i < n; i++) {
        float x = in[i];
        float y = x;
        switch (effect) {
            case 1: y = pitch_shift(x, semitones); break;
            case 2: y = pitch_shift(x, 7.0f); break;
            case 3: y = std::tanh(3.0f * pitch_shift(x, -7.0f)) * 0.6f; break;
            case 4: y = robot(x); break;
            case 5: y = echo(x); break;
            default: break;
        }
        out[i] = y;
    }
}
