# effective-esp32

Embedded systems design skill for ESP32/Arduino firmware architecture.

Unlike a generic "ESP32 rules" doc, this skill is built from a measured baseline: an unaided model already writes 4+/5 architecture on memory, task design, and contention. So the skill deliberately does **not** re-teach those — it fills only the two areas the baseline reliably misses:

1. **ISR primitives** — `IRAM_ATTR`, `xQueueSendFromISR`/`xTaskNotifyFromISR` + `pxHigherPriorityTaskWoken` + `portYIELD_FROM_ISR`, `std::atomic`/`portMUX` over bare `volatile`, and "the best ISR is often no ISR" (driver DMA).
2. **Validation / empiricism** — stack sizing via `uxTaskGetStackHighWaterMark`, `heap_caps_malloc` by capability, measure-before-tune, hardware bring-up test modes, power budget in mA, toolchain pinning.

It also encodes per-chip facts (C3 single-core / no PSRAM, S3 dual-core / USB-OTG) and an anti-pattern list of common AVR-isms that do nothing on ESP32 (`PROGMEM`/`F()` to "save SRAM", `ESP.getHeapFragmentation()`).

## Proven

Blind A/B benchmark, 12 iterations across 3 projects (audio-FFT C3, 256-LED WiFi C3, USB-HID macropad S3), judged against an authority rubric (Espressif ESP-IDF + FreeRTOS docs + datasheets), not the skill's own claims. See `benchmarks/`.

| variant | avg /25 | vs no-skill baseline |
|---|---|---|
| no skill (baseline) | 20.0 | — |
| **this skill** | **24.25** | **won 12-0-0** |

(An earlier rule-heavy draft scored 15.2 and *lost* to baseline by teaching ESP32-wrong rules — the current version was rebuilt by deleting the cargo cult and targeting only the measured gaps.)

## Use

Triggers on ESP32/Arduino C/C++ firmware architecture, peripheral management, FreeRTOS task design, and resource-constraint optimization.
