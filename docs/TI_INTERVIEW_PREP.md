# Texas Instruments Analog / Power Management Engineer Interview Guide
## Technical Interview Cheat Sheet: Synchronous Buck Converter Design

This document prepares you for technical interviews at **Texas Instruments (TI)** for roles such as **Analog Design Engineer**, **Power Management IC (PMIC) Engineer**, **Field Applications Engineer (FAE - Power)**, and **Hardware/Analog Systems Engineer**.

---

### Core Questions TI Interviewers Will Ask You About This Project

#### 1. "Why did you implement Type-III compensation instead of Type-II?"
* **The Interviewer's Trap:** In classical textbook buck converters with aluminum electrolytic or tantalum capacitors, Type-II compensation is standard because the ESR zero ($f_{ESR} = \frac{1}{2\pi \cdot ESR \cdot C_{out}}$) is low enough to boost the phase after the LC double pole.
* **Your Winning Answer:**
  > "Modern power management designs, especially for automotive and industrial Point-of-Load (POL) converters, universally use **ceramic MLCC capacitors** for high reliability, small footprint, and low ripple.
  > 
  > However, ceramic MLCCs have extremely low ESR ($2.5\,\text{m}\Omega$ in our design). This pushes the ESR zero out to **$2.12\,\text{MHz}$**, which is more than 40 times higher than our target crossover frequency ($f_c = 50\,\text{kHz}$).
  > 
  > At the power stage LC double pole ($f_{LC} = 13.4\,\text{kHz}$), the loop phase drops sharply by **$-180^\circ$**. Because the ceramic ESR zero cannot provide phase recovery before crossover, a Type-II compensator (which only offers a single zero/pole pair providing at most $+90^\circ$ phase boost) is structurally insufficient and results in negative or marginal phase margin.
  > 
  > Therefore, I synthesized a **Type-III compensator** (3 poles, 2 zeros). By placing two zeros ($f_{z1} = 10.05\,\text{kHz}$, $f_{z2} = 13.4\,\text{kHz}$) right at the LC resonance, the compensator provides **$+180^\circ$ of phase boost**, achieving a robust **Phase Margin of $50.3^\circ$** and **Gain Margin of $21.8\,\text{dB}$**."

---

#### 2. "Why does TI predominantly use Peak Current Mode Control (PCMC) in chips like TPS54302 or LM5164?"
* **Your Answer:**
  > "There are three primary architectural advantages to PCMC over Voltage Mode Control:
  > 1. **Order Reduction of the Plant:** By measuring the inductor current cycle-by-cycle with an inner current loop, the inductor acts like a high-impedance voltage-controlled current source. This eliminates the complex conjugate LC double pole, converting the plant into a **first-order single-pole system** dominated by the output capacitor and load:
  >    $$f_p = \frac{1}{2\pi R_{load} C_{out}}$$
  >    This drastically simplifies loop compensation, allowing standard Type-II or simple transconductance ($g_m$) error amplifier networks to achieve fast response without Type-III complexity.
  > 2. **Inherent Cycle-by-Cycle Over-Current Protection (OCP):** Because the error amplifier output ($V_{comp}$) directly commands the peak inductor current, clamping $V_{comp}$ naturally enforces an instantaneous hard limit on switch current during shorts or load steps.
  > 3. **Line Feedforward:** Any perturbation in $V_{in}$ immediately alters the inductor current charging slope ($di/dt = (V_{in} - V_{out})/L$), modulating the duty cycle within that exact switching period without needing to wait for an error to propagate through $V_{out}$ and the feedback amplifier."

---

#### 3. "What is Subharmonic Oscillation in PCMC, and how do you solve it?"
* **Your Answer:**
  > "When the duty cycle **$D > 0.5$** in Peak Current Mode Control, a small perturbation in inductor current $\Delta I$ will amplify rather than decay over successive switching cycles, leading to period-doubling oscillation at $f_{sw}/2$.
  > 
  > The mathematical condition for stability is:
  > $$\alpha = \frac{S_f - S_e}{S_n + S_e} < 1$$
  > where $S_n$ is the inductor rising current slope, $S_f$ is the falling slope, and $S_e$ is an added external compensation ramp slope.
  > 
  > When $D > 0.5$, $S_f > S_n$, so without compensation $\alpha > 1$ (unstable). To guarantee stability for all duty cycles up to 100%, we inject an artificial **slope compensation ramp** with slope:
  > $$S_e \ge 0.5 S_f = \frac{V_{out}}{2 L}$$
  > At TI, slope compensation is typically synthesized on-chip by adding a linear sawtooth current ramp to the sensed current signal or subtracting it from the control voltage."

---

#### 4. "How do you size dead time in a synchronous buck converter, and what are the trade-offs?"
* **Your Answer:**
  > "Dead time is the non-overlap delay introduced between turning off the high-side MOSFET and turning on the low-side synchronous rectifier (and vice versa).
  > - **If dead time is too short ($< 10\,\text{ns}$):** Propagation delay mismatches across PVT (Process, Voltage, Temperature) corners will cause **shoot-through (cross-conduction)**, where both switches are momentarily ON, shorting $V_{in}$ directly to GND and destroying the silicon.
  > - **If dead time is too long ($> 40\,\text{ns}$):** During the dead interval, the inductor current forces conduction through the low-side MOSFET's **parasitic body diode**. The forward drop ($V_{sd} \approx 0.75\,\text{V}$) is much higher than the $I \cdot R_{DS(on)}$ drop ($30\,\text{mV}$), resulting in:
  >   1. Elevated conduction loss: $P_{diode} = 2 \cdot V_{sd} \cdot I_{out} \cdot t_{dead} \cdot f_{sw}$ (costing ~1–2% efficiency).
  >   2. Reverse recovery charge ($Q_{rr}$) dissipation and high $dV/dt$ voltage spikes/ringing on the switch node ($SW$) when the high-side turns back on, worsening EMI.
  > 
  > In this design, I implemented a balanced **$25\,\text{ns}$ dead-time**, which provides reliable break-before-make margin while keeping body diode dissipation below $56\,\text{mW}$."

---

#### 5. "Walk me through the efficiency breakdown of your converter."
* **Your Answer:**
  > "Our 12V-to-3.3V / 3A converter achieves a **peak efficiency of $95.9\%$ at $1.37\,\text{A}$** and **$95.2\%$ at full $3\,\text{A}$ load**.
  > 
  > The power dissipation breakdown changes across the load curve:
  > - **At Light Loads ($< 0.5\,\text{A}$):** Frequency-dependent losses dominate:
  >   - High-side switching loss: $P_{sw} = \frac{1}{2} V_{in} I_{out} (t_r + t_f) f_{sw}$
  >   - Gate driver charge loss: $P_{gate} = (Q_{g,HS} + Q_{g,LS}) V_{gate} f_{sw}$
  >   - Output capacitance loss: $P_{oss} = \frac{1}{2} C_{oss} V_{in}^2 f_{sw}$
  >   *(Note: This is why TI parts like TPS54302 implement PFM/Eco-mode at light loads to reduce effective switching frequency).*
  > - **At Heavy Loads ($3\,\text{A}$):** Ohmic conduction losses dominate ($I^2 R$):
  >   - Inductor DCR loss: $I_{rms}^2 R_{DCR} = 161.9\,\text{mW}$ (largest single contributor)
  >   - Low-side MOSFET conduction: $(1-D) I_{rms}^2 R_{DS(on),LS} = 65.2\,\text{mW}$ (because $1-D = 72.5\%$, low-side duty is much higher than high-side!)
  >   - High-side MOSFET conduction: $D I_{rms}^2 R_{DS(on),HS} = 34.6\,\text{mW}$
  >   - High-side hard switching: $125.4\,\text{mW}$."

---

#### 6. "How did you verify stability in simulation without breaking physical closed-loop operation?"
* **Your Answer:**
  > "For closed-loop stability verification, I utilized the **Middlebrook loop injection method**.
  > An AC perturbation source ($V_{ac}$) is placed in series inside the feedback path between the low-impedance output node ($V_{out}$) and the top feedback resistor ($R_1$).
  > 
  > By probing the voltage immediately before ($V_y$) and after ($V_x$) the perturbation source, the true loop gain is evaluated as:
  > $$T(s) = -\frac{V_y(s)}{V_x(s)}$$
  > This preserves the DC operating point while providing the exact open-loop Bode response (crossover frequency and phase margin).
  > 
  > I validated this with a **large-signal load step transient simulation** ($0.5\,\text{A} \to 3.0\,\text{A}$ at $1\,\text{A}/\mu\text{s}$): the output recovered within $25\,\mu\text{s}$ with $< 70\,\text{mV}$ undershoot and zero oscillatory ringing, perfectly corroborating the $50.3^\circ$ phase margin."
