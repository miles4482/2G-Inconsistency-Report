# 2G Cell Parameter Comparison — Pre vs Post

| Item | Value |
|---|---|
| Pre dump | 26 April 2026 (`2G Cell Parameters Data_26April26_Pre`) |
| Post dump | 13 September 2026 (`2G Cell Parameters Data_13Sep26_Post`) |
| Descriptions | `GSM_Parameter List_Huawei_v1.0` |
| Pre cells | 24,899 |
| Post cells | 25,591 |
| Common cells compared | 24,816 |
| New cells in Post | 775 |
| Cells removed since Pre | 83 |
| Parameters with any change | 109 |

Identity columns (BSC/BTS/Cell name/index) were excluded. Rank is by **number of common cells whose value changed**.

Classic TCH drop parameters (handover hysteresis/thresholds, RLT/radio-link timers, power control, RXQUAL HO) **did not change**. The CDR rise lines up with a small set of **network-wide bulk campaigns** plus VAMOS / half-rate / identity changes.

## Highest-priority findings for sudden CDR increase

### 1. Intelligent Access Congestion Control enabled on almost the whole network

On **24,541 cells (98.9%)**:

- `INTACESCONGCTRLSW`: **OFF → ON** (Huawei default/recommended = OFF)
- `INTACESCONGCTRLTHRES`: empty → **5** (recommended **20** — much more sensitive)
- `INTACESCONGCTRLTIMER1`: empty → **1** (recommended **2** — T3122 increases faster)
- `INTACESCONGCTRLTIMER2`: empty → **100** (recommended **5** — inflated T3122 stays high far longer)

Huawei meaning: when ON, the BSC dynamically lengthens the SDCCH (location update) and initial uplink PS access interval to relieve congestion.

KPI: mainly **CSSR / SDCCH congestion / location-update delay**. It can show up as SDCCH drop or assignment failure. Combined with T3122 below, this is the largest access-policy change in the dump.

### 2. T3122 (`IMMREJWAITINDTIMER`) raised 10 → 15 on 24,175 cells (97.4%)

Huawei default and recommended value is **10**. After an immediate assignment reject, the MS waits T3122 before retrying. A larger value makes access harder. Radio impact (Huawei): *If set large, an MS is difficult to access the network.*

### 3. LTE SAI identity rewritten for SRVCC on ~24,046–24,627 cells (~97–99%)

| Parameter | Typical Pre → Post | Cells |
|---|---|---:|
| `LTESAIMCC` | 000 → **470** | 24,046 |
| `LTESAIMNC` | 000 → **02** | 24,046 |
| `LTESAILAC` | 1 (or old LAC) → **15000** | 24,624 |
| `LTESAISAC` | 0 → **15** | 24,627 |

These four values are the SAI used to recognize an **incoming SRVCC handover**. If they do not match what LTE/MME sends, SRVCC is handled as a normal HO (or the reverse). That is a direct CS-continuity / VoLTE→GSM drop mechanism. `SRVCCHOEN` itself changed on only 3 cells (NO→YES), so this SAI rewrite was applied on top of the existing SRVCC-allowed flag.

### 4. VAMOS — Huawei states this increases call drop

- `VAMOSSWITCH` **OFF → ON** on **358 cells**. Huawei: *VAMOS increases capacity by sacrificing quality; quality-related KPIs deteriorate.*
- About **50 further VAMOS mux/demux parameters** were filled from empty → operating values on those same ~358 cells (first-time VAMOS activation).
- Load demux thresholds (`VFRLOADREUSETHD`, `VAMOSLOADREUSELOADTHD`) moved on **~17,187 cells (69%)** in ±1 steps (SON-like). Huawei: a smaller demux threshold keeps VAMOS paired longer and **increases call drop rate more significantly**.

### 5. Cluster changes that also hurt quality

| Change | Cells | Why it matters |
|---|---:|---|
| Fast-return RSRP `FDDFASTRETURNRSRPTH` 32→22 and `TDDFASTRETURNRSRPTH` 28→22 | 603 | Easier GSM→LTE fast return; Huawei warns of ping-pong. Rec=28. |
| `SRVCCRAPIDSELMEASOPTSW` OFF→ON | 603 | SRVCC fast-return measurement optimization |
| `TCHBUSYTHRES` lowered (e.g. 65→20, 80→30, many →0) | 203 | More TCH/H at low load; Huawei: voice quality deteriorates. Rec=60 |
| `AMRTCHHPRIORLOAD` lowered similarly | 195 | More AMR HR; Rec=55 |
| `TIGHTBCCHSWITCH` OFF→ON + related HO/assign thresholds | 75 | Aggressive BCCH reuse |
| `NCC` / `BCC` (BSIC) changed | 636 / 624 | HO failure if neighbors not updated |
| Energy-save `DYNOPENTRXPOWER` YES→NO | 480 | TRX intelligent shutdown **disabled** (usually helps, not hurts, CDR) |

## Network-wide bulk parameter list (max changes first)

| Rank | MO | Parameter ID | Parameter Name | Cells | % | Pre → Post | KPI | Rec |
|---:|---|---|---|---:|---:|---|---|---|
| 1 | GCELLHOBASIC | `LTESAISAC` | LTE SAI SAC | 24,627 | 99.24% | 0 → 15 (24046) | SRVCC HO / CS continuity (VoLTE→GSM) | None |
| 2 | GCELLHOBASIC | `LTESAILAC` | LTE SAI LAC | 24,624 | 99.23% | 1 → 15000 (24046) | SRVCC HO / CS continuity (VoLTE→GSM) | None |
| 3 | GCELLCCCH | `INTACESCONGCTRLSW` | Intelligent Access Congest Ctrl Switch | 24,541 | 98.89% | OFF → ON (24541) | CSSR / SDCCH (access delay); possible SDCCH drop | OFF(Off) |
| 4 | GCELLCCCH | `INTACESCONGCTRLTHRES` | Intelligent Access Congest Ctrl Thres. | 24,541 | 98.89% | (empty) → 5 (24541) | CSSR / SDCCH (access delay); possible SDCCH drop | 20 |
| 5 | GCELLCCCH | `INTACESCONGCTRLTIMER1` | Intelligent Access Congest Ctrl Timer 1 | 24,541 | 98.89% | (empty) → 1 (24541) | CSSR / SDCCH (access delay); possible SDCCH drop | 2 |
| 6 | GCELLCCCH | `INTACESCONGCTRLTIMER2` | Intelligent Access Congest Ctrl Timer 2 | 24,541 | 98.89% | (empty) → 100 (24541) | CSSR / SDCCH (access delay); possible SDCCH drop | 5 |
| 7 | GCELLTMR | `IMMREJWAITINDTIMER` | T3122 | 24,175 | 97.42% | 10 → 15 (24175) | CSSR / SDCCH (access delay); possible SDCCH drop | 10 |
| 8 | GCELLHOBASIC | `LTESAIMCC` | LTE SAI MCC | 24,046 | 96.90% | 000 → 470 (24043) | SRVCC HO / CS continuity (VoLTE→GSM) | None |
| 9 | GCELLHOBASIC | `LTESAIMNC` | LTE SAI MNC | 24,046 | 96.90% | 000 → 02 (24043) | SRVCC HO / CS continuity (VoLTE→GSM) | None |
| 10 | GCELLVAMOS | `VFRLOADREUSETHD` | Load Thld for Low Load VAMOS FR Demultiplexing | 17,187 | 69.26% | 85 → 86 (527) | TCH CDR / MOS (VAMOS quality) | 30 |
| 11 | GCELLVAMOS | `VAMOSLOADREUSELOADTHD` | Load Thres. of Channel Demultiplex | 17,186 | 69.25% | 85 → 86 (527) | TCH CDR / MOS (VAMOS quality) | 25 |
| 12 | GCELLVAMOS | `VAMOSIUOINNERLOADTHD` | Load Thres. in Overlaid Subcell | 11,009 | 44.36% | 95 → 96 (907) | TCH CDR / MOS (VAMOS quality) | 75 |
| 13 | GCELLVAMOS | `VAMOSMULTLOADTHD` | Channel Multiplex Load Thres. | 11,009 | 44.36% | 95 → 96 (907) | TCH CDR / MOS (VAMOS quality) | 75 |
| 14 | GCELLVAMOS | `VFRIUOINNERLOADTHD` | OL Load Threshold for VAMOS FR Multiplexing | 11,009 | 44.36% | 95 → 96 (907) | TCH CDR / MOS (VAMOS quality) | 50 |
| 15 | GCELLVAMOS | `VFRLOADTHD` | Load Threshold for VAMOS FR Multiplexing | 11,009 | 44.36% | 95 → 96 (907) | TCH CDR / MOS (VAMOS quality) | 50 |

## Full changed-parameter list (max changes first)

| Rank | MO | Parameter ID | Parameter Name | Cells Changed | % Common | Change type | Top Pre → Post | KPI |
|---:|---|---|---|---:|---:|---|---|---|
| 1 | GCELLHOBASIC | `LTESAISAC` | LTE SAI SAC | 24,627 | 99.24% | Network-wide bulk change | 0 → 15 (24046); 103 → 15 (3); 45567 → 15 (1); 41686 → 15 (1); 29095 → 15 (1); 48313 → 15 (1); 48543 → 15 (1); 41583 → 15 (1) | SRVCC HO / CS continuity (VoLTE→GSM) |
| 2 | GCELLHOBASIC | `LTESAILAC` | LTE SAI LAC | 24,624 | 99.23% | Network-wide bulk change | 1 → 15000 (24046); 365 → 15000 (144); 363 → 15000 (135); 78 → 15000 (49); 79 → 15000 (48); 368 → 15000 (45); 543 → 15000 (42); 541 → 15000 (30) | SRVCC HO / CS continuity (VoLTE→GSM) |
| 3 | GCELLCCCH | `INTACESCONGCTRLSW` | Intelligent Access Congest Ctrl Switch | 24,541 | 98.89% | Network-wide bulk change | OFF → ON (24541) | CSSR / SDCCH (access delay); possible SDCCH drop |
| 4 | GCELLCCCH | `INTACESCONGCTRLTHRES` | Intelligent Access Congest Ctrl Thres. | 24,541 | 98.89% | Network-wide bulk change | (empty) → 5 (24541) | CSSR / SDCCH (access delay); possible SDCCH drop |
| 5 | GCELLCCCH | `INTACESCONGCTRLTIMER1` | Intelligent Access Congest Ctrl Timer 1 | 24,541 | 98.89% | Network-wide bulk change | (empty) → 1 (24541) | CSSR / SDCCH (access delay); possible SDCCH drop |
| 6 | GCELLCCCH | `INTACESCONGCTRLTIMER2` | Intelligent Access Congest Ctrl Timer 2 | 24,541 | 98.89% | Network-wide bulk change | (empty) → 100 (24541) | CSSR / SDCCH (access delay); possible SDCCH drop |
| 7 | GCELLTMR | `IMMREJWAITINDTIMER` | T3122 | 24,175 | 97.42% | Network-wide bulk change | 10 → 15 (24175) | CSSR / SDCCH (access delay); possible SDCCH drop |
| 8 | GCELLHOBASIC | `LTESAIMCC` | LTE SAI MCC | 24,046 | 96.90% | Network-wide bulk change | 000 → 470 (24043); 0 → 470 (3) | SRVCC HO / CS continuity (VoLTE→GSM) |
| 9 | GCELLHOBASIC | `LTESAIMNC` | LTE SAI MNC | 24,046 | 96.90% | Network-wide bulk change | 000 → 02 (24043); 0 → 02 (3) | SRVCC HO / CS continuity (VoLTE→GSM) |
| 10 | GCELLVAMOS | `VFRLOADREUSETHD` | Load Thld for Low Load VAMOS FR Demultiplexing | 17,187 | 69.26% | Per-cell / SON-like drift | 85 → 86 (527); 86 → 87 (386); 86 → 85 (358); 87 → 86 (324); 80 → 81 (317); 84 → 85 (294); 81 → 82 (290); 85 → 84 (264) | TCH CDR / MOS (VAMOS quality) |
| 11 | GCELLVAMOS | `VAMOSLOADREUSELOADTHD` | Load Thres. of Channel Demultiplex | 17,186 | 69.25% | Per-cell / SON-like drift | 85 → 86 (527); 86 → 87 (386); 86 → 85 (358); 87 → 86 (324); 80 → 81 (317); 84 → 85 (294); 81 → 82 (290); 85 → 84 (264) | TCH CDR / MOS (VAMOS quality) |
| 12 | GCELLVAMOS | `VAMOSIUOINNERLOADTHD` | Load Thres. in Overlaid Subcell | 11,009 | 44.36% | Per-cell / SON-like drift | 95 → 96 (907); 93 → 94 (772); 94 → 95 (673); 96 → 95 (575); 92 → 93 (556); 94 → 93 (519); 96 → 97 (445); 93 → 92 (438) | TCH CDR / MOS (VAMOS quality) |
| 13 | GCELLVAMOS | `VAMOSMULTLOADTHD` | Channel Multiplex Load Thres. | 11,009 | 44.36% | Per-cell / SON-like drift | 95 → 96 (907); 93 → 94 (772); 94 → 95 (673); 96 → 95 (575); 92 → 93 (556); 94 → 93 (519); 96 → 97 (445); 93 → 92 (438) | TCH CDR / MOS (VAMOS quality) |
| 14 | GCELLVAMOS | `VFRIUOINNERLOADTHD` | OL Load Threshold for VAMOS FR Multiplexing | 11,009 | 44.36% | Per-cell / SON-like drift | 95 → 96 (907); 93 → 94 (772); 94 → 95 (673); 96 → 95 (575); 92 → 93 (556); 94 → 93 (519); 96 → 97 (445); 93 → 92 (438) | TCH CDR / MOS (VAMOS quality) |
| 15 | GCELLVAMOS | `VFRLOADTHD` | Load Threshold for VAMOS FR Multiplexing | 11,009 | 44.36% | Per-cell / SON-like drift | 95 → 96 (907); 93 → 94 (772); 94 → 95 (673); 96 → 95 (575); 92 → 93 (556); 94 → 93 (519); 96 → 97 (445); 93 → 92 (438) | TCH CDR / MOS (VAMOS quality) |
| 16 | GCELL | `NCC` | NCC | 636 | 2.56% | Per-cell / SON-like drift | 7 → 2 (19); 3 → 4 (18); 6 → 7 (17); 1 → 3 (17); 7 → 4 (17); 1 → 6 (17); 7 → 3 (16); 2 → 1 (16) | HO / identity (can cause HO fail & drop) |
| 17 | GCELL | `BCC` | BCC | 624 | 2.51% | Per-cell / SON-like drift | 4 → 3 (19); 2 → 1 (19); 0 → 1 (18); 4 → 7 (18); 3 → 4 (17); 6 → 4 (16); 7 → 2 (15); 0 → 6 (15) | HO / identity (can cause HO fail & drop) |
| 18 | GCELLPRIEUTRANSYS | `FDDFASTRETURNRSRPTH` | RSRP Threshold for Fast FDD LTE Reselection | 603 | 2.43% | Cluster bulk change | 32 → 22 (603) | CSFB/SRVCC return & ping-pong |
| 19 | GCELLPRIEUTRANSYS | `TDDFASTRETURNRSRPTH` | RSRP Threshold for Fast TDD LTE Reselection | 603 | 2.43% | Cluster bulk change | 28 → 22 (603) | CSFB/SRVCC return & ping-pong |
| 20 | GCELLSRVCC | `SRVCCRAPIDSELBASECFGSW` | Config Based SRVCC Fast Reselect Switch | 603 | 2.43% | Cluster bulk change | (empty) → OFF (603) | SRVCC HO / CS continuity (VoLTE→GSM) |
| 21 | GCELLSRVCC | `SRVCCRAPIDSELMEASOPTSW` | SRVCC Fast Reselect Meas Optimize Switch | 603 | 2.43% | Cluster bulk change | OFF → ON (603) | SRVCC HO / CS continuity (VoLTE→GSM) |
| 22 | GCELLBASICPARA | `CONCENINTELSHUTDOWNSW` | Concentric Intelligent Shutdown Switch | 480 | 1.93% | Limited / targeted change | OFF → (empty) (480) | Energy saving (coverage/drop if ON) |
| 23 | GCELLBASICPARA | `DYNOPENTRXPOWER` | Allow Dynamic Shutdown of TRX | 480 | 1.93% | Limited / targeted change | YES → NO (480) | Energy saving (coverage/drop if ON) |
| 24 | GCELLBASICPARA | `ENERGYCONSRVPREFSW` | Energy Conserve Prefer Switch | 480 | 1.93% | Limited / targeted change | OFF → (empty) (480) | Energy saving (coverage/drop if ON) |
| 25 | GCELLBASICPARA | `PDCHTRXDYNSHUTSW` | PDCH TRX Intelligent Shutdown Switch | 480 | 1.93% | Limited / targeted change | DISABLED → (empty) (480) | Energy saving (coverage/drop if ON) |
| 26 | GCELLVAMOS | `MULTALLOWBEFORECONN` | Allow HO Multiplex Before CONNECT ACK | 365 | 1.47% | Limited / targeted change | (empty) → OFF (358); ON → OFF (7) | TCH CDR / MOS (VAMOS quality) |
| 27 | GCELLVAMOS | `MUTESAICSWITCH` | Mute SAIC Terminal Processing Switch | 365 | 1.47% | Limited / targeted change | (empty) → OFF (358); ON → OFF (7) | TCH CDR / MOS (VAMOS quality) |
| 28 | GCELLVAMOS | `SAICPROMSSWITCH` | Problem SAIC Terminal Processing Switch | 365 | 1.47% | Limited / targeted change | (empty) → OFF (358); ON → OFF (7) | TCH CDR / MOS (VAMOS quality) |
| 29 | GCELLVAMOS | `VAMOSINTRAHODLQUALTHD` | DL Rx Qual. Thres. of Established Calls | 365 | 1.47% | Limited / targeted change | (empty) → 50 (358); 40 → 50 (7) | TCH CDR / MOS (VAMOS quality) |
| 30 | GCELLVAMOS | `VAMOSINTRAHODLRXLEVTHD` | DL Rx Lev. Thres. of VAMOS Calls | 365 | 1.47% | Limited / targeted change | (empty) → 27 (358); 17 → 27 (7) | TCH CDR / MOS (VAMOS quality) |
| 31 | GCELLVAMOS | `VAMOSINTRAHOULQUALTHD` | UL Rx Qual. Thres. of Established Calls | 365 | 1.47% | Limited / targeted change | (empty) → 50 (358); 30 → 50 (7) | TCH CDR / MOS (VAMOS quality) |
| 32 | GCELLVAMOS | `VAMOSINTRAHOULRXLEVTHD` | UL RX Level Thld for Channel Multiplexing | 365 | 1.47% | Limited / targeted change | (empty) → 20 (358); 10 → 20 (7) | TCH CDR / MOS (VAMOS quality) |
| 33 | GCELLVAMOS | `VAMOSNONESAICALLOW` | Allow VAMOS-1&NonSAIC and SAIC&NonSAIC | 365 | 1.47% | Limited / targeted change | (empty) → OFF (358); ON → OFF (7) | TCH CDR / MOS (VAMOS quality) |
| 34 | GCELLVAMOS | `SPEMSIDEDLRXLEVTHD` | DL RX Level Thd of Terminal Identify | 364 | 1.47% | Limited / targeted change | (empty) → 47 (358); 25 → 47 (6) | TCH CDR / MOS (VAMOS quality) |
| 35 | GCELLVAMOS | `SPEMSIDELOAD` | LO Thresh upon Terminal Identify Request | 364 | 1.47% | Limited / targeted change | (empty) → 20 (358); 40 → 20 (6) | TCH CDR / MOS (VAMOS quality) |
| 36 | GCELLVAMOS | `SPEMSIDEMAXCALLS` | Max Calls in Terminal Identification | 364 | 1.47% | Limited / targeted change | (empty) → 10 (358); 20 → 10 (6) | TCH CDR / MOS (VAMOS quality) |
| 37 | GCELLVAMOS | `SPEMSIDEULRXLEVTHD` | UL RX Level Thd of Terminal Identify | 364 | 1.47% | Limited / targeted change | (empty) → 40 (358); 18 → 40 (6) | TCH CDR / MOS (VAMOS quality) |
| 38 | GCELLVAMOS | `VAMOSASSULQUALTHDOFFSET` | Channel Multiplex Rx Qual. Thres. Offset in Asgmt. | 364 | 1.47% | Limited / targeted change | (empty) → 0 (358); 4 → 0 (6) | TCH CDR / MOS (VAMOS quality) |
| 39 | GCELLVAMOS | `VAMOSBQDEMUXPENSW` | Enable BQ VAMOS Channel Demultiplex Penalty | 364 | 1.47% | Limited / targeted change | (empty) → ON (358); OFF → ON (6) | TCH CDR / MOS (VAMOS quality) |
| 40 | GCELLVAMOS | `VAMOSMAINTSC` | Primary TSC in VAMOS | 364 | 1.47% | Limited / targeted change | (empty) → 0 (358); 2 → 0 (2); 1 → 0 (1); 3 → 0 (1); 7 → 0 (1); 6 → 0 (1) | TCH CDR / MOS (VAMOS quality) |
| 41 | GCELLVAMOS | `VAMOSSUBTSC` | Secondary TSC in VAMOS | 364 | 1.47% | Limited / targeted change | (empty) → 2 (358); 0 → 2 (2); 7 → 2 (1); 4 → 2 (1); 1 → 2 (1); 5 → 2 (1) | TCH CDR / MOS (VAMOS quality) |
| 42 | GCELLVAMOS | `OPTVAMOSCHNMULALG` | Opt VAMOS Channel Multiplexing Alg Allowed | 358 | 1.44% | Limited / targeted change | (empty) → NO (358) | TCH CDR / MOS (VAMOS quality) |
| 43 | GCELLVAMOS | `SAICWHTMSIDENTSW` | SAIC White MS Identification Switch | 358 | 1.44% | Limited / targeted change | (empty) → OFF (358) | TCH CDR / MOS (VAMOS quality) |
| 44 | GCELLVAMOS | `SPEMSIDEATCBTHD` | ATCB Thres of Terminal Identify | 358 | 1.44% | Limited / targeted change | (empty) → 68 (358) | TCH CDR / MOS (VAMOS quality) |
| 45 | GCELLVAMOS | `SPEMSIDEDLRXQUALTHD` | DL RX Qual Thres of Terminal Identify | 358 | 1.44% | Limited / targeted change | (empty) → 10 (358) | TCH CDR / MOS (VAMOS quality) |
| 46 | GCELLVAMOS | `SPEMSIDELASTTIMES` | Satisfy Time for Terminal Identify | 358 | 1.44% | Limited / targeted change | (empty) → 3 (358) | TCH CDR / MOS (VAMOS quality) |
| 47 | GCELLVAMOS | `SPEMSIDESTATTIMES` | Watch Time for Terminal Identify | 358 | 1.44% | Limited / targeted change | (empty) → 3 (358) | TCH CDR / MOS (VAMOS quality) |
| 48 | GCELLVAMOS | `SPEMSIDEULRXQUALTHD` | UL RX Qual Thres of Terminal Identify | 358 | 1.44% | Limited / targeted change | (empty) → 10 (358) | TCH CDR / MOS (VAMOS quality) |
| 49 | GCELLVAMOS | `VAMOSANTULRXLEVDIFFTHD` | Main and Diversity UL RX Level Diff Thld for MUX | 358 | 1.44% | Limited / targeted change | (empty) → 9 (358) | TCH CDR / MOS (VAMOS quality) |
| 50 | GCELLVAMOS | `VAMOSASSDLRXLEVTHDOFFSET` | Rx Lev. Thres. Offset During Assignment | 358 | 1.44% | Limited / targeted change | (empty) → 128 (358) | TCH CDR / MOS (VAMOS quality) |
| 51 | GCELLVAMOS | `VAMOSASSLOADOFT` | Multiplexing Load Thres. Offset in Assignment | 358 | 1.44% | Limited / targeted change | (empty) → 100 (358) | TCH CDR / MOS (VAMOS quality) |
| 52 | GCELLVAMOS | `VAMOSASSMULTATCBOFFSET` | Channel Multiplex ATCB Thres. Offset in Asgmt. | 358 | 1.44% | Limited / targeted change | (empty) → 2 (358) | TCH CDR / MOS (VAMOS quality) |
| 53 | GCELLVAMOS | `VAMOSASSSWITCH` | Allow Channel Multiplex in Assignment | 358 | 1.44% | Limited / targeted change | (empty) → ON (358) | TCH CDR / MOS (VAMOS quality) |
| 54 | GCELLVAMOS | `VAMOSDEPOLRXQUALOFT` | OL BQ Demultiplexing Rx Quality Thres. Offset | 358 | 1.44% | Limited / targeted change | (empty) → 70 (358) | TCH CDR / MOS (VAMOS quality) |
| 55 | GCELLVAMOS | `VAMOSFACCHENHANCE` | VAMOS FACCH Send Enhance Switch | 358 | 1.44% | Limited / targeted change | (empty) → ON (358) | TCH CDR / MOS (VAMOS quality) |
| 56 | GCELLVAMOS | `VAMOSINTRAHONONESAICATCBTHD` | ATCB Thres. of Established Non-SAIC Calls | 358 | 1.44% | Limited / targeted change | (empty) → 82 (358) | TCH CDR / MOS (VAMOS quality) |
| 57 | GCELLVAMOS | `VAMOSINTRAHOSAICATCBTHD` | ATCB Thres. of Established SAIC Calls | 358 | 1.44% | Limited / targeted change | (empty) → 66 (358) | TCH CDR / MOS (VAMOS quality) |
| 58 | GCELLVAMOS | `VAMOSINTRAHOSWITCH` | Allow Channel Multiplex via In-Cell HO | 358 | 1.44% | Limited / targeted change | (empty) → ON (358) | TCH CDR / MOS (VAMOS quality) |
| 59 | GCELLVAMOS | `VAMOSINTRAHOVAMOS1ATCBTHD` | ATCB Thres. of Established VAMOS-1 Calls | 358 | 1.44% | Limited / targeted change | (empty) → 66 (358) | TCH CDR / MOS (VAMOS quality) |
| 60 | GCELLVAMOS | `VAMOSINTRAHOVAMOS2ATCBTHD` | ATCB Thres. of Established VAMOS-2 Calls | 358 | 1.44% | Limited / targeted change | (empty) → 66 (358) | TCH CDR / MOS (VAMOS quality) |
| 61 | GCELLVAMOS | `VAMOSIUOINNERATCBTHD` | ATCB Offset in Overlaid Subcell | 358 | 1.44% | Limited / targeted change | (empty) → 130 (358) | TCH CDR / MOS (VAMOS quality) |
| 62 | GCELLVAMOS | `VAMOSLOADREUSESWITCH` | Channel Demultiplex on Low Cell Load | 358 | 1.44% | Limited / targeted change | (empty) → ON (358) | TCH CDR / MOS (VAMOS quality) |
| 63 | GCELLVAMOS | `VAMOSMSENABLE` | MS Support VAMOS I&II Enable | 358 | 1.44% | Limited / targeted change | (empty) → ON (358) | TCH CDR / MOS (VAMOS quality) |
| 64 | GCELLVAMOS | `VAMOSNODLMRHOOPTSW` | VAMOS No DL MR Handover Optimize Switch | 358 | 1.44% | Limited / targeted change | (empty) → OFF (358) | TCH CDR / MOS (VAMOS quality) |
| 65 | GCELLVAMOS | `VAMOSOLDCALLLASTTIMES` | Duration of Satisfying Candidate VAMOS Call | 358 | 1.44% | Limited / targeted change | (empty) → 2 (358) | TCH CDR / MOS (VAMOS quality) |
| 66 | GCELLVAMOS | `VAMOSOLDCALLSTATTIMES` | Watch Time of Candidate Calls | 358 | 1.44% | Limited / targeted change | (empty) → 3 (358) | TCH CDR / MOS (VAMOS quality) |
| 67 | GCELLVAMOS | `VAMOSOLRXLEVOFT` | OL Multiplexing Rx Level Thres. Offset | 358 | 1.44% | Limited / targeted change | (empty) → 128 (358) | TCH CDR / MOS (VAMOS quality) |
| 68 | GCELLVAMOS | `VAMOSOLRXQUALOFT` | OL Multiplexing Rx Quality Thres. Offset | 358 | 1.44% | Limited / targeted change | (empty) → 70 (358) | TCH CDR / MOS (VAMOS quality) |
| 69 | GCELLVAMOS | `VAMOSPATHLOSSMAXDIFFVALUE` | Path Loss Offset Thres. of VAMOS Call | 358 | 1.44% | Limited / targeted change | (empty) → 20 (358) | TCH CDR / MOS (VAMOS quality) |
| 70 | GCELLVAMOS | `VAMOSQUALREUSEDOWNLINKQUALTHD` | DL RX Bad Qual. Demultiplex Thres. | 358 | 1.44% | Limited / targeted change | (empty) → 50 (358) | TCH CDR / MOS (VAMOS quality) |
| 71 | GCELLVAMOS | `VAMOSQUALREUSELASTTIMES` | Bad Qual. Duration for Demultiplex | 358 | 1.44% | Limited / targeted change | (empty) → 1 (358) | TCH CDR / MOS (VAMOS quality) |
| 72 | GCELLVAMOS | `VAMOSQUALREUSESTATTIMES` | Watch Time of Bad Qual. for Demultiplex | 358 | 1.44% | Limited / targeted change | (empty) → 1 (358) | TCH CDR / MOS (VAMOS quality) |
| 73 | GCELLVAMOS | `VAMOSQUALREUSESWITCH` | Channel Demultiplex on Bad Qual. | 358 | 1.44% | Limited / targeted change | (empty) → ON (358) | TCH CDR / MOS (VAMOS quality) |
| 74 | GCELLVAMOS | `VAMOSQUALREUSEUPLINKQUALTHD` | UL RX Bad Qual. Demultiplex Thres. | 358 | 1.44% | Limited / targeted change | (empty) → 50 (358) | TCH CDR / MOS (VAMOS quality) |
| 75 | GCELLVAMOS | `VAMOSQUALUNDOPNTSWITCH` | BQ VAMOS Channel Demultiplex Optimize | 358 | 1.44% | Limited / targeted change | (empty) → ON (358) | TCH CDR / MOS (VAMOS quality) |
| 76 | GCELLVAMOS | `VAMOSQUALUNDOPNTTIMER` | BQ VAMOS Channel Demultiplex Penalty Period | 358 | 1.44% | Limited / targeted change | (empty) → 5 (358) | TCH CDR / MOS (VAMOS quality) |
| 77 | GCELLVAMOS | `VAMOSSWITCH` | VAMOS Switch | 358 | 1.44% | Limited / targeted change | OFF → ON (358) | TCH CDR / MOS (VAMOS quality) |
| 78 | GCELLVAMOS | `VAMOSTSCAUTOMAPSW` | VAMOS TSC Automatic Mapping Switch | 358 | 1.44% | Limited / targeted change | (empty) → ON (358) | TCH CDR / MOS (VAMOS quality) |
| 79 | GCELLVAMOS | `VFRATCBOFFSET` | ATCB Thld Offset for VAMOS FR Multiplexing | 358 | 1.44% | Limited / targeted change | (empty) → 64 (358) | TCH CDR / MOS (VAMOS quality) |
| 80 | GCELLVAMOS | `VFRQUALOFFSET` | RX Quality Thld Offset for VAMOS FR Multiplex | 358 | 1.44% | Limited / targeted change | (empty) → 0 (358) | TCH CDR / MOS (VAMOS quality) |
| 81 | GCELLVAMOS | `VFRQUALREUSEOFFSET` | RX Quality Thld Offset for BQ FR Demultiplexing | 358 | 1.44% | Limited / targeted change | (empty) → 0 (358) | TCH CDR / MOS (VAMOS quality) |
| 82 | GCELLVAMOS | `VFRRXLEVOFFSET` | RX Level Thld Offset for VAMOS FR Multiplexing | 358 | 1.44% | Limited / targeted change | (empty) → 128 (358) | TCH CDR / MOS (VAMOS quality) |
| 83 | GCELLVAMOS | `VFRTOVHRENABLE` | Enable VAMOS FR to HR Multiplexing Conversion | 358 | 1.44% | Limited / targeted change | (empty) → ON (358) | TCH CDR / MOS (VAMOS quality) |
| 84 | GCELLCHMGAD | `TCHBUSYTHRES` | TCH Traffic Busy Threshold | 203 | 0.82% | Per-cell / SON-like drift | 65 → 20 (15); 3 → 0 (13); 80 → 30 (13); 10 → 0 (12); 5 → 0 (10); 1 → 0 (9); 80 → 40 (8); 50 → 20 (8) | TCH CDR / MOS (more TCHH) |
| 85 | GCELLCHMGAD | `AMRTCHHPRIORLOAD` | AMR TCH/H Prior Cell Load Threshold | 195 | 0.79% | Per-cell / SON-like drift | 64 → 19 (15); 5 → 0 (11); 2 → 0 (10); 80 → 29 (9); 49 → 19 (8); 64 → 29 (7); 89 → 29 (7); 89 → 59 (6) | TCH CDR / MOS (more TCHH) |
| 86 | GCELLCHMGAD | `TIGHTBCCHASSMAINBCCHLEV` | Level Thresh for Assign BCCH Under TBCCH | 75 | 0.30% | Limited / targeted change | 30 → 25 (75) | TCH CDR / CSSR (tight BCCH reuse) |
| 87 | GCELLCHMGAD | `TIGHTBCCHASSMAINBCCHQUAL` | Quality Thresh for Assign BCCH Under TBCCH | 75 | 0.30% | Limited / targeted change | 1 → 2 (75) | TCH CDR / CSSR (tight BCCH reuse) |
| 88 | GCELLCHMGBASIC | `TIGHTBCCHSWITCH` | TIGHT BCCH Switch | 75 | 0.30% | Limited / targeted change | OFF → ON (75) | TCH CDR / CSSR (tight BCCH reuse) |
| 89 | GCELLHOAD | `TIGHTBCCHHOLOADTHRES` | Non-BCCH Load Threshold for TIGHT BCCH HO | 75 | 0.30% | Limited / targeted change | 80 → 85 (75) | TCH CDR / CSSR (tight BCCH reuse) |
| 90 | GCELL | `LAC` | Cell LAC | 60 | 0.24% | Limited / targeted change | 3103 → 3111 (15); 3115 → 3116 (6); 3116 → 3108 (6); 3103 → 3105 (3); 6315 → 6307 (3); 3116 → 3111 (3); 3103 → 3108 (3); 6302 → 6305 (3) | HO / identity (can cause HO fail & drop) |
| 91 | GCELLOTHEXT | `RESERVEDIDLECH` | Reserved TCH Number for PA Turning On | 33 | 0.13% | Limited / targeted change | 2 → 3 (33) | Other |
| 92 | GCELLDYNTURNOFF | `TURNOFFCELLSTPTIME` | Dyn. Turning Off Cell Stop Time | 15 | 0.06% | Limited / targeted change | 08:00 → 07:00 (2); 10:00 → 09:00 (2); 23:59 → 18:00 (1); 23:59 → 19:00 (1); 13:00 → 11:00 (1); 23:59 → 10:00 (1); 18:00 → 11:00 (1); 23:59 → 07:00 (1) | Other |
| 93 | GCELLDYNTURNOFF | `COCOVLEVELTHLD` | Joint Co-Coverage Level Threshold | 10 | 0.04% | Limited / targeted change | (empty) → 20 (10) | Other |
| 94 | GCELLDYNTURNOFF | `COCOVRATIOTHLD` | Joint Co-Coverage Ratio Threshold | 10 | 0.04% | Limited / targeted change | (empty) → 90 (10) | Other |
| 95 | GCELLDYNTURNOFF | `LOWBANDCOTURNOFFSW` | Low Band Joint Turn-off Switch | 10 | 0.04% | Limited / targeted change | (empty) → OFF (10) | Radio KPI related |
| 96 | GCELLDYNTURNOFF | `PREFERTURNOFFBCCHTRXSW` | Preferentially Turn Off BCCH TRX Switch | 10 | 0.04% | Limited / targeted change | ON → (empty) (10) | Radio KPI related |
| 97 | GCELLDYNTURNOFF | `SAMECVGCELLID` | Same Coverage Cell No | 10 | 0.04% | Limited / targeted change | 613 → (empty) (1); 177 → (empty) (1); 314 → (empty) (1); 1518 → (empty) (1); 509 → (empty) (1); 1825 → (empty) (1); 1818 → (empty) (1); 1300 → (empty) (1) | Radio KPI related |
| 98 | GCELLDYNTURNOFF | `TURNOFFENABLE` | Enable Turning Off Cell | 10 | 0.04% | Limited / targeted change | ENABLE → AUTOCOTURNOFF (10) | Other |
| 99 | GCELLVAMOS | `MUTESAICIDESWITCH` | Auto Mute SAIC Identification Switch | 7 | 0.03% | Limited / targeted change | OFF → (empty) (7) | TCH CDR / MOS (VAMOS quality) |
| 100 | GCELLVAMOS | `SAICALPHAJUMPPRD` | Faulty SAIC MS Alpha Hop Modulate Period | 7 | 0.03% | Limited / targeted change | 2 → (empty) (7) | TCH CDR / MOS (VAMOS quality) |
| 101 | GCELLVAMOS | `SAICALPHAJUMPVALUE` | Faulty SAIC MS Alpha Hop Modulate Value | 7 | 0.03% | Limited / targeted change | 4 → (empty) (7) | TCH CDR / MOS (VAMOS quality) |
| 102 | GCELLVAMOS | `SAICPROMSIDESWITCH` | Problem SAIC Terminal Identify Switch | 7 | 0.03% | Limited / targeted change | OFF → (empty) (7) | TCH CDR / MOS (VAMOS quality) |
| 103 | GCELLVAMOS | `UNKOWNSAICMULTSWITCH` | Allow Multiplex for Unknown SAIC MS | 7 | 0.03% | Limited / targeted change | ON → (empty) (7) | TCH CDR / MOS (VAMOS quality) |
| 104 | GCELL | `ACTSTATUS` | Active Status | 5 | 0.02% | Limited / targeted change | DEACTIVATED → ACTIVATED (5) | Other |
| 105 | GCELLDYNTURNOFF | `TURNOFFCELLSTRTIME` | Dyn. Turning Off Cell Start Time | 3 | 0.01% | Limited / targeted change | 01:00 → 00:00 (1); 00:00 → 02:00 (1); 00:00 → 01:00 (1) | Other |
| 106 | GCELLHOBASIC | `SRVCCHOEN` | SRVCC Handover Allowed | 3 | 0.01% | Limited / targeted change | NO → YES (3) | SRVCC HO / CS continuity (VoLTE→GSM) |
| 107 | GCELLBASICPARA | `MAXTA` | Max TA | 1 | 0.00% | Limited / targeted change | 2 → 4 (1) | TCH CDR (timing / coverage) |
| 108 | GCELLDYNTURNOFF | `SAMECVGCELLLOADTHRD` | Same Coverage Cell Load Threshold | 1 | 0.00% | Limited / targeted change | 50 → 1 (1) | Other |
| 109 | GCELLDYNTURNOFF | `TURNONCELLLOADTHRD` | Dyn. Turning On Cell Load Threshold | 1 | 0.00% | Limited / targeted change | 80 → 2 (1) | Other |

## Descriptions of the top bulk changes (from Huawei parameter list)

### 1. GCELLHOBASIC / `LTESAISAC` — LTE SAI SAC

- Cells changed: **24,627** (99.24% of 24,816)
- Value changes: 0 → 15 (24046); 103 → 15 (3); 45567 → 15 (1); 41686 → 15 (1); 29095 → 15 (1); 48313 → 15 (1); 48543 → 15 (1); 41583 → 15 (1)
- Default: 0 · Recommended: None
- Meaning: SAC parameter in SAI for an SRVCC handover. The BSC interprets the handover request message as an SRVCC handover request when all the following conditions are met: "SRVCCHOEN" in the "SET GCELLHOBASIC" command is set to YES(Yes).  The source cell ID type in the incoming BSC handover request message is SAI. The values of "LTE SAI MCC", "LTE SAI MNC", "LTE SAI LAC", "LTE SAI SAC" for the source cell carried in the incoming BSC handover request message are consistent with those configured on the BSC.
- Radio impact: None

### 2. GCELLHOBASIC / `LTESAILAC` — LTE SAI LAC

- Cells changed: **24,624** (99.23% of 24,816)
- Value changes: 1 → 15000 (24046); 365 → 15000 (144); 363 → 15000 (135); 78 → 15000 (49); 79 → 15000 (48); 368 → 15000 (45); 543 → 15000 (42); 541 → 15000 (30)
- Default: 1 · Recommended: None
- Meaning: LAC parameter in SAI for an SRVCC handover. The BSC interprets the handover request message as an SRVCC handover request when all the following conditions are met: "SRVCCHOEN" in the "SET GCELLHOBASIC" command is set to YES(Yes).  The source cell ID type in the incoming BSC handover request message is SAI. The values of "LTE SAI MCC", "LTE SAI MNC", "LTE SAI LAC", "LTE SAI SAC" for the source cell carried in the incoming BSC handover request message are consistent with those configured on the BSC.
- Radio impact: None

### 3. GCELLCCCH / `INTACESCONGCTRLSW` — Intelligent Access Congest Ctrl Switch

- Cells changed: **24,541** (98.89% of 24,816)
- Value changes: OFF → ON (24541)
- Default: OFF(Off) · Recommended: OFF(Off)
- Meaning: Whether to enable the intelligent access congestion control function. When this parameter is set to ON(On), this function is enabled. The BSC dynamically adjusts the SDCCH access interval (location update) and initial uplink PS access interval to relieve network congestion. When this parameter is set to OFF(Off), this function is disabled.
- Radio impact: Setting this parameter to ON(On) increases the SDCCH access interval (location update) and initial uplink PS access interval and decreases the SDCCH and uplink TBF congestion rates.

### 4. GCELLCCCH / `INTACESCONGCTRLTHRES` — Intelligent Access Congest Ctrl Thres.

- Cells changed: **24,541** (98.89% of 24,816)
- Value changes: (empty) → 5 (24541)
- Default: 20 · Recommended: 20
- Meaning: Threshold for triggering intelligent access congestion control. This parameter is used to check the congestion status of the location update SDCCH or uplink initial PS access.
- Radio impact: Setting this parameter to a small value decreases the SDCCH and uplink TBF congestion rates.

### 5. GCELLCCCH / `INTACESCONGCTRLTIMER1` — Intelligent Access Congest Ctrl Timer 1

- Cells changed: **24,541** (98.89% of 24,816)
- Value changes: (empty) → 1 (24541)
- Default: 2 · Recommended: 2
- Meaning: Increased value for timer T3122. This parameter is used with "IntAcesCongCtrlThres" to dynamically specify the increase of the cell access interval.  The BSC starts the timer specified by this parameter when an immediate assignment fails but this timer is not started.  If the timer specified by this parameter has not expired, the increased T3122 value remains unchanged.  If the timer specified by this parameter expires, the BSC stops the timer. If the congestion rate of SDCCH access (location update) or initial uplink PS access is greater than or equal to the value of "IntAcesCongCtrlThres" within the duration specified by the timer, the value of T3122 for SDCCH or PDCH access is incremen...
- Radio impact: Setting this parameter to a small value decreases the SDCCH congestion rate and uplink TBF congestion rate, but increases the location update and uplink initial PS access intervals.

### 6. GCELLCCCH / `INTACESCONGCTRLTIMER2` — Intelligent Access Congest Ctrl Timer 2

- Cells changed: **24,541** (98.89% of 24,816)
- Value changes: (empty) → 100 (24541)
- Default: 5 · Recommended: 5
- Meaning: Decreased value for timer T3122. This parameter is used with "IntAcesCongCtrlThres" to dynamically specify the decrease of the cell access interval.  The BSC automatically starts the timer specified by this parameter when the timer specified by "IntAcesCongCtrlTimer1" starts.  If the timer specified by this parameter has not expired, the decreased T3122 value remains unchanged.  When the timer specified by this parameter expires, if the congestion rate of SDCCH access (location update) or initial uplink PS access is less than the value of "IntAcesCongCtrlThres" within the duration specified by this timer, the value of T3122 for SDCCH access or initial uplink PS access is decreased by 1. O...
- Radio impact: Setting this parameter to a large value increases the location update interval and uplink initial PS access interval.

### 7. GCELLTMR / `IMMREJWAITINDTIMER` — T3122

- Cells changed: **24,175** (97.42% of 24,816)
- Value changes: 10 → 15 (24175)
- Default: 10 · Recommended: 10
- Meaning: Timer carried by the Wait Indication information element when the BSC sends an immediate assignment reject or DTM reject message to an MS. After the MS receives the immediate assignment reject or DTM reject message, the MS does not reattempt to access the network until the timer expires.
- Radio impact: If this parameter is set to a large value, an MS is difficult to access the network. If this parameter is set to a small value, the channel load increases and the network access rate for the MS decreases.

### 8. GCELLHOBASIC / `LTESAIMCC` — LTE SAI MCC

- Cells changed: **24,046** (96.90% of 24,816)
- Value changes: 000 → 470 (24043); 0 → 470 (3)
- Default: 000 · Recommended: None
- Meaning: MCC parameter in SAI for an SRVCC handover. The BSC interprets the handover request message as an SRVCC handover request when all the following conditions are met: "SRVCCHOEN" in the "SET GCELLHOBASIC" command is set to YES(Yes).  The source cell ID type in the incoming BSC handover request message is SAI. The values of "LTE SAI MCC", "LTE SAI MNC", "LTE SAI LAC", "LTE SAI SAC" for the source cell carried in the incoming BSC handover request message are consistent with those configured on the BSC.
- Radio impact: None

### 9. GCELLHOBASIC / `LTESAIMNC` — LTE SAI MNC

- Cells changed: **24,046** (96.90% of 24,816)
- Value changes: 000 → 02 (24043); 0 → 02 (3)
- Default: 000 · Recommended: None
- Meaning: MNC parameter in SAI for an SRVCC handover. The BSC interprets the handover request message as an SRVCC handover request when all the following conditions are met: "SRVCCHOEN" in the "SET GCELLHOBASIC" command is set to YES(Yes).  The source cell ID type in the incoming BSC handover request message is SAI. The values of "LTE SAI MCC", "LTE SAI MNC", "LTE SAI LAC", "LTE SAI SAC" for the source cell carried in the incoming BSC handover request message are consistent with those configured on the BSC.
- Radio impact: None

### 10. GCELLVAMOS / `VFRLOADREUSETHD` — Load Thld for Low Load VAMOS FR Demultiplexing

- Cells changed: **17,187** (69.26% of 24,816)
- Value changes: 85 → 86 (527); 86 → 87 (386); 86 → 85 (358); 87 → 86 (324); 80 → 81 (317); 84 → 85 (294); 81 → 82 (290); 85 → 84 (264)
- Default: 30 · Recommended: 30
- Meaning: Load threshold for triggering VAMOS FR channel demultiplexing due to low load in a common cell or in the overlaid or underlaid subcell of a concentric cell. VAMOS FR channel demultiplexing is triggered if the load in a common cell or in the overlaid or underlaid subcell of a concentric cell is less than the value of this parameter.
- Radio impact: The smaller the value of this parameter, the later the BSC makes a decision on VAMOS FR channel demultiplexing in a common cell or in the overlaid or underlaid subcell of a concentric cell. This helps alleviate cell congestion but decreases the MOS and increases the call drop rate more significantly.

### 11. GCELLVAMOS / `VAMOSLOADREUSELOADTHD` — Load Thres. of Channel Demultiplex

- Cells changed: **17,186** (69.25% of 24,816)
- Value changes: 85 → 86 (527); 86 → 87 (386); 86 → 85 (358); 87 → 86 (324); 80 → 81 (317); 84 → 85 (294); 81 → 82 (290); 85 → 84 (264)
- Default: 25 · Recommended: 25
- Meaning: Load threshold for triggering VAMOS HR channel demultiplexing in a common cell or in a concentric cell. VAMOS HR channel demultiplexing is triggered only when the load of a common cell or concentric cell is less than the value of this parameter.
- Radio impact: The smaller the value of this parameter, the later the VAMOS channel demultiplexing decision due to low cell load is made, the smaller the number of times for handovers due to low cell load, the heavier the VAMOS traffic in the cell, and the greater the network quality deterioration.

### 12. GCELLVAMOS / `VAMOSIUOINNERLOADTHD` — Load Thres. in Overlaid Subcell

- Cells changed: **11,009** (44.36% of 24,816)
- Value changes: 95 → 96 (907); 93 → 94 (772); 94 → 95 (673); 96 → 95 (575); 92 → 93 (556); 94 → 93 (519); 96 → 97 (445); 93 → 92 (438)
- Default: 75 · Recommended: 75
- Meaning: Load threshold for triggering VAMOS HR channel multiplexing in the overlaid subcell of a concentric cell. VAMOS HR channel multiplexing using an intra-cell handover is triggered only when the load of the overlaid subcell of a concentric cell is greater than or equal to the value of this parameter. VAMOS HR channel multiplexing using channel allocation is triggered only when the load of the overlaid subcell of a concentric cell is greater than or equal to the sum of this parameter and "VAMOSASSLOADOFT".
- Radio impact: The larger the value of this parameter, the smaller the number of new candidate VAMOS calls in the overlaid subcell. This affects VAMOS traffic volume and network quality.

### 13. GCELLVAMOS / `VAMOSMULTLOADTHD` — Channel Multiplex Load Thres.

- Cells changed: **11,009** (44.36% of 24,816)
- Value changes: 95 → 96 (907); 93 → 94 (772); 94 → 95 (673); 96 → 95 (575); 92 → 93 (556); 94 → 93 (519); 96 → 97 (445); 93 → 92 (438)
- Default: 75 · Recommended: 75
- Meaning: Load threshold for triggering VAMOS HR channel multiplexing in a common cell or in the underlaid subcell of a concentric cell. VAMOS HR channel multiplexing using an intra-cell handover is triggered only when the load in a common cell or in the underlaid subcell of a concentric cell is greater than or equal to the value of this parameter. VAMOS HR channel multiplexing using channel allocation is triggered only when the load in a common cell or in the underlaid subcell of a concentric cell is greater than or equal to the sum of this parameter and "VAMOSASSLOADOFT".
- Radio impact: The smaller the value of this parameter, the earlier the channel multiplexing decision is made, the higher the VAMOS traffic volume and the lower the network quality.

### 14. GCELLVAMOS / `VFRIUOINNERLOADTHD` — OL Load Threshold for VAMOS FR Multiplexing

- Cells changed: **11,009** (44.36% of 24,816)
- Value changes: 95 → 96 (907); 93 → 94 (772); 94 → 95 (673); 96 → 95 (575); 92 → 93 (556); 94 → 93 (519); 96 → 97 (445); 93 → 92 (438)
- Default: 50 · Recommended: 50
- Meaning: Load threshold for triggering VAMOS FR channel multiplexing in the overlaid subcell of a concentric cell. VAMOS FR channel multiplexing using an intra-cell handover is triggered only if the load in the overlaid subcell of a concentric cell is greater than or equal to the value of this parameter. VAMOS FR channel multiplexing using channel allocation is triggered only if the load in the overlaid subcell of a concentric cell is greater than or equal to the sum of this parameter and "VAMOSASSLOADOFT".
- Radio impact: The smaller the value of this parameter, the earlier the BSC makes a decision on VAMOS FR channel multiplexing in the overlaid subcell of a concentric cell and the heavier the VAMOS FR traffic in the overlaid subcell. Therefore, setting this parameter to a small value helps alleviate cell congestion. Compared with VAMOS HR, VAMOS FR has the same theoretical capacity and a higher MOS. This improves user experience. However, the HQI decreases and the call drop rate increases. Therefore, increas...

### 15. GCELLVAMOS / `VFRLOADTHD` — Load Threshold for VAMOS FR Multiplexing

- Cells changed: **11,009** (44.36% of 24,816)
- Value changes: 95 → 96 (907); 93 → 94 (772); 94 → 95 (673); 96 → 95 (575); 92 → 93 (556); 94 → 93 (519); 96 → 97 (445); 93 → 92 (438)
- Default: 50 · Recommended: 50
- Meaning: Load threshold for triggering VAMOS FR channel multiplexing in a common cell or in the underlaid subcell of a concentric cell. VAMOS FR channel multiplexing using an intra-cell handover is triggered only if the load in a common cell or in the underlaid subcell of a concentric cell is greater than or equal to the value of this parameter.  VAMOS FR channel multiplexing using channel allocation is triggered only if the load in a common cell or in the underlaid subcell of a concentric cell is greater than or equal to the sum of this parameter and "VAMOSASSLOADOFT".
- Radio impact: The smaller the value of this parameter, the earlier the BSC makes a decision on VAMOS FR channel multiplexing in a common cell or in the underlaid subcell of a concentric cell and the heavier the VAMOS FR traffic in the cell. Therefore, setting this parameter to a small value helps alleviate cell congestion. Compared with VAMOS HR, VAMOS FR has the same theoretical capacity and a higher MOS. This improves user experience. However, the high quality indicator (HQI) decreases and the call drop ...

## MO-level change volume

| MO | Description | Params changed | Total cell-param diffs |
|---|---|---:|---:|
| GCELLVAMOS | VAMOS Channel Multiplex Parameters of Cell | 69 | 99,312 |
| GCELLCCCH | Common Control Channel Parameters of Cell | 4 | 98,164 |
| GCELLHOBASIC | Basic Handover Parameters of Cell | 5 | 97,346 |
| GCELLTMR | Timer Parameters of Cell | 1 | 24,175 |
| GCELLBASICPARA | Basic Parameters of Cell | 5 | 1,921 |
| GCELL | GSM Cell at BSC | 4 | 1,325 |
| GCELLPRIEUTRANSYS | Cell Priority and EUTRAN System Information Parameters | 2 | 1,206 |
| GCELLSRVCC | Cell-level SRVCC parameters | 2 | 1,206 |
| GCELLCHMGAD | Advanced Channel Management Parameters of Cell | 4 | 548 |
| GCELLDYNTURNOFF | Parameters for Dynamically Turning off Cell | 10 | 80 |
| GCELLCHMGBASIC | Basic Channel Management Parameters of Cell | 1 | 75 |
| GCELLHOAD | Advanced Handover Parameters of Cell | 1 | 75 |
| GCELLOTHEXT | Extended Parameters of Cell | 1 | 33 |

## What did **not** change

No differences on common cells for handover control/emergency/fast HO (`GCELLHOCTRL`, `GCELLHOEMG`, `GCELLHOFAST`, `GCELLHOFITPEN`), power control (`GCELLPWRBASIC`, `GCELLPWR2`, `GCELLPWR3`), AMR, idle/reselect, GPRS, and most other MOs. That strongly suggests the CDR step is from the bulk campaigns above rather than from a general HO retune.

## Suggested verification order

1. Confirm who enabled **Intelligent Access Congestion Control** and why T3122 was moved off the recommended value 10, with Timer2=100 and threshold=5.
2. Confirm the **LTE SAI (470/02, LAC 15000, SAC 15)** against the live LTE SRVCC SAI. Mismatch → SRVCC drops.
3. Correlate TCH CDR by cell with **new VAMOS ON** (358 cells) and with cells whose VAMOS demux load threshold drifted.
4. Check HO fail after **NCC/BCC** changes (need neighbor BSIC alignment).
5. Review cells where **TCHBUSYTHRES / AMRTCHHPRIORLOAD** were cut toward 0 (forced HR).
