---
name: effective-esp32
description: Embedded systems design for ESP32/Arduino. Use when writing C/C++ for ESP32, designing firmware architecture, managing peripheral interactions, or optimizing for resource constraints. Focuses on the two things Claude reliably slips on -- ISR primitives and proving the design with measurement -- not on re-teaching architecture it already does well.
---

# Effective ESP32 -- Fill the Two Holes, Don't Re-teach the Whole Thing

You already write correct, idiomatic ESP32 architecture for the easy 80%. Measured against authority (ESP-IDF, FreeRTOS, the datasheets), an unaided baseline already:

- reaches for **RMT/DMA** to drive WS2812 so interrupts stay enabled (the root-cause fix, not a `delay()` band-aid),
- **statically allocates** buffers and avoids `String`/heap churn,
- splits work into **FreeRTOS tasks with justified priorities** and knows the **C3 is single-core** (so core-pinning is a no-op there),
- knows **`PROGMEM`/`F()` are no-ops on ESP32** -- flash is MMU-mapped, `const` already lands in `.rodata`.

Do not "correct" any of that. Re-teaching it with rules of thumb makes the output *worse*. This skill is only about the two places the baseline reliably drops the ball:

1. **ISR primitives** -- the instinct ("defer work out of the ISR") is right, but the *mechanism* is often vague.
2. **Validation / empiricism** -- designs ship as assertions, not measurements. This is the single weakest area.

Everything below is one of those two. If a suggestion isn't filling one of these holes, you're adding noise.

---

## Hole 1: ISR primitives (get the mechanism exact)

The shape is right: ISR does the minimum, real work happens in a task. The parts that get dropped:

```cpp
// The ISR itself
void IRAM_ATTR gpio_isr(void *arg) {        // IRAM_ATTR: runs even when flash cache is disabled
    BaseType_t hpw = pdFALSE;
    uint32_t evt = read_some_register();     // DRAM only, no float, no printf, no malloc
    xQueueSendFromISR(evtQ, &evt, &hpw);     // ...FromISR variant, never the plain call
    portYIELD_FROM_ISR(hpw);                 // wake the task NOW, not one tick later
}
```

Rules that matter (authority: ESP-IDF intr_alloc + FreeRTOS):
- **`IRAM_ATTR`** on any ISR that can fire during SPI-flash ops, or it crashes when cache is off.
- Hand off with **`xQueueSendFromISR` / `xTaskNotifyFromISR`** + a `BaseType_t hpw` + **`portYIELD_FROM_ISR(hpw)`**. A bare polled `volatile` flag adds up to one tick of latency and is the lazy-but-worse pattern.
- Shared scalars: **`std::atomic`** or a **`portMUX_TYPE` critical section** (`portENTER_CRITICAL_ISR`/`portEXIT_CRITICAL_ISR`). `volatile` alone is **not** atomicity on the SMP parts.
- No `Serial`, `WiFi`, `delay()`, float, or heap in the ISR. Float in an ISR needs explicit FPU handling -- just don't.
- **Often the best ISR is no ISR**: for I2S audio / WS2812 output, let the **driver's DMA** do the timing and block the task on `i2s_read` / the RMT transfer. Say so when it applies.

## Hole 2: Validation / empiricism (make the design prove itself)

This is where unaided output is weakest. Every non-trivial design should carry the measurement that backs it. Add whichever apply:

- **Stack sizing by measurement, not guess:** `uxTaskGetStackHighWaterMark(NULL)` logged once the task is warm; size the stack to the watermark + margin. (FFT buffers and the WiFi stack blow guessed stacks silently.)
- **Heap by capability:** `heap_caps_malloc(n, MALLOC_CAP_DMA)` for DMA buffers, `MALLOC_CAP_INTERNAL` to stay off PSRAM, `MALLOC_CAP_SPIRAM` only on parts that have it (**S3 can, C3 cannot**). Check `heap_caps_get_free_size(...)` for the cap you actually use. (`ESP.getHeapFragmentation()` is an ESP8266 API -- no-op on ESP32; don't.)
- **Measure before tuning:** benchmark the hot path in `setup()` before declaring it fits.
  ```cpp
  uint32_t t0 = micros();
  for (int i=0;i<64;i++) computeFFT();
  Serial.printf("FFT %u us/call\n", (micros()-t0)/64);   // "C3 too slow for FFT" is usually false -- measure it
  ```
- **Hardware bring-up mode before product logic:** a `TEST_PATTERN` mode that lights corners/diagonals to verify WS2812 mapping (serpentine vs zigzag) on the real panel. Don't write animation against an assumed map.
- **Power budget in mA, not vibes:** 256 WS2812 @ full white ≈ 15A; USB gives ~2A → cap brightness (`FastLED.setMaxPowerInVoltsAndMilliamps(5,2000)` is better than a flat brightness guess because it scales per frame).
- **Watchdog the long tasks:** subscribe critical tasks with `esp_task_wdt_add()` and feed them; an unfed loop is how a field unit bricks silently.
- **Pin the toolchain** when timing-sensitive (`platform = espressif32@6.9.0` etc.) so a silent core bump doesn't change RMT/I2S behavior under you.

---

## Per-chip facts (so the design targets the real part)

| | ESP32 | ESP32-C3 | ESP32-S3 |
|---|---|---|---|
| cores | 2 | **1** | 2 |
| on-chip SRAM | 520KB | 400KB | 512KB |
| PSRAM | optional | **none** | optional (in-package/ext) |
| native USB | no | no (USB-Serial-JTAG) | **yes (USB-OTG/TinyUSB)** |

- **C3 is single-core** → don't pin tasks to "the other core"; pinning is at best a no-op, and "use core 0 for X" is a category error. Prioritize instead, and keep app tasks *below* the WiFi/LwIP stack (~prio 18+).
- **S3 is dual-core** → core-pinning is legitimate (e.g. USB/scan on one core, blocking flash I/O on the other).
- Free SRAM is **not** a fixed "~300KB"; it depends on the part and what WiFi/BT reserve. Size to the part.

## Contention (you already do this -- just keep it concrete)

The baseline already names the WiFi-ISR-vs-clockless-LED-timing conflict and fixes it with RMT/DMA. Keep doing exactly that. The only addition: **quantify** the interrupt-off window when you bit-bang (e.g. 256·24·1.25µs ≈ 7.7ms) so the reader sees why DMA wins. Yielding (`vTaskDelay`) reduces but does not *close* a bit-bang window; DMA does.

## Hard rules (the short list that's actually true)
- ISR: `IRAM_ATTR` + `...FromISR` + `portYIELD_FROM_ISR`; `std::atomic`/`portMUX` for shared data; nothing blocking inside.
- Prefer driver **DMA** (I2S, RMT) over hand-rolled timing.
- **Measure, then state:** stack via high-water, hot path via `micros()`, power via mA, mapping via a bring-up mode.
- Target the **specific part** (cores, SRAM, PSRAM, USB) -- see the table.
- **No AVR-isms**: `PROGMEM`/`F()`/`pgm_read_*` do nothing useful on ESP32; `ESP.getHeapFragmentation()` is a no-op.
- Network/blocking I/O off the main path, in its own task, notified back.

## Anti-patterns (these showed up and each cost real points)
- `PROGMEM`/`F()` "to save SRAM" — no-op on ESP32.
- Core-pinning on the C3 — it has one core.
- "Keep it monolithic to avoid C3 static-init corruption" — static-init-order is generic C++, fixed by construct-on-first-use, not by one file.
- `volatile sig_atomic_t` as the *whole* ISR-safety answer — missing IRAM_ATTR/FromISR/yield.
- Magic `delay(8)` — use `vTaskDelay(pdMS_TO_TICKS(n))` to a measured budget.
- Shipping numbers (stack depth, buffer size, brightness) as guesses with no measurement behind them.
