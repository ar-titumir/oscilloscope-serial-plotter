// ===================== GLOBAL =====================
volatile int adcValue = 0;
volatile bool newSample = false;

// ===================== TIMER2 ISR (500 µs) =====================
ISR(TIMER2_COMPA_vect)
{
  adcValue = analogRead(A0);
  newSample = true;
}

// ===================== TIMER2 SETUP =====================
void setupTimer2()
{
  cli();

  TCCR2A = (1 << WGM21);   // CTC
  TCCR2B = (1 << CS22);    // prescaler 64 → 4 µs tick

  OCR2A = 124;             // 500 µs = 125 ticks

  TIMSK2 = (1 << OCIE2A);

  sei();
}

// ===================== TIMER1 → 50 Hz (PIN 9) =====================
void setupTimer1_50Hz()
{
  pinMode(9, OUTPUT);

  cli();

  TCCR1A = 0;
  TCCR1B = 0;

  TCCR1B |= (1 << WGM12);   // CTC mode

  TCCR1A |= (1 << COM1A0);  // toggle OC1A (pin 9)

  TCCR1B |= (1 << CS12);    // prescaler 256

  OCR1A = 480;              // 50 Hz=624

  sei();
}

// ===================== TIMER0 → 100 Hz (PIN 5 SOFTWARE DIVIDER) =====================
volatile int t0_count = 0;
volatile bool pwm_state = false;

ISR(TIMER0_COMPA_vect)
{
  t0_count++;

  // Timer0 tick rate = 16MHz/64/256 ≈ 976 Hz
  // toggle every ~5 ticks → ~100 Hz output
  if (t0_count >= 6)
  {
    t0_count = 0;
    pwm_state = !pwm_state;
    digitalWrite(5, pwm_state);
  }
}

void setupTimer0_100Hz()
{
  pinMode(5, OUTPUT);

  cli();

  TCCR0A = (1 << WGM01);   // CTC
  TCCR0B = (1 << CS01) | (1 << CS00); // prescaler 64

  OCR0A = 255;             // overflow interval

  TIMSK0 = (1 << OCIE0A);

  sei();
}

// ===================== SETUP =====================
void setup()
{
  Serial.begin(250000);
  pinMode(13, OUTPUT);

  setupTimer1_50Hz();   // Pin 9 → correct 50 Hz
  setupTimer0_100Hz();  // Pin 5 → ~100 Hz
  setupTimer2();        // 500 µs ISR
}

// ===================== LOOP =====================
int alu = 0;
void loop()
{
  if (newSample)
  {
    noInterrupts();
    int val = adcValue;
    newSample = false;
    interrupts();

    Serial.println(val);
    alu = (alu + 1) % 1000;
    if(!alu) {
      digitalWrite(13, !digitalRead(13));
    }
  }
}
