# 🏛️ ShikshaSetu: SIH 2024 Live Demo Pitch Script
### Smart India Hackathon | Problem Statement 26101 (MoSPI / DIID)
**Title**: AI-Powered Personalized Capability & Competency Development Platform for Indian Official Statistical System  
**Team**: Kinetics  
**Demo Duration**: 7 Minutes  
**Deployed URL**: `https://shikshasetu-frontend.onrender.com` (or local mirror `http://localhost:5173`)

---

## 👥 Demo Personas & Credentials

| Role | Name | Email | Password | Primary Mission |
| :--- | :--- | :--- | :--- | :--- |
| **Official** | Rajesh Sharma (Statistical Officer) | `officer@shikshasetu.gov.in` | `Password@123` | Identify gaps, learn on iGOT/NSSTA, take adaptive assessments, ask Karmayogi Co-Pilot. |
| **Trainer** | Dr. Ananya Verma (NSSTA Lead Faculty) | `trainer@shikshasetu.gov.in` | `Password@123` | Ingest MoSPI training materials, generate AI MCQs, review/approve questions, publish quizzes. |
| **Admin** | System Administrator (Director, CBC/DoPT)| `admin@shikshasetu.gov.in` | `Password@123` | Monitor workforce capability health, critical skill deficits, and training ROI across departments. |

---

## ⏱️ Chronological 7-Minute Demo Flow

```text
  0:00 - 1:15  ───  ACT 1: THE NATIONAL GOVERNANCE PROBLEM & ADMIN DASHBOARD
  1:15 - 3:30  ───  ACT 2: TRAINER STUDIO (CURRICULUM INGESTION & AI MCQ STUDIO)
  3:30 - 6:00  ───  ACT 3: THE OFFICIAL LEARNER JOURNEY & DETERMINISTIC ADAPTIVE LOOP
  6:00 - 7:00  ───  ACT 4: KARMAYOGI AI CO-PILOT, MULTILINGUAL TOGGLE & Q&A
```

---

### 🎬 ACT 1: The National Governance Challenge (0:00 - 1:15)
* **Goal**: Establish the problem context — MoSPI statistical officers need continuous competency development aligned with Mission Karmayogi.
* **Action**:
  1. Login as **Admin** (`admin@shikshasetu.gov.in` / `Password@123`).
  2. Arrive at **Admin Dashboard** (`/admin/dashboard`).
  3. **Narrative to Judges**:
     > *"Respected Jury, India’s statistical system across MoSPI, state DES, and line ministries requires rigorous capacity building across 42 competencies. ShikshaSetu provides executive visibility into national workforce readiness. Notice the real-time average capability index (3.2/5.0), critical gap counters, and domain distribution across Statistical, Technical, Governance, and Behavioral disciplines."*
  4. Show **Workforce Overview** and **Skill Gap Analytics**.

---

### 🎬 ACT 2: Trainer Studio & AI-Powered Question Generation (1:15 - 3:30)
* **Goal**: Show how NSSTA faculty turn raw MoSPI curricula into validated assessments with Human-in-the-Loop AI.
* **Action**:
  1. Switch / Login as **Trainer** (`trainer@shikshasetu.gov.in` / `Password@123`).
  2. Navigate to **Training Materials** (`/trainer/materials`).
  3. Show uploaded document (e.g. `Sampling Theory & Survey Design 2024.pdf`).
  4. Click **Generate MCQs with AI**:
     - Select target competency: `STAT_SAMPLING` (Sampling & Estimation).
     - Target difficulty: `MEDIUM`.
     - Click **Generate Questions**.
  5. Jump to **Question Review Studio** (`/trainer/review-studio`):
     - **Narrative to Judges**:
       > *"Unlike unregulated AI that directly tests learners, ShikshaSetu enforces human faculty governance. The generated questions cite exact source chunks `[CHUNK-01]`. The trainer can review, edit options, adjust difficulty, or approve with one click."*
  6. Click **Approve** on questions, then navigate to **Quiz Studio** and show the published quiz.

---

### 🎬 ACT 3: Official Learner Journey & Deterministic Adaptive Loop (3:30 - 6:00)
* **Goal**: Demonstrate the core learner experience, evidence governance, and the adaptive test engine.
* **Action**:
  1. Login as **Official** (`officer@shikshasetu.gov.in` / `Password@123`).
  2. Arrive at **Official Dashboard** (`/dashboard`):
     - Show **My Skill Gaps**: `STAT_SAMPLING` requires Level 4.0, currently 0.0/None.
     - Show **Recommended Learning**: Point to matched **iGOT Karmayogi** module (*Survey Sampling & Estimation Methods*).
  3. Click **Start Learning**:
     - Complete module progress.
     - Open **Evidence Ledger**:
       - **Narrative to Judges**:
         > *"Notice our critical governance rule in action: Self-paced learning completion logs **Supporting Evidence (0.30 confidence)**. The competency rating remains unchanged because learning alone is not proof of mastery."*
  4. Navigate to **Assessments** (`/assessments`) -> Launch **Adaptive Capability Assessment**:
     - Show the **Real-Time Capability Meter** ($\theta \in [1.0, 5.0]$).
     - Answer Question 1 correctly -> Meter steps up to Medium/Hard.
     - Answer Question 2 -> Real-time difficulty calibration.
     - Click **Finalize Assessment**.
     - **Narrative to Judges**:
       > *"Finalizing the adaptive assessment logs **Authoritative Evidence (0.85 confidence)**. The competency profile updates instantly to 3.2, and the skill gap on the dashboard shrinks in real-time."*

---

### 🎬 ACT 4: Karmayogi AI Co-Pilot & Multilingual Hindi Toggle (6:00 - 7:00)
* **Goal**: Highlight personalized AI assistance and native Rajbhasha accessibility.
* **Action**:
  1. Open the floating **Karmayogi AI Co-Pilot** in the bottom-right corner.
  2. Click prompt chip: *"मेरी सबसे महत्वपूर्ण क्षमता कमियाँ क्या हैं?"* (What are my top skill gaps?).
  3. Show the assistant's structured response with unmutated source citations `[SRC-01]`, `[iGOT Course]`.
  4. In the top navigation bar, click the **Language Toggle** (`हिन्दी / English`):
     - Notice the entire UI seamlessly switches into authentic Rajbhasha Hindi vocabulary (*क्षमता डैशबोर्ड, कौशल अंतराल, अनुशंसित प्रशिक्षण, अनुकूली मूल्यांकन*).
  5. Conclude pitch:
     > *"ShikshaSetu delivers an end-to-end, governed, explainable capability platform empowering India's statistical infrastructure. Thank you!"*

---

## 🛡️ Backup & Offline Fail-Safe Checklist

If live internet or external AI API quotas fluctuate during the demonstration:
- ✅ **Deterministic Fallback Activated**: The AI Question Generator and Co-Pilot automatically synthesize contextual answers from local retrieved chunks if Gemini rate limits occur.
- ✅ **Local Mirror**: If cloud Wi-Fi disconnects, `http://localhost:5173` is running locally with MongoDB Atlas connection.
