# Texas Instruments Analog / Power Engineering Resume Bullets

Copy and paste these exact bullet points into the **Projects** or **Technical Experience** section of your resume. Choose either the 3-bullet comprehensive block or the 2-bullet concise block depending on your resume space.

---

### Option 1: Comprehensive 3-Bullet Block (Recommended for Analog / Power IC roles)

**High-Efficiency Synchronous Buck DC-DC Converter Design & Stability Analysis** | *LTspice, Python, MATLAB*
* Designed and simulated a 12V-to-3.3V / 3A (10W), 500 kHz synchronous buck converter for automotive POL applications, achieving **95.9% peak efficiency** and $< 12\,\text{mV}_{p-p}$ output ripple.
* Synthesized an active Type-III op-amp compensator to overcome ceramic MLCC high-frequency ESR zero ($f_{ESR} = 2.12\,\text{MHz}$), achieving **$f_c = 49.8\,\text{kHz}$ crossover**, **$50.3^\circ$ Phase Margin**, and **$21.8\,\text{dB}$ Gain Margin**.
* Modeled MOSFET switching/conduction losses and body diode reverse recovery in Python; implemented 25 ns non-overlapping dead-time gate drivers and validated transient stability under $2.5\,\text{A}$ dynamic load steps ($1\,\text{A}/\mu\text{s}$).

---

### Option 2: Concise 2-Bullet Block (Best if short on resume space)

**Closed-Loop Synchronous Buck Converter & Control Modeling** | *LTspice, Python*
* Engineered a 12V $\to$ 3.3V/3A, 500 kHz synchronous buck converter in LTspice with discrete dead-time logic, realistic $R_{DS(on)}$/parasitic models, and Middlebrook loop-gain verification.
* Developed an automated Python modeling suite for Type-III loop compensation and power-loss budgeting, delivering **95.9% peak efficiency** and robust $50.3^\circ$ Phase Margin across ceramic MLCC filters.

---

### Key Skills to list in your Resume Skills section from this project:
* **Power Electronics & Analog Design:** Buck Converters, DC-DC Topologies, Voltage Mode Control (VMC), Peak Current Mode Control (PCMC), Slope Compensation, Gate Drive & Dead-Time Sizing.
* **Control Systems & Small-Signal Modeling:** Transfer Functions ($G_{vd}, G_{vc}, G_c, T(s)$), Type-II & Type-III Active Compensation, Bode Analysis, Phase Margin, Middlebrook Loop Injection.
* **Simulation & Analysis Tools:** LTspice, SPICE Netlisting, Python (`NumPy`, `SciPy`, `Matplotlib`), Transient Load Step Analysis, Power Loss Budgeting.
