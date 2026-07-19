# Multilingual Design (Q3)

## Philippines Bot

| Aspect | Configuration |
|--------|--------------|
| Sector | Life insurance / bancassurance |
| Languages | English, Filipino/Tagalog, Taglish |
| ASR | Google Cloud Speech v2 (fil-PH) |
| TTS | Google Cloud TTS (fil-PH) |
| Use case | Premium reminder |

### Localization Examples (Not Translation)

1. Greeting: "Magandang araw po!" not "Good morning!"
2. Respect markers: "po" and "opo" used throughout
3. Code-switching: "May reminder po kami about your premium payment" (natural Taglish)

## Indonesia Bot

| Aspect | Configuration |
|--------|--------------|
| Sector | Multifinance / consumer finance |
| Languages | Formal Bahasa, colloquial Indonesian, English finance loanwords |
| ASR | Google Cloud Speech v2 (id-ID) |
| TTS | Google Cloud TTS (id-ID) |
| Use case | Installment (cicilan) reminder |
| Regional accent | Javanese-accented Indonesian |

### Localization Examples

1. Finance terms: "cicilan" not "installment", "jatuh tempo" not "due date"
2. Polite address: "Bapak/Ibu" instead of "Sir/Ma'am"
3. Colloquial: "gimana", "udah", "nggak" in informal conversation

## Test Results

See `evaluation/test_cases/multilingual.json`
