# omr.py
# Core OMR / CV helpers and grading.

import cv2, math, numpy as np
from config import WARP_W, WARP_H, PAD, ANSWER_ROIS, ROI_ID, DIGITS_TOP_TO_BOTTOM

# ---- Corner detection & warp ----
def find_markers(gray):
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    cnts,_ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h,w = gray.shape
    pts = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < (w*h)*0.0002 or area > (w*h)*0.02:
            continue
        x,y,bw,bh = cv2.boundingRect(c)
        asp = bw/float(bh)
        if 0.6 < asp < 1.4:
            peri = cv2.arcLength(c, True)
            if len(cv2.approxPolyDP(c, 0.05*peri, True)) == 4:
                M = cv2.moments(c)
                if M["m00"] != 0:
                    pts.append((int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])) )
    if len(pts) < 4:
        raise RuntimeError("4 corner squares not found")
    pts = np.array(pts, np.float32)
    s = pts.sum(1); d = np.diff(pts, axis=1).reshape(-1)
    TL = pts[np.argmin(s)]; BR = pts[np.argmax(s)]
    TR = pts[np.argmin(d)]; BL = pts[np.argmax(d)]
    return np.array([TL,TR,BR,BL], np.float32)


def warp_page(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = find_markers(g)
    dst = np.array([[PAD,PAD],[WARP_W-PAD,PAD],[WARP_W-PAD,WARP_H-PAD],[PAD,WARP_H-PAD]], np.float32)
    M = cv2.getPerspectiveTransform(m, dst)
    return cv2.warpPerspective(img, M, (WARP_W, WARP_H))


# ---- Bubble scoring helpers ----
def center_ring_score(gray, cx, cy, r_in, r1, r2):
    H,W = gray.shape
    mask_in = np.zeros((H,W), np.uint8)
    mask_ring = np.zeros((H,W), np.uint8)
    cv2.circle(mask_in, (cx,cy), int(r_in), 255, -1)
    cv2.circle(mask_ring, (cx,cy), int(r2), 255, -1)
    cv2.circle(mask_ring, (cx,cy), int(r1), 0, -1)
    mi = cv2.mean(gray, mask=mask_in)[0]
    mr = cv2.mean(gray, mask=mask_ring)[0]
    return max(0.0, (mr-mi)/max(1.0, mr))


def _grid_centers_and_scores(gray, box, rows, cols, cfg):
    H,W = gray.shape
    y1,y2,x1,x2 = box
    y1i,y2i = int(H*y1), int(H*y2)
    x1i,x2i = int(W*x1), int(W*x2)
    gh,gw = y2i-y1i, x2i-x1i
    if gh <= 0 or gw <= 0:
        return [], [], 0

    rt, rb = cfg["row_top_margin"], cfg["row_bottom_margin"]
    cl, cr = cfg["col_left_margin"], cfg["col_right_margin"]
    rshift, cshift = cfg["row_shift_px"], cfg["col_shift_px"]
    rscale = cfg["radius_scale"]

    usable_h = gh * (1.0 - rt - rb)
    usable_w = gw * (1.0 - cl - cr)
    rcent = rshift + (gh*rt) + np.linspace(0, usable_h, rows)
    ccent = cshift + (gw*cl) + np.linspace(0, usable_w, cols)

    base = max(4.0, min(
        (rcent[1]-rcent[0]) if rows>1 else 999,
        (ccent[1]-ccent[0]) if cols>1 else 999))
    r_in = base*0.60; r1 = base*0.72; r2 = base*0.98
    r_draw = int(base * float(rscale))

    centers=[]; scores=[]
    for cy in rcent:
        row_xy=[]; row_sc=[]
        for cx in ccent:
            cxp,cyp = int(x1i+cx), int(y1i+cy)
            row_xy.append((cxp,cyp))
            row_sc.append(center_ring_score(gray, cxp, cyp, r_in, r1, r2))
        centers.append(row_xy)
        scores.append(row_sc)
    return centers, scores, r_draw


def detect_answers(warped_gray, cfg):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    g = clahe.apply(warped_gray)

    answers=[]; centers=[]; r_draw=8
    abs_min, margin, z_min = cfg["abs_min"], cfg["margin"], cfg["z_min"]
    force_pick = bool(cfg.get("force_pick", False))

    for box in ANSWER_ROIS:
        c, s, r_draw = _grid_centers_and_scores(g, box, rows=10, cols=5, cfg=cfg)
        centers.extend(c)
        for row_scores in s:
            arr = np.array(row_scores, float)
            best = int(arr.argmax())
            second = float(np.partition(arr, -2)[-2]) if len(arr)>1 else 0.0
            mean, std = arr.mean(), arr.std()+1e-6
            z = (arr[best]-mean)/std
            good = (arr[best] >= abs_min) and (arr[best] >= second+margin) and (z >= z_min)
            answers.append(best if (good or force_pick) else -1)
    return answers, centers, r_draw


def detect_student_id(warped_gray, cfg):
    """Return (id_string, id_centers_per_col, r_draw). Always picks 5 digits."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    g = clahe.apply(warped_gray)

    centers, scores, r_draw = _grid_centers_and_scores(g, ROI_ID, rows=10, cols=5, cfg=cfg)
    if not centers:
        return "", [], r_draw

    rows=len(centers); cols=len(centers[0]) if rows else 0
    id_digits=[]; id_cols=[]
    for c in range(cols):
        col_scores = [scores[r][c] for r in range(rows)]
        col_centers = [centers[r][c] for r in range(rows)]
        best_row = int(np.argmax(col_scores))
        id_digits.append(DIGITS_TOP_TO_BOTTOM[best_row])
        id_cols.append((best_row, col_centers))
    return "".join(id_digits), id_cols, r_draw


def annotate(warped, centers, r, answers, key=None, mark_blanks=True, id_cols=None, r_id=None, limit_items=None):
    out = warped.copy()
    N = len(answers) if limit_items is None else max(0, int(limit_items))

    # Guides for all items (yellow)
    for row in centers:
        for (x,y) in row:
            cv2.circle(out, (x,y), r, (0,255,255), 1)

    # Correctness for first N
    for i,row in enumerate(centers):
        if i >= N:
            continue
        sel = answers[i] if i < len(answers) else -1
        k = key.get(i+1, None) if key else None

        if sel < 0:
            if mark_blanks and row:
                xavg = int(sum(p[0] for p in row)/len(row))
                yavg = int(sum(p[1] for p in row)/len(row))
                cv2.putText(out, "NO ANSWER", (xavg - 44, yavg + 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,255), 2, cv2.LINE_AA)
            if k is not None and 0 <= k < len(row):
                xg, yg = row[k]
                cv2.circle(out, (xg,yg), r, (0,255,0), 3)
            continue

        if k is None:
            x,y = row[sel]
            cv2.circle(out, (x,y), r, (0,255,0), 3)
        else:
            if sel == k:
                xg, yg = row[sel]
                cv2.circle(out, (xg,yg), r, (0,255,0), 3)
            else:
                xr, yr = row[sel]
                cv2.circle(out, (xr,yr), r, (0,0,255), 3)
                if 0 <= k < len(row):
                    xg, yg = row[k]
                    cv2.circle(out, (xg,yg), r, (0,255,0), 3)

    # Student ID (blue guides + pick)
    if id_cols:
        rr = r_id if r_id else r
        for best_row, col_centers in id_cols:
            for (x,y) in col_centers:
                cv2.circle(out,(x,y), rr, (255,0,0), 1)
            x,y = col_centers[best_row]
            cv2.circle(out,(x,y), rr, (255,0,0), 3)
    return out


def grade(answers, key, limit_items=None):
    correct = 0
    N = len(answers) if limit_items is None else max(0, int(limit_items))
    for i,a in enumerate(answers[:N], 1):
        k = key.get(i, None)
        if k is not None and a == k:
            correct += 1
    return correct
