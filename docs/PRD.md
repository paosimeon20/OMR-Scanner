# 📕 Product Requirements Document (PRD)

**Product:** Optical Mark Recognition (OMR) Scanner  
**Version:** 1.1  
**Date:** September 17, 2025  
**Author:** Paolo Simeon Satuito  

---

## 1. Executive Summary

### Problem Statement
Teachers spend significant time manually grading multiple-choice exams, leading to inefficiency, human error, and delayed feedback.

### Solution Overview
Develop a desktop OMR scanner that runs on Windows 10/11 mini PCs with a USB webcam. The system provides instant grading, annotated feedback, student score reports, and class-level statistics, all through an intuitive and touch-friendly UI.

### Business Impact
- Reduces grading time by up to 80%  
- Improves grading accuracy and fairness  
- Enables data-driven decision-making for administrators  
- Provides a scalable, low-cost alternative to OMR machines  

### Key Metrics
- ≥95% recognition accuracy  
- ≤5 seconds average processing time per sheet  
- ≥90% teacher adoption within pilot schools  
- ≥80% user satisfaction rating  

### Timeline
- **MVP:** Camera scanning, answer key import, class section import, auto-grading, export results (3 months)  
- **V1:** Statistics dashboard, item analysis, error handling, session management (6 months)  
- **V2:** Multi-exam management, advanced analytics (12 months)  

---

## 2. Market Context & Opportunity

### Market Size
- **TAM:** ~$2B global EdTech grading automation market  
- **SAM:** ~$200M for low-cost grading tools in Southeast Asia  
- **SOM:** ~$10M starting with schools in the Philippines  

### Competitive Landscape
- **ZipGrade, ExamSoft, Akindi:** Cloud-based, subscription-based  
- **Traditional OMR machines:** Expensive hardware-dependent  
- **Differentiation:** Offline, one-time setup, runs on standard Windows PCs  

### User Research Insights
- Teachers want simplicity and touch-friendly UI.  
- Administrators need exportable reports and analytics.  
- Students expect fairness and fast results.  

### Business Case
Low-cost grading automation improves productivity, reduces errors, and enables schools to modernize assessments without heavy investment.

---

## 3. User Personas & Journey

### Primary Users
- **Teacher Persona:** Grades 3–5 exam batches per week; pain point = manual checking.  
- **Administrator Persona:** Needs performance insights across sections.  

### Secondary Users
- **Students:** Indirect beneficiaries.  
- **IT Support:** Ensures setup and troubleshooting.  

### User Journey
- **Current:** Teachers manually check papers → errors/delays.  
- **Future:** Teachers scan sheets → instant grading + reports → admin reviews analytics.  

### Use Cases
- Scan one batch of 200 papers in a session  
- Flag duplicate student IDs  
- Export scores to Excel  
- Generate item analysis for review  

---

## 4. Product Goals & Success Metrics

### Objectives
- Automate exam grading  
- Improve grading accuracy  
- Provide actionable insights  

### Key Results
- **KR1:** ≥95% accuracy within MVP  
- **KR2:** Reduce grading time by 80%  
- **KR3:** ≥80% teacher satisfaction  

### Success Criteria
- Accurate, reliable scanning validated in multiple schools  
- Reports adopted in decision-making  
- Smooth onboarding  

### Risk Metrics
- <90% recognition accuracy → usability risk  
- 10% duplicate errors → trust erosion  

---

## 5. Feature Requirements

### Core Features (MVP)
- Load Answer Key (.txt)  
- Load Class Section (.txt with names + IDs)  
- Webcam scanning  
- Auto-grading & annotation  
- Export results (CSV/XLSX)  

### Nice-to-Have Features (Future)
- Item analysis (% correct per question)  
- Score trend charts  
- Multi-exam management  
- Cloud sync  

### Out of Scope
- Raspberry Pi  
- Mobile-native apps  
- LMS integration  

### Feature Prioritization (MoSCoW)
- **Must-Have:** Scanning, grading, exports  
- **Should-Have:** Statistics dashboard  
- **Could-Have:** Cloud sync, multi-exam history  
- **Won’t-Have:** LMS integration  

---

## 6. User Experience Requirements

- **Flows:** Load → Scan → Review → Export  
- **IA:** Tabs for *Scan | Scores | Statistics*  
- **Accessibility:** WCAG AA contrast, large dropdowns  
- **Performance:** ≤5s per sheet, smooth scrolling for statistics  

---

## 7. Technical Considerations

- **Platform:** Windows 10/11 mini PCs  
- **Integration:** TXT/CSV/XLSX import/export  
- **Scalability:** Up to 200 students per batch  
- **Security:** Offline-first, logs for audit  

---

## 8. Go-to-Market Strategy

- **Launch Plan:** Pilot in 2–3 local schools → refine → expand  
- **Positioning:** “Affordable, accurate grading automation for schools”  
- **Training & Support:** User guide + video tutorials  
- **Feedback:** In-app error logs, surveys  

---

## 9. Timeline & Milestones

| Phase | Milestones                            | Duration   |
|-------|---------------------------------------|------------|
| MVP   | Scanning, grading, exports            | 3 months   |
| V1    | Statistics dashboard, error handling  | +3 months  |
| V2    | Multi-exam management, analytics      | +6 months  |

### Dependencies
- Availability of webcams  
- Teacher willingness for pilot testing  

### Resources
- 1 Software Engineer (Python/UI)  
- 1 QA Engineer  
- 1 Product Manager  

---

## 10. Risk Assessment

### Technical Risks
- **Misaligned sheets** → Mitigation: corner detection, tolerance  
- **Webcam quality** → Mitigation: require minimum resolution  

### Market Risks
- **Teacher adoption** → Mitigation: simple UI, training  
- **Competitor apps** → Mitigation: emphasize offline/local  

### Resource Risks
- **Limited budget** → Mitigation: staged rollout  
- **Tight school schedules** → Mitigation: phased pilots  
