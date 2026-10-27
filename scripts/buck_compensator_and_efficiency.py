"""
Texas Instruments Standard: Synchronous Buck Converter Design & Analysis Tool
=============================================================================
Author: Roshan (Analog / Power Management Engineering Portfolio)
Target Application: 12V to 3.3V / 3A Synchronous Buck Converter (Automotive / Industrial POL)

Capabilities:
1. Small-signal control-to-output plant transfer function derivation (VMC & PCMC).
2. Type-III (3-pole, 2-zero) compensator synthesis for ceramic MLCC output capacitors.
3. Peak Current-Mode Control (PCMC) comparison & slope compensation design.
4. Closed-loop stability verification (Bode plot, Phase Margin, Gain Margin).
5. Comprehensive MOSFET & Inductor loss modeling with efficiency curves (100mA to 3.5A).
"""

import os
import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# 1. DESIGN SPECIFICATIONS & NOMINAL OPERATING POINT
# =============================================================================
Vin_nom   = 12.0          # Input voltage [V] (nominal 12V automotive/industrial bus)
Vin_min   = 8.0           # Minimum input voltage [V]
Vin_max   = 18.0          # Maximum input voltage [V]
Vout      = 3.3           # Target regulated output voltage [V]
Iout_nom  = 3.0           # Nominal full-load output current [A]
fsw       = 500e3         # Switching frequency [Hz] (500 kHz)
Tsw       = 1.0 / fsw     # Switching period [s]
Vref      = 0.8           # Internal bandgap reference voltage [V] (TI standard)
Vramp     = 1.5           # PWM modulator sawtooth ramp peak-to-peak [V]

# Power Stage Passives
L         = 4.7e-6        # Power inductor inductance [H] (4.7 uH)
R_dcr     = 18e-3         # Inductor DC resistance [Ohm] (18 mOhm)
Cout_eff  = 30e-6         # Effective output capacitance with DC bias derating [F] (2x 22uF X7R)
R_esr     = 2.5e-3        # Equivalent series resistance of MLCC bank [Ohm] (2.5 mOhm)

# MOSFET & Gate Driver Parameters (TI CSD18534Q5A class 60V / 11mOhm NexFET)
Rds_on_hs = 14e-3         # High-side MOSFET on-state resistance @ Tj=75C [Ohm]
Rds_on_ls = 10e-3         # Low-side MOSFET on-state resistance @ Tj=75C [Ohm]
Qg_hs     = 7.5e-9        # High-side gate charge [C] (7.5 nC)
Qg_ls     = 11.0e-9       # Low-side gate charge [C] (11.0 nC)
Coss_hs   = 140e-12       # High-side output capacitance [F]
tr        = 8e-9          # High-side switch rise time [s] (8 ns)
tf        = 6e-9          # High-side switch fall time [s] (6 ns)
Vsd       = 0.75          # Body diode forward voltage drop [V]
tdead     = 25e-9         # Dead-time (break-before-make) [s] (25 ns)
Vgate     = 5.0           # Gate drive voltage rail [V]

# Target Loop Metrics
fc_target = 50e3          # Target crossover frequency [Hz] (fsw / 10)
PM_target = 60.0          # Target phase margin [degrees]

# Output directory for saving figures
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(SCRIPT_DIR, "..", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# =============================================================================
# 2. POWER STAGE STEADY-STATE CALCULATIONS
# =============================================================================
D = Vout / Vin_nom
Rload_nom = Vout / Iout_nom
dIL = (Vin_nom - Vout) * D / (L * fsw)
ripple_ratio = dIL / Iout_nom
dV_cout = dIL / (8.0 * fsw * Cout_eff)
dV_esr = dIL * R_esr
dVout_ripple_pp = dV_cout + dV_esr

fLC = 1.0 / (2.0 * np.pi * np.sqrt(L * Cout_eff))
fESR = 1.0 / (2.0 * np.pi * R_esr * Cout_eff)

print("=" * 70)
print("TEXAS INSTRUMENTS SYNCHRONOUS BUCK CONVERTER DESIGN ENGINE")
print("=" * 70)
print(f"Input Voltage: {Vin_nom:.1f} V (Range: {Vin_min:.1f} V - {Vin_max:.1f} V)")
print(f"Output Voltage: {Vout:.2f} V @ {Iout_nom:.1f} A (Rload = {Rload_nom:.2f} Ohm)")
print(f"Switching Frequency: {fsw/1e3:.1f} kHz (Tsw = {Tsw*1e6:.2f} us)")
print(f"Duty Cycle: {D*100:.1f} %")
print(f"Inductor Ripple: {dIL:.2f} A pk-pk ({ripple_ratio*100:.1f}% of Iout)")
print(f"Output Voltage Ripple (pp): {dVout_ripple_pp*1e3:.2f} mV (Cap: {dV_cout*1e3:.2f} mV, ESR: {dV_esr*1e3:.2f} mV)")
print(f"LC Double Pole (fLC): {fLC/1e3:.2f} kHz")
print(f"Ceramic ESR Zero (fESR): {fESR/1e3:.2f} kHz  <-- (Note: fESR >> fc, Type-III mandatory!)")
print("-" * 70)

# =============================================================================
# 3. CONTROL LOOP: VOLTAGE-MODE CONTROL (VMC) & TYPE-III COMPENSATOR
# =============================================================================
# Plant Transfer Function Gvd(s)
def Gvd_vmc(s, Vin=Vin_nom, Rload=Rload_nom):
    # Includes inductor DCR and capacitor ESR
    # Gvd(s) = (Vin / Vramp) * (1 + s*Resr*C) / [1 + s*(L/R + (Resr+Rdcr)*C) + s^2*L*C]
    num = (Vin / Vramp) * (1.0 + s * R_esr * Cout_eff)
    den = 1.0 + s * (L / Rload + (R_esr + R_dcr) * Cout_eff) + (s**2) * L * Cout_eff
    return num / den

# Type-III Compensator Synthesis
# Placement rules based on TI Application Report SLVA662:
# fz1 = 0.75 * fLC
# fz2 = fLC
# fp1 = fESR (or fsw/2 if fESR > fsw/2)
# fp2 = 0.5 * fsw
fz1 = 0.75 * fLC
fz2 = fLC
fp1 = min(fESR, fsw * 0.5)
fp2 = fsw * 0.5

wz1 = 2.0 * np.pi * fz1
wz2 = 2.0 * np.pi * fz2
wp1 = 2.0 * np.pi * fp1
wp2 = 2.0 * np.pi * fp2
wc  = 2.0 * np.pi * fc_target

# Required compensator gain at crossover to achieve |T(jwc)| = 1
plant_mag_at_fc = np.abs(Gvd_vmc(1j * wc))
compensator_shape_mag = np.abs(((1.0 + 1j * wc / wz1) * (1.0 + 1j * wc / wz2)) /
                               ((1j * wc) * (1.0 + 1j * wc / wp1) * (1.0 + 1j * wc / wp2)))
K_comp = 1.0 / (plant_mag_at_fc * compensator_shape_mag)

# Synthesize physical op-amp component values
# Standard 3-R, 3-C Type-III topology (TI SLVA662 Section 4):
# Inverting input network: R1 || (R3 + C3)
# Feedback network: (R2 + C1) || C2
R1 = 20.0e3  # Chosen input resistor [Ohm]
R_bottom = R1 * Vref / (Vout - Vref)

# Standard placement based on TI Application Note SLVA662:
# Zero 2: placed at fLC
# Pole 2: placed at fsw / 2
C3 = 1.0 / (2.0 * np.pi * fz2 * R1)
R3 = 1.0 / (2.0 * np.pi * fp2 * C3)

# Calculate Zin at crossover frequency wc
s_c = 1j * wc
Z_in_at_fc = (R1 * (R3 + 1.0/(s_c * C3))) / (R1 + R3 + 1.0/(s_c * C3))

# Normalized feedback impedance with R2=1 Ohm:
# C1_norm = 1 / wz1, C2_norm = 1 / wp1
# Z_fb(R2) = R2 * [ (1 + 1/(s*C1_norm)) * (1/(s*C2_norm)) ] / [ 1 + 1/(s*C1_norm) + 1/(s*C2_norm) ]
Z_fb_norm_at_fc = ((1.0 + wz1/s_c) * (wp1/s_c)) / (1.0 + wz1/s_c + wp1/s_c)

# Solve for exact R2 to force |Gc(jwc)| * |Gvd(jwc)| = 1
plant_mag_c = np.abs(Gvd_vmc(s_c))
R2 = np.abs(Z_in_at_fc) / (plant_mag_c * np.abs(Z_fb_norm_at_fc))

# Synthesize physical C1 and C2
C1 = 1.0 / (wz1 * R2)
C2 = 1.0 / (wp1 * R2)

def Gc_type3(s):
    """Op-Amp Type-III Compensator Transfer Function."""
    # Z_in = (R1) in parallel with (R3 + 1/(s*C3))
    # Z_fb = (R2 + 1/(s*C1)) in parallel with (1/(s*C2))
    Z_in = (R1 * (R3 + 1.0/(s * C3))) / (R1 + R3 + 1.0/(s * C3))
    Z_fb = ((R2 + 1.0/(s * C1)) * (1.0/(s * C2))) / (R2 + 1.0/(s * C1) + 1.0/(s * C2))
    return Z_fb / Z_in

def T_vmc(s):
    """Open-Loop Gain T(s) = Gvd(s) * Gc(s)"""
    return Gvd_vmc(s) * Gc_type3(s)

print("TYPE-III COMPENSATOR SYNTHESIS RESULTS:")
print(f"Target Crossover (fc): {fc_target/1e3:.1f} kHz | Target PM: {PM_target:.1f} deg")
print(f"Compensator Zeros: fz1 = {fz1/1e3:.2f} kHz, fz2 = {fz2/1e3:.2f} kHz")
print(f"Compensator Poles: fp1 = {fp1/1e3:.2f} kHz, fp2 = {fp2/1e3:.2f} kHz")
print(f"Physical Component Values:")
print(f"  R1 (Top Divider)   = {R1/1e3:.2f} kOhm")
print(f"  R_bottom (Divider) = {R_bottom/1e3:.2f} kOhm (yields Vout = {Vref*(1 + R1/R_bottom):.2f} V)")
print(f"  R2 (Feedback Zero) = {R2/1e3:.2f} kOhm")
print(f"  R3 (Feedfwd Pole)  = {R3/1e3:.2f} kOhm")
print(f"  C1 (Feedback Zero) = {C1*1e9:.2f} nF")
print(f"  C2 (Feedback Pole) = {C2*1e12:.2f} pF")
print(f"  C3 (Feedfwd Zero)  = {C3*1e9:.2f} nF")
print("-" * 70)

# =============================================================================
# 4. FREQUENCY DOMAIN LOOP METRIC EVALUATION
# =============================================================================
freqs = np.logspace(1, 6, 2000)
w_vec = 2.0 * np.pi * freqs
s_vec = 1j * w_vec

T_eval = T_vmc(s_vec)
T_mag_db = 20.0 * np.log10(np.abs(T_eval))
T_phase_deg = np.unwrap(np.angle(T_eval)) * 180.0 / np.pi

# Find 0 dB crossover
idx_cross = np.where(np.diff(np.sign(T_mag_db)))[0]
if len(idx_cross) > 0:
    ic = idx_cross[-1]
    fc_achieved = freqs[ic]
    pm_achieved = 180.0 + T_phase_deg[ic]
else:
    fc_achieved = float('nan')
    pm_achieved = float('nan')

# Find -180 deg phase crossover for gain margin
idx_phase180 = np.where(np.diff(np.sign(T_phase_deg + 180.0)))[0]
if len(idx_phase180) > 0:
    ip = idx_phase180[-1]
    gm_achieved = -T_mag_db[ip]
else:
    gm_achieved = float('nan')

print(f"ACHIEVED CLOSED-LOOP STABILITY METRICS:")
print(f"  Crossover Frequency (fc): {fc_achieved/1e3:.2f} kHz")
print(f"  Phase Margin (PM):        {pm_achieved:.1f} degrees (Target: >= 50 deg)")
print(f"  Gain Margin (GM):         {gm_achieved:.1f} dB (Target: >= 10 dB)")
print("-" * 70)

# =============================================================================
# 5. PEAK CURRENT-MODE CONTROL (PCMC) COMPARISON
# =============================================================================
# Plant for PCMC: inductor behaves as a controlled current source!
# Eliminates the LC double-pole; replaces it with single dominant pole at fp = 1/(2*pi*Rload*Cout)
Rsense = 20e-3  # Equivalent current sense gain [V/A]
f_pcmc_pole = 1.0 / (2.0 * np.pi * Rload_nom * Cout_eff)

def Gvc_pcmc(s, Rload=Rload_nom):
    # First-order model with current-loop sampling effect (Ridley model)
    num = (Rload / Rsense) * (1.0 + s * R_esr * Cout_eff)
    den = (1.0 + s * Rload * Cout_eff) * (1.0 + s / (np.pi * fsw) + (s / (np.pi * fsw))**2)
    return num / den

Gvc_eval = Gvc_pcmc(s_vec)
Gvd_eval = Gvd_vmc(s_vec)

# =============================================================================
# 6. COMPREHENSIVE EFFICIENCY & POWER LOSS MODELING
# =============================================================================
Iload_arr = np.linspace(0.1, 3.5, 100)
P_cond_hs_arr = []
P_cond_ls_arr = []
P_sw_hs_arr   = []
P_gate_arr    = []
P_oss_arr     = []
P_diode_arr   = []
P_dcr_arr     = []
P_esr_arr     = []
P_total_arr   = []
eta_arr       = []

for I_l in Iload_arr:
    # Inductor current RMS and components
    dIL_curr = (Vin_nom - Vout) * D / (L * fsw)
    IL_rms_sq = I_l**2 + (dIL_curr**2) / 12.0
    
    # 1. Conduction losses
    P_cond_hs = D * IL_rms_sq * Rds_on_hs
    P_cond_ls = (1.0 - D) * IL_rms_sq * Rds_on_ls
    
    # 2. Hard switching loss (high-side during turn-on & turn-off)
    P_sw_hs = 0.5 * Vin_nom * I_l * (tr + tf) * fsw
    
    # 3. Gate drive losses
    P_gate = (Qg_hs + Qg_ls) * Vgate * fsw
    
    # 4. MOSFET output capacitance loss (Coss)
    P_oss = 0.5 * Coss_hs * (Vin_nom**2) * fsw
    
    # 5. Body diode conduction during dead-time
    P_diode = 2.0 * Vsd * I_l * tdead * fsw
    
    # 6. Inductor DCR loss
    P_dcr = IL_rms_sq * R_dcr
    
    # 7. Output capacitor ESR loss
    # Capacitor ripple current RMS = dIL / sqrt(12)
    Ic_rms_sq = (dIL_curr**2) / 12.0
    P_esr = Ic_rms_sq * R_esr
    
    P_loss = P_cond_hs + P_cond_ls + P_sw_hs + P_gate + P_oss + P_diode + P_dcr + P_esr
    P_out = Vout * I_l
    eta = (P_out / (P_out + P_loss)) * 100.0
    
    P_cond_hs_arr.append(P_cond_hs)
    P_cond_ls_arr.append(P_cond_ls)
    P_sw_hs_arr.append(P_sw_hs)
    P_gate_arr.append(P_gate)
    P_oss_arr.append(P_oss)
    P_diode_arr.append(P_diode)
    P_dcr_arr.append(P_dcr)
    P_esr_arr.append(P_esr)
    P_total_arr.append(P_loss)
    eta_arr.append(eta)

P_cond_hs_arr = np.array(P_cond_hs_arr)
P_cond_ls_arr = np.array(P_cond_ls_arr)
P_sw_hs_arr   = np.array(P_sw_hs_arr)
P_gate_arr    = np.array(P_gate_arr)
P_diode_arr   = np.array(P_diode_arr)
P_dcr_arr     = np.array(P_dcr_arr)
P_total_arr   = np.array(P_total_arr)
eta_arr       = np.array(eta_arr)

# Find peak efficiency and full-load efficiency
peak_eta_idx = np.argmax(eta_arr)
peak_eta = eta_arr[peak_eta_idx]
peak_eta_I = Iload_arr[peak_eta_idx]
full_load_idx = np.argmin(np.abs(Iload_arr - Iout_nom))
full_load_eta = eta_arr[full_load_idx]
full_load_loss = P_total_arr[full_load_idx]

print(f"POWER STAGE LOSS & EFFICIENCY SUMMARY:")
print(f"  Peak Efficiency:      {peak_eta:.2f} % @ {peak_eta_I:.2f} A")
print(f"  Full-Load Efficiency: {full_load_eta:.2f} % @ {Iout_nom:.1f} A")
print(f"  Total Full-Load Loss: {full_load_loss:.3f} W (Pout = {Vout*Iout_nom:.2f} W)")
print(f"  Loss Breakdown @ 3A:")
print(f"    HS Conduction:     {P_cond_hs_arr[full_load_idx]*1e3:.1f} mW")
print(f"    LS Conduction:     {P_cond_ls_arr[full_load_idx]*1e3:.1f} mW")
print(f"    HS Switching:      {P_sw_hs_arr[full_load_idx]*1e3:.1f} mW")
print(f"    Inductor DCR:      {P_dcr_arr[full_load_idx]*1e3:.1f} mW")
print(f"    Gate Drive:        {P_gate*1e3:.1f} mW")
print(f"    Body Diode:        {P_diode_arr[full_load_idx]*1e3:.1f} mW")
print("=" * 70)

# =============================================================================
# 7. GENERATE PUBLICATION-QUALITY PLOTS
# =============================================================================
# Plot 1: Type-III VMC Loop Gain & Stability Bode Plot
fig, (ax_mag, ax_ph) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax_mag.semilogx(freqs, 20*np.log10(np.abs(Gvd_eval)), 'tab:gray', ls='--', lw=1.5, label='Plant Gvd(s)')
ax_mag.semilogx(freqs, 20*np.log10(np.abs(Gc_type3(s_vec))), 'tab:blue', ls=':', lw=1.5, label='Type-III Compensator Gc(s)')
ax_mag.semilogx(freqs, T_mag_db, 'tab:red', lw=2.2, label='Loop Gain T(s)')
ax_mag.axhline(0, color='black', lw=0.8, ls='-')
ax_mag.axvline(fc_achieved, color='darkorange', ls='--', lw=1.2, label=f'Crossover fc = {fc_achieved/1e3:.1f} kHz')
ax_mag.set_ylabel('Magnitude [dB]', fontsize=11, fontweight='bold')
ax_mag.set_title('Type-III Voltage-Mode Control: Small-Signal Loop Dynamics (12V to 3.3V / 3A)', fontsize=12, fontweight='bold')
ax_mag.grid(True, which='both', ls='-', alpha=0.3)
ax_mag.legend(loc='lower left', framealpha=0.9)
ax_mag.set_ylim(-40, 60)

ax_ph.semilogx(freqs, np.unwrap(np.angle(Gvd_eval))*180/np.pi, 'tab:gray', ls='--', lw=1.5)
ax_ph.semilogx(freqs, np.unwrap(np.angle(Gc_type3(s_vec)))*180/np.pi, 'tab:blue', ls=':', lw=1.5)
ax_ph.semilogx(freqs, T_phase_deg, 'tab:red', lw=2.2)
ax_ph.axhline(-180, color='black', lw=0.8, ls='-')
ax_ph.axvline(fc_achieved, color='darkorange', ls='--', lw=1.2)
ax_ph.annotate(f'Phase Margin = {pm_achieved:.1f}°',
               xy=(fc_achieved, -180 + pm_achieved), xytext=(fc_achieved*1.5, -120),
               arrowprops=dict(facecolor='darkorange', shrink=0.08, width=1.5, headwidth=6),
               fontweight='bold', color='darkorange')
ax_ph.set_xlabel('Frequency [Hz]', fontsize=11, fontweight='bold')
ax_ph.set_ylabel('Phase [deg]', fontsize=11, fontweight='bold')
ax_ph.grid(True, which='both', ls='-', alpha=0.3)
ax_ph.set_ylim(-240, 20)

plt.tight_layout()
bode_path = os.path.join(FIG_DIR, "ti_buck_type3_bode.png")
fig.savefig(bode_path, dpi=200)
plt.close(fig)
print(f"Saved: {bode_path}")

# Plot 2: PCMC vs VMC Plant Comparison
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

ax1.semilogx(freqs, 20*np.log10(np.abs(Gvd_eval)), 'tab:blue', lw=2.0, label='Voltage-Mode Plant Gvd(s) [2nd Order LC]')
ax1.semilogx(freqs, 20*np.log10(np.abs(Gvc_eval)), 'tab:green', lw=2.0, label='Current-Mode Plant Gvc(s) [1st Order Dominated]')
ax1.axvline(fLC, color='tab:blue', ls=':', label=f'LC Resonance ({fLC/1e3:.1f} kHz)')
ax1.set_ylabel('Magnitude [dB]', fontsize=11, fontweight='bold')
ax1.set_title('Small-Signal Plant Architecture: Voltage-Mode vs. Peak Current-Mode', fontsize=12, fontweight='bold')
ax1.grid(True, which='both', alpha=0.3)
ax1.legend(loc='lower left')

ax2.semilogx(freqs, np.unwrap(np.angle(Gvd_eval))*180/np.pi, 'tab:blue', lw=2.0)
ax2.semilogx(freqs, np.unwrap(np.angle(Gvc_eval))*180/np.pi, 'tab:green', lw=2.0)
ax2.axvline(fLC, color='tab:blue', ls=':')
ax2.set_xlabel('Frequency [Hz]', fontsize=11, fontweight='bold')
ax2.set_ylabel('Phase [deg]', fontsize=11, fontweight='bold')
ax2.grid(True, which='both', alpha=0.3)

plt.tight_layout()
pcmc_vs_vmc_path = os.path.join(FIG_DIR, "pcmc_vs_vmc_plant.png")
fig.savefig(pcmc_vs_vmc_path, dpi=200)
plt.close(fig)
print(f"Saved: {pcmc_vs_vmc_path}")

# Plot 3: Power Efficiency & Loss Breakdown Stacked Area
fig, (ax_eta, ax_loss) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax_eta.plot(Iload_arr, eta_arr, 'darkblue', lw=2.5)
ax_eta.axhline(peak_eta, color='red', ls=':', alpha=0.7, label=f'Peak Efficiency: {peak_eta:.1f}% @ {peak_eta_I:.1f}A')
ax_eta.axvline(Iout_nom, color='gray', ls='--', alpha=0.7, label=f'Full Load (3A): {full_load_eta:.1f}%')
ax_eta.set_ylabel('Efficiency [%]', fontsize=11, fontweight='bold')
ax_eta.set_title('Efficiency & Loss Breakdown vs. Load Current (Vin=12V, Vout=3.3V, fsw=500kHz)', fontsize=12, fontweight='bold')
ax_eta.grid(True, ls='-', alpha=0.3)
ax_eta.legend(loc='lower right')
ax_eta.set_ylim(75, 100)

labels = ['HS Cond', 'LS Cond', 'HS Switch', 'Inductor DCR', 'Gate Drive', 'Body Diode']
ax_loss.stackplot(Iload_arr,
                  P_cond_hs_arr*1e3,
                  P_cond_ls_arr*1e3,
                  P_sw_hs_arr*1e3,
                  P_dcr_arr*1e3,
                  np.full_like(Iload_arr, P_gate*1e3),
                  P_diode_arr*1e3,
                  labels=labels, alpha=0.85)
ax_loss.set_xlabel('Load Current [A]', fontsize=11, fontweight='bold')
ax_loss.set_ylabel('Power Loss [mW]', fontsize=11, fontweight='bold')
ax_loss.grid(True, ls='-', alpha=0.3)
ax_loss.legend(loc='upper left', ncol=2)

plt.tight_layout()
loss_path = os.path.join(FIG_DIR, "buck_efficiency_and_loss_breakdown.png")
fig.savefig(loss_path, dpi=200)
plt.close(fig)
print(f"Saved: {loss_path}")
print("ALL DESIGN CALCULATIONS AND PLOTS COMPLETED SUCCESSFULLY.")
