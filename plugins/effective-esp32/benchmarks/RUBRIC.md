# Authority-Grounded ESP32 Architecture Rubric (referee doc)

Grade firmware architecture sketches 0-5 on each of 5 dimensions. Score the DECISION, not the vocabulary. Right words with no correct application = no credit. Grounded in Espressif ESP-IDF + FreeRTOS + datasheets (sources at bottom).

## SKILL FACT-CHECK (independent of grading; for skill author)
1. "String literals live in SRAM unless PROGMEM; use PROGMEM/FPSTR on ESP32" — **WRONG**. ESP32 flash is MMU-mapped; PROGMEM/F() are no-ops, `const` already sits in flash. AVR-ism.
2. "Declare ISR vars `volatile sig_atomic_t`" — **PARTIAL**. volatile != atomic on SMP; ESP-IDF idiom is portMUX/critical section or std::atomic + IRAM_ATTR ISR + FromISR handoff.
3. "ESP32 has ~300KB free SRAM (fixed)" — **WRONG**. Total on-chip: 520KB ESP32 / 400KB C3 / 512KB S3. Free varies (~150-290KB). C3 has NO PSRAM; S3 can add it.
4. "ISR sets a flag only, work in a task" — **PARTIAL**. Canonical = xQueueSendFromISR/xTaskNotifyFromISR + pxHigherPriorityTaskWoken + portYIELD_FROM_ISR(), not a polled volatile flag (adds up to 1 tick latency).
5. "delay(8) gives WiFi breathing room" — **PARTIAL**. delay() does call vTaskDelay so it yields, but correct idiom is vTaskDelay(pdMS_TO_TICKS(n)); magic 8ms is a guess not a budget.
6. "Keep C3 monolithic; multi-TU static-init corruption on C3" — **WRONG/ANECDOTAL**. SIOF is generic C++, not C3-specific; fixed by Construct-On-First-Use, not single-file.
7. Omissions (all absent), importance (Audio-FFT-C3 / 256-LED-WiFi-C3 / USB-HID-S3):
   - IRAM_ATTR ISRs: HIGH/HIGH/MED · FromISR APIs: HIGH/MED/MED · portYIELD_FROM_ISR: HIGH/MED/MED
   - esp_task_wdt: MED/MED/MED · uxTaskGetStackHighWaterMark: HIGH/MED/MED
   - heap_caps/PSRAM: MED/MED/LOW (C3 no PSRAM) · DMA for I2S: HIGH/MED/LOW

## RUBRIC

### Dim 1: Memory awareness
- **5:** Correct per-chip SRAM (C3 400KB no-PSRAM / S3 512KB +optional PSRAM); static/stack alloc, avoids runtime new/String churn; sizes buffers to real budget; heap_caps_malloc with right CAP; knows PROGMEM is a no-op.
- **3:** Knows RAM is tight, avoids heap churn, but generic/fixed RAM figure, no chip distinction, no heap_caps/DMA.
- **0:** PROGMEM-to-save-SRAM, fixed "~300KB", dynamic String/containers in hot paths, PSRAM-on-C3.

### Dim 2: ISR safety
- **5:** ISR is IRAM_ATTR, minimal, DRAM-only, no blocking/printf/malloc; handoff via xQueueSendFromISR/xTaskNotifyFromISR + pxHigherPriorityTaskWoken + portYIELD_FROM_ISR(); shared data via portMUX/std::atomic.
- **3:** Short ISR, sets flag, uses volatile, but misses IRAM_ATTR or FromISR+yield handoff.
- **0:** Real work/blocking/Serial/malloc in ISR, or no sync primitive, or "volatile sig_atomic_t" as the whole answer.

### Dim 3: Task design
- **5:** FreeRTOS tasks with justified priorities; notifications/queues for handoff; pins to core only where real (notes C3 single-core so pinning moot); no busy-wait; critical tasks on esp_task_wdt.
- **3:** Tasks + queue/semaphore + vTaskDelay, but arbitrary priorities, no watchdog, or core-pins on C3.
- **0:** Single loop() with delay() busy-wait, or desktop thread-pool boilerplate.

### Dim 4: Contention handling
- **5:** Names the specific conflict (WiFi ISRs vs clockless-LED timing; flash-op cache stall vs audio ISR) + concrete mitigation: RMT/I2S DMA buffering, core/priority isolation, IRAM ISR, explicit yield on single-core C3, async-handler discipline.
- **3:** Recognizes WiFi-vs-render/single-core and yields, but vague ("add delay"), no DMA/RMT/priority specifics.
- **0:** Ignores contention, blocks in callbacks, or assumes two cores on C3.

### Dim 5: Validation / empiricism
- **5:** measure-before-tune: uxTaskGetStackHighWaterMark, heap/free-RAM monitoring, hardware self-test/bring-up mode, toolchain/core pinning, power budget (mA).
- **3:** Mentions checking free heap or real-HW test, but no stack high-water, no version pin, no power budget.
- **0:** Guessed buffer/stack/delay numbers, no measurement plan.

## SCORE CAPS (red flags)
- PROGMEM/F() to "save SRAM" → Dim 1 ≤ 2
- Core-pinning / "use other core" on C3 → Dim 3 ≤ 2
- Allocating PSRAM on C3 → Dim 1 ≤ 2
- Blocking/Serial/malloc in ISR → Dim 2 ≤ 1
- Fixed "~300KB free SRAM" as universal → Dim 1 ≤ 3
- Monolithic justified by "C3 static-init corruption" → Dim 5 ≤ 2
- Right words, no correct application → no credit

## SOURCES
ESP-IDF intr_alloc, ESP-IDF FreeRTOS, FreeRTOS task notifications, ESP-IDF heap mem_alloc, ESP-IDF watchdogs, esp32.com t=20595 (PROGMEM), Arduino PROGMEM ref, C3/ESP32/S3 datasheets, FastLED #1961, esp32.com t=3980 (RMT+WiFi flicker), cppreference SIOF.
