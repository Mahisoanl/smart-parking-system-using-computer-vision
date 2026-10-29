# from fastapi import FastAPI, UploadFile, File, Request
# from fastapi.middleware.cors import CORSMiddleware
# import shutil
# import os
# import cv2
# import base64
# import numpy as np
# import time
# from collections import Counter
# from detections.licence_plate_detection import LicencePlateDetection
# from supabase import create_client, Client

# # ===============================
# # SUPABASE CONFIG
# # ===============================

# SUPABASE_URL = ""
# SUPABASE_KEY = ""  # ⚠ Use service role key in backend

# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# # ===============================
# # FASTAPI APP
# # ===============================

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # for development
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ===============================
# # LOAD MODEL
# # ===============================

# detector = LicencePlateDetection("models/best.pt")

# # ===============================
# # LIVE SESSION VARIABLES (Webcam)
# # ===============================

# detected_plates_live = []
# last_detection_time = 0
# SESSION_TIMEOUT = 3   # seconds without detection = vehicle left


# # ===============================
# # TEST DB ROUTE
# # ===============================

# @app.get("/test-db")
# def test_db():
#     response = supabase.table("parking_logs").select("*").limit(1).execute()
#     return response.data


# # ===============================
# # VIDEO UPLOAD DETECTION
# # ===============================

# @app.post("/detect")
# async def detect_plate(file: UploadFile = File(...)):

#     file_path = f"temp_{file.filename}"

#     # Save uploaded file
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     cap = cv2.VideoCapture(file_path)
#     detected_plates = []

#     # Read video frame by frame
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         _, texts = detector.detect_frame(frame)

#         for t in texts:
#             if t != "N/A":
#                 detected_plates.append(t)

#     cap.release()
#     os.remove(file_path)

#     # If nothing detected
#     if not detected_plates:
#         return {"message": "No plate detected"}

#     # Majority voting
#     final_plate = Counter(detected_plates).most_common(1)[0][0]

#     # Process booking logic
#     return process_booking(final_plate)


# # ===============================
# # WEBCAM FRAME DETECTION
# # ===============================

# @app.post("/detect-frame")
# async def detect_frame(request: Request):

#     global detected_plates_live, last_detection_time

#     data = await request.json()
#     image_data = data["image"].split(",")[1]

#     # Decode base64 image
#     image_bytes = base64.b64decode(image_data)
#     np_arr = np.frombuffer(image_bytes, np.uint8)
#     frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

#     _, texts = detector.detect_frame(frame)

#     current_time = time.time()

#     # If plate detected in this frame
#     for t in texts:
#         if t != "N/A":
#             detected_plates_live.append(t)
#             last_detection_time = current_time
#             return {"status": "scanning"}

#     # If no detection for some time → finalize session
#     if detected_plates_live and (current_time - last_detection_time > SESSION_TIMEOUT):

#         final_plate = Counter(detected_plates_live).most_common(1)[0][0]
#         detected_plates_live = []

#         return process_booking(final_plate)

#     return {"status": "waiting"}


# def process_booking(final_plate):

#     final_plate = final_plate.strip()

#     # 🔍 Check existing booking
#     booking = supabase.table("bookings") \
#         .select("*") \
#         .eq("vehicle_number", final_plate) \
#         .eq("status", "active") \
#         .execute()

#     print("Booking found:", booking.data)

#     # =========================
#     # CASE 1: BOOKING EXISTS
#     # =========================
#     if booking.data:

#         slot_id = booking.data[0]["slot_id"]

#     # =========================
#     # CASE 2: NO BOOKING → ASSIGN SLOT
#     # =========================
#     else:

#         # 🔍 Find FREE slot
#         free_slot = supabase.table("parking_slots") \
#             .select("*") \
#             .eq("status", "free") \
#             .limit(1) \
#             .execute()

#         if not free_slot.data:
#             return {
#                 "status": "full",
#                 "message": "No free slots available"
#             }

#         slot_id = free_slot.data[0]["id"]

#         # Create booking
#         supabase.table("bookings").insert({
#             "vehicle_number": final_plate,
#             "slot_id": slot_id,
#             "status": "active"
#         }).execute()

#     # =========================
#     # COMMON STEP (BOTH CASES)
#     # =========================

#     # Insert parking log
#     # Insert parking log with type
#     log_type = "booked" if booking.data else "guest"

#     supabase.table("parking_logs").insert({
#         "vehicle_number": final_plate,
#         "slot_id": slot_id,
#         "type": log_type
#     }).execute()

#     # Update slot → occupied
#     supabase.table("parking_slots") \
#         .update({"status": "occupied"}) \
#         .eq("id", slot_id) \
#         .execute()

#     # Update booking → entered
#     supabase.table("bookings") \
#         .update({"status": "entered"}) \
#         .eq("vehicle_number", final_plate) \
#         .eq("status", "active") \
#         .execute()

#     return {
#         "status": "allowed",
#         "plate": final_plate,
#         "slot": slot_id
#     }
# ttttttttttttttttttttttttttttttttttttttttttttttttttt
# ===============================
# COMMON BOOKING PROCESS FUNCTION
# ===============================

# def process_booking(final_plate):

#     booking = supabase.table("bookings") \
#         .select("*") \
#         .eq("vehicle_number", final_plate) \
#         .execute()

#     print("Booking found:", booking.data)

#     if booking.data:

#         slot_id = booking.data[0]["slot_id"]

#         # Insert parking log
#         supabase.table("parking_logs").insert({
#             "vehicle_number": final_plate,
#             "slot_id": slot_id
#         }).execute()

#         # Update parking slot to occupied
#         supabase.table("parking_slots") \
#             .update({"status": "occupied"}) \
#             .eq("id", slot_id) \
#             .execute()

#         # Update booking status to entered
#         supabase.table("bookings") \
#             .update({"status": "entered"}) \
#             .eq("vehicle_number", final_plate) \
#             .eq("status", "active") \
#             .execute()

#         return {
#             "status": "allowed",
#             "plate": final_plate,
#             "slot": slot_id
#         }

#     return {
#         "status": "denied",
#         "plate": final_plate
#     }
#tttttttttttttttttttttttttttttttttttttttttttttttttttttttttt

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import shutil
import os
import cv2
import base64
import numpy as np
import time
from collections import Counter
from detections.licence_plate_detection import LicencePlateDetection
from supabase import create_client, Client

# ===============================
# SUPABASE CONFIG
# ===============================

SUPABASE_URL = ""
SUPABASE_KEY = ""

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===============================
# FASTAPI APP
# ===============================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# LOAD MODEL
# ===============================

detector = LicencePlateDetection("models/best.pt")

# ===============================
# LIVE SESSION VARIABLES
# ===============================

detected_plates_live = []
last_detection_time = 0
SESSION_TIMEOUT = 3

# ===============================
# EXIT MODEL
# ===============================

class ExitRequest(BaseModel):
    plate_number: str

# ===============================
# TEST ROUTE
# ===============================

@app.get("/test-db")
def test_db():
    return supabase.table("parking_logs").select("*").limit(1).execute().data

# ===============================
# VIDEO DETECTION (AUTO ENTRY + EXIT)
# ===============================

@app.post("/detect")
async def detect_plate(file: UploadFile = File(...)):

    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cap = cv2.VideoCapture(file_path)
    detected_plates = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        _, texts = detector.detect_frame(frame)

        for t in texts:
            if t != "N/A":
                detected_plates.append(t)

    cap.release()
    os.remove(file_path)

    if not detected_plates:
        return {"message": "No plate detected"}

    final_plate = Counter(detected_plates).most_common(1)[0][0]
    final_plate = final_plate.strip().upper()

    # 🔍 Check active log
    active_log = supabase.table("parking_logs") \
        .select("*") \
        .eq("vehicle_number", final_plate) \
        .is_("exit_time", None) \
        .execute()

    if active_log.data:
        return vehicle_exit(ExitRequest(plate_number=final_plate))
    else:
        return process_booking(final_plate)

# ===============================
# WEBCAM DETECTION (AUTO ENTRY + EXIT)
# ===============================

@app.post("/detect-frame")
async def detect_frame(request: Request):

    global detected_plates_live, last_detection_time

    data = await request.json()
    image_data = data["image"].split(",")[1]

    image_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    _, texts = detector.detect_frame(frame)

    current_time = time.time()

    for t in texts:
        if t != "N/A":
            detected_plates_live.append(t)
            last_detection_time = current_time
            return {"status": "scanning"}

    if detected_plates_live and (current_time - last_detection_time > SESSION_TIMEOUT):

        final_plate = Counter(detected_plates_live).most_common(1)[0][0]
        detected_plates_live = []

        final_plate = final_plate.strip().upper()

        # 🔍 Check active log
        active_log = supabase.table("parking_logs") \
            .select("*") \
            .eq("vehicle_number", final_plate) \
            .is_("exit_time", None) \
            .execute()

        if active_log.data:
            return vehicle_exit(ExitRequest(plate_number=final_plate))
        else:
            return process_booking(final_plate)

    return {"status": "waiting"}

# ===============================
# ENTRY LOGIC (UNCHANGED)
# ===============================

def process_booking(final_plate):

    final_plate = final_plate.strip().upper()

    booking = supabase.table("bookings") \
        .select("*") \
        .eq("vehicle_number", final_plate) \
        .eq("status", "active") \
        .execute()

    if booking.data:
        slot_id = booking.data[0]["slot_id"]
    else:
        free_slot = supabase.table("parking_slots") \
            .select("*") \
            .eq("status", "free") \
            .limit(1) \
            .execute()

        if not free_slot.data:
            return {"status": "full"}

        slot_id = free_slot.data[0]["id"]

        supabase.table("bookings").insert({
            "vehicle_number": final_plate,
            "slot_id": slot_id,
            "status": "active"
        }).execute()

    log_type = "booked" if booking.data else "guest"

    supabase.table("parking_logs").insert({
        "vehicle_number": final_plate,
        "slot_id": slot_id,
        "type": log_type
    }).execute()

    supabase.table("parking_slots") \
        .update({"status": "occupied"}) \
        .eq("id", slot_id) \
        .execute()

    supabase.table("bookings") \
        .update({"status": "entered"}) \
        .eq("vehicle_number", final_plate) \
        .eq("status", "active") \
        .execute()

    return {
        "status": "entry",
        "plate": final_plate,
        "slot": slot_id
    }

# ===============================
# EXIT LOGIC
# ===============================

@app.post("/exit")
def vehicle_exit(data: ExitRequest):

    plate = data.plate_number.strip().upper()

    log = supabase.table("parking_logs") \
        .select("*") \
        .eq("vehicle_number", plate) \
        .is_("exit_time", None) \
        .order("entry_time", desc=True) \
        .limit(1) \
        .execute()

    if not log.data:
        return {"status": "not_found"}

    log_data = log.data[0]
    slot_id = log_data["slot_id"]

    supabase.table("parking_logs").update({
        "exit_time": datetime.now().isoformat()
    }).eq("id", log_data["id"]).execute()

    supabase.table("parking_slots").update({
        "status": "free"
    }).eq("id", slot_id).execute()

    return {
        "status": "exit",
        "plate": plate,
        "slot_freed": slot_id
    }